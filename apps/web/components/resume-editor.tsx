'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useDeferredValue, useEffect, useState } from 'react';
import { api, errorMessage, json, request } from '../lib/api';
import { useResume } from '../lib/use-resume';
import { fieldDefinitions, sectionLabels, type Generation, type ResumeDocument, type Section, type SectionType, type Template } from '../lib/types';
import { Protected } from './session';
import { ResumePreview } from './resume-preview';
import { AiPanel } from './ai-panel';
import { ConfirmDialog } from './confirm-dialog';

interface Version { id: string; revision: number; createdAt: string }
type AiOpenState = { scenario: 'generate-section' | 'polish'; sectionType?: SectionType };

export function ResumeEditor({ id }: { id: string }) {
  return <Protected><EditorContent id={id} /></Protected>;
}

function EditorContent({ id }: { id: string }) {
  const router = useRouter();
  const model = useResume(id);
  const { resume, latest, loading, saving, error, setError, conflict, dirty, change, flush, load, replace } = model;
  const [style, setStyle] = useState('professional');
  const [mobileTab, setMobileTab] = useState<'edit' | 'preview'>('edit');
  const [openSections, setOpenSections] = useState<string[]>([]);
  const [ai, setAi] = useState(false);
  const [aiTarget, setAiTarget] = useState<AiOpenState>({ scenario: 'generate-section' });
  const [versions, setVersions] = useState<Version[] | null>(null);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [restore, setRestore] = useState<Version | null>(null);
  const [reload, setReload] = useState(false);
  const preview = useDeferredValue(resume);

  // The selected template controls the same visual style used by the live
  // preview and the server-side PDF renderer. Users can still switch the PDF
  // style manually after the template is applied.
  useEffect(() => {
    if (!resume?.templateId) return;
    let active = true;
    void api<{ template: Template }>(`/templates/${encodeURIComponent(resume.templateId)}`)
      .then(({ template }) => {
        if (!active) return;
        const nextStyle = template.style === 'minimal' || template.style === 'clean' ? 'clean'
          : template.style === 'compact' ? 'compact' : 'professional';
        setStyle(nextStyle);
      })
      .catch(() => {
        // A template can be taken down after a resume was saved. Keep the
        // existing style in that case so the editor remains usable.
      });
    return () => { active = false; };
  }, [resume?.templateId]);

  useEffect(() => {
    if (resume?.id !== id) return;
    setOpenSections((current) => current.length ? current : resume.sections.map((section) => section.type));
  }, [id, resume?.id]);

  const closeAi = useCallback(() => setAi(false), []);

  function updateSection(sectionId: string, transform: (section: Section) => Section) {
    change((current) => ({
      ...current,
      sections: current.sections.map((section) => section.id === sectionId ? transform(section) : section),
    }));
  }

  function toggleSection(type: string) {
    setOpenSections((current) => current.includes(type) ? current.filter((item) => item !== type) : [...current, type]);
  }

  function move(sectionId: string, direction: number) {
    change((current) => {
      const sections = [...current.sections].sort((a, b) => a.order - b.order);
      const index = sections.findIndex((section) => section.id === sectionId);
      const target = index + direction;
      if (target < 0 || target >= sections.length) return current;
      [sections[index], sections[target]] = [sections[target], sections[index]];
      return { ...current, sections: sections.map((section, nextIndex) => ({ ...section, order: nextIndex })) };
    });
  }

  function openAiFor(sectionType?: SectionType, scenario: AiOpenState['scenario'] = 'generate-section') {
    setAiTarget({ sectionType, scenario });
    setAi(true);
  }

  async function download() {
    setBusy('pdf'); setMessage(''); setError('');
    try {
      if (!await flush()) return;
      const response = await request(`/resumes/${id}/pdf`, json('POST', { style }));
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      const disposition = response.headers.get('content-disposition');
      const encoded = disposition?.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
      anchor.download = encoded ? decodeURIComponent(encoded) : `${latest.current?.title || '简历'}.pdf`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
      setMessage('PDF 已生成，下载已开始。');
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(''); }
  }

  async function showVersions() {
    setBusy('versions'); setError('');
    try {
      if (!await flush()) return;
      setVersions((await api<{ versions: Version[] }>(`/resumes/${id}/versions`)).versions);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(''); }
  }

  async function snapshot() {
    setBusy('snapshot'); setError('');
    try {
      if (!await flush()) return;
      await api(`/resumes/${id}/versions`, json('POST'));
      setMessage('版本快照已保存。');
      if (versions) await showVersions();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(''); }
  }

  function accept(generation: Generation) {
    const polish = generation.scenario === 'polish';
    change((current) => ({
      ...current,
      sections: current.sections.map((section) => section.type === generation.result.sectionType
        ? {
          ...section,
          visible: true,
          // A polish result is allowed to improve wording, but it must not
          // erase facts the model omitted. Merge non-empty fields by index and
          // keep entries that were not returned by the model.
          content: polish && section.content.length
            ? section.content.map((entry, index) => ({
              ...entry,
              ...Object.fromEntries(Object.entries(generation.result.items[index] || {}).filter(([, value]) => value.trim())),
            }))
            : generation.result.items,
        }
        : section),
    }));
    setOpenSections((current) => current.includes(generation.result.sectionType) ? current : [...current, generation.result.sectionType]);
    setMessage('已采纳 AI 内容。请核对事实，必要时继续编辑。');
  }

  if (loading) return <div className="page-state" role="status"><span className="spinner" />正在打开简历…</div>;
  if (!resume) return <div className="page-state"><h1>无法打开简历</h1><p role="alert">{error || '简历不存在或你无权访问。'}</p><button className="button" onClick={() => void load()}>重新加载</button><button className="text-button" onClick={() => router.push('/resumes')}>返回我的简历</button></div>;

  const orderedSections = [...resume.sections].sort((a, b) => a.order - b.order);

  return <div className="editor-page">
    <div className="editor-toolbar">
      <div className="editor-title">
        <button className="text-button editor-back" onClick={async () => { if (await flush()) router.push('/resumes'); }}>‹ 我的简历</button>
        <div className="editor-title-row"><label><span className="sr-only">简历名称</span><input aria-label="简历名称" value={resume.title} maxLength={100} onChange={(event) => change((current) => ({ ...current, title: event.target.value }))} /></label><span className="editor-mode-label">编辑工作台</span></div>
        <span className="save-status" role="status">{conflict ? '版本冲突，当前编辑已保留在页面' : saving ? '正在保存…' : dirty ? '有待保存的修改' : '✓ 所有修改已保存'}　<span className="muted">版本 {resume.revision}</span></span>
      </div>
      <div className="editor-actions">
        <Link className="button secondary small" href={`/templates?resumeId=${encodeURIComponent(id)}`}>选择模板</Link>
        <button className="button secondary small" onClick={() => void snapshot()} disabled={!!busy || conflict}>保存快照</button>
        <button className="button secondary small" onClick={() => void showVersions()} disabled={!!busy}>历史版本</button>
        <button className="button teal small" onClick={() => openAiFor(undefined, 'generate-section')}>AI 助手</button>
        <button className="button small" onClick={() => void download()} disabled={!!busy || conflict}>{busy === 'pdf' ? <><span className="spinner" />生成 PDF…</> : '下载 PDF'}</button>
      </div>
    </div>

    {error ? <div className="notice error" role="alert">{error}{conflict ? <><p>当前页面的修改仍然保留。请先下载草稿备份，再重新载入最新版本。</p><div className="button-row"><button className="button small secondary" onClick={() => { const url = URL.createObjectURL(new Blob([JSON.stringify(latest.current, null, 2)], { type: 'application/json' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = '简历冲突草稿.json'; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }}>下载当前草稿</button><button className="button small secondary" onClick={() => setReload(true)}>重新载入</button></div></> : <button className="text-button" style={{ marginLeft: 12 }} onClick={() => void flush()}>重试保存</button>}</div> : null}
    {message ? <div className="notice success" role="status">{message}</div> : null}

    <div className="editor-guide"><span className="guide-check">✓</span><strong>先填写真实经历</strong><span>再用 AI 润色表达</span><span>最后选择模板并导出 PDF</span></div>
    <div className="mobile-editor-tabs" role="tablist" aria-label="编辑视图"><button role="tab" aria-selected={mobileTab === 'edit'} className={mobileTab === 'edit' ? 'active' : ''} onClick={() => setMobileTab('edit')}>编辑内容</button><button role="tab" aria-selected={mobileTab === 'preview'} className={mobileTab === 'preview' ? 'active' : ''} onClick={() => setMobileTab('preview')}>实时预览</button></div>

    <div className="editor-grid">
      <div className={`editor-form ${mobileTab !== 'edit' ? 'mobile-hidden' : ''}`}>
        <div className="module-nav"><div><strong>简历内容</strong><span className="module-count">{orderedSections.filter((section) => section.visible).length} 个模块显示中</span></div><button className="text-button" onClick={() => setOpenSections((current) => current.length === orderedSections.length ? [] : orderedSections.map((section) => section.type))}>{openSections.length === orderedSections.length ? '全部收起' : '展开全部'}</button></div>
        <div className="editor-hint">每个模块都可以直接编辑。填写完成后，点击模块右侧的 <strong>AI 润色</strong> 只优化表达，不改变你的事实。</div>
        {orderedSections.map((section, index) => {
          const expanded = openSections.includes(section.type);
          const entries = section.content.filter((item) => Object.values(item).some(Boolean)).length;
          return <div className={`section-editor ${expanded ? 'is-open' : ''}`} key={section.id}>
            <div className="section-heading">
              <label className="visibility-toggle" title={section.visible ? '隐藏模块' : '显示模块'}><span className="sr-only">显示{section.title}</span><input type="checkbox" checked={section.visible} onChange={(event) => updateSection(section.id, (current) => ({ ...current, visible: event.target.checked }))} /><span className="visibility-mark" /></label>
              <button className="section-toggle" aria-expanded={expanded} aria-controls={`section-${section.id}`} onClick={() => toggleSection(section.type)}><span className="section-chevron" aria-hidden="true">{expanded ? '−' : '+'}</span><span>{section.title}</span><span className="section-meta">{!section.visible ? '已隐藏' : entries ? `${entries} 条内容` : '待填写'}</span></button>
              <button className="section-ai" onClick={() => openAiFor(section.type, 'polish')} disabled={!section.visible} title={`润色${section.title}`}><span aria-hidden="true">✦</span> AI 润色</button>
              <button className="icon-button section-move" aria-label={`上移${section.title}`} disabled={index === 0} onClick={() => move(section.id, -1)}>↑</button><button className="icon-button section-move" aria-label={`下移${section.title}`} disabled={index === orderedSections.length - 1} onClick={() => move(section.id, 1)}>↓</button>
            </div>
            {expanded ? <div className="section-body" id={`section-${section.id}`}>
              {section.type === 'basic' ? <p className="section-lead">先填写联系方式，让招聘者能快速找到你。</p> : section.type === 'intent' ? <p className="section-lead">明确你想去哪里、做什么工作。</p> : section.type === 'summary' ? <p className="section-lead">用 2–3 句话概括你的优势和工作方式。</p> : <p className="section-lead">写清楚你做了什么、怎么做的，以及带来了什么结果。</p>}
              {section.content.map((item, itemIndex) => <div className="section-entry" key={itemIndex}>{!['basic', 'intent', 'summary'].includes(section.type) ? <div className="entry-actions"><span>第 {itemIndex + 1} 条经历</span><button className="text-button danger" onClick={() => updateSection(section.id, (current) => ({ ...current, content: current.content.filter((_, indexToRemove) => indexToRemove !== itemIndex) }))}>移除此条</button></div> : null}<div className="field-grid">{fieldDefinitions[section.type].map(([key, label, multiline]) => <label className={`field ${multiline ? 'wide' : ''}`} key={key}>{label}{multiline ? <textarea value={item[key] || ''} maxLength={6000} onChange={(event) => updateSection(section.id, (current) => ({ ...current, content: current.content.map((entry, entryIndex) => entryIndex === itemIndex ? { ...entry, [key]: event.target.value } : entry) }))} placeholder={`写下你的${label}`} /> : <input value={item[key] || ''} maxLength={6000} onChange={(event) => updateSection(section.id, (current) => ({ ...current, content: current.content.map((entry, entryIndex) => entryIndex === itemIndex ? { ...entry, [key]: event.target.value } : entry) }))} placeholder={`填写${label}`} />}</label>)}</div></div>)}
              {!['basic', 'intent', 'summary'].includes(section.type) ? <button className="button secondary small add-entry" disabled={section.content.length >= 30} onClick={() => updateSection(section.id, (current) => ({ ...current, content: [...current.content, Object.fromEntries(fieldDefinitions[section.type].map(([key]) => [key, '']))] }))}>＋ 添加{section.title}</button> : null}
            </div> : null}
          </div>;
        })}
      </div>

      <div className={`preview-workspace ${mobileTab !== 'preview' ? 'mobile-hidden' : ''}`}><div className="preview-tools"><div><span className="preview-live-dot" />A4 实时预览</div><label>PDF 样式 <select aria-label="PDF 样式" value={style} onChange={(event) => setStyle(event.target.value)}><option value="professional">专业蓝</option><option value="clean">简约文书</option><option value="compact">紧凑清晰</option></select></label></div>{preview ? <ResumePreview resume={preview} style={style} /> : null}</div>
    </div>

    {ai ? <AiPanel resume={resume} onClose={closeAi} beforeGenerate={flush} onAccept={accept} initialScenario={aiTarget.scenario} initialSectionType={aiTarget.sectionType || 'work'} /> : null}
    {versions ? <><button className="panel-overlay" onClick={() => setVersions(null)} aria-label="关闭历史版本" /><aside className="side-panel" role="dialog" aria-modal="true" aria-labelledby="versions-title"><div className="panel-heading"><h2 id="versions-title">历史版本</h2><button className="icon-button" onClick={() => setVersions(null)} aria-label="关闭历史版本">×</button></div><p className="muted small-text">每次保存和手动快照都可保留版本，最多保留最近 50 份。</p><button className="button secondary small" onClick={() => void snapshot()} disabled={!!busy}>保存当前快照</button>{versions.length ? versions.map((version) => <div className="version-row" key={version.id}><div><strong>版本 {version.revision}</strong><br /><span className="muted small-text">{new Date(version.createdAt).toLocaleString('zh-CN')}</span></div><button className="text-button" onClick={() => setRestore(version)} disabled={version.revision === resume.revision}>恢复此版本</button></div>) : <p className="notice">还没有历史版本。点击“保存当前快照”保留这一刻。</p>}</aside></> : null}
    {restore ? <ConfirmDialog title={`恢复到版本 ${restore.revision}？`} description="当前内容将被所选历史版本替换。恢复前会保存当前修改，恢复操作会创建新版本。" action="确认恢复" busy={busy === 'restore'} onCancel={() => setRestore(null)} onConfirm={async () => { setBusy('restore'); try { if (!await flush()) return; const { resume: restored } = await api<{ resume: ResumeDocument }>(`/resumes/${id}/versions/${restore.id}/restore`, json('POST', { revision: latest.current!.revision })); replace(restored); setRestore(null); setVersions(null); setMessage('已恢复历史内容，并创建新版本。'); } catch (e) { setError(errorMessage(e)); } finally { setBusy(''); } }} /> : null}
    {reload ? <ConfirmDialog title="重新载入最新版本？" description="当前页面尚未保存的修改会丢失。请确认已经下载草稿备份。" action="重新载入" danger onCancel={() => setReload(false)} onConfirm={() => { setReload(false); void load(); }} /> : null}
  </div>;
}
