'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, errorMessage, json } from '../lib/api';
import { sectionLabels, type ResumeDocument, type Template } from '../lib/types';
import { useSession } from './session';
import { MiniPaper } from './resume-preview';

const styleName: Record<string, string> = { professional: '专业', minimal: '简约', clean: '简约', compact: '紧凑', creative: '创意' };
const categories = [
  { key: 'all', label: '精品推荐' },
  { key: 'professional', label: '专业商务', style: 'professional' },
  { key: 'minimal', label: '简约清爽', style: 'minimal' },
  { key: 'compact', label: '技术紧凑', style: 'compact' },
  { key: '应届生', label: '应届/校招', tag: '应届生' },
  { key: '产品', label: '产品/运营', tag: '产品' },
  { key: '技术', label: '互联网/IT', tag: '技术' },
];

const safeUrl = (value?: string | null) => {
  try {
    const url = new URL(value || '');
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
  } catch { return null; }
};

export function TemplateVisual({ template }: { template: Template }) {
  const image = safeUrl(template.thumbnailUrl);
  return <div className={`template-visual ${template.style}`}>
    {image ? <img className="template-thumbnail" src={image} alt={`${template.title}预览`} loading="lazy" /> : <MiniPaper title="你的职业故事" sections={(template.sectionOrder || ['work', 'projects', 'education']).filter((type) => !['basic', 'intent'].includes(type)).slice(0, 4).map((type) => sectionLabels[type])} />}
  </div>;
}

export function TemplateLibrary() {
  const searchParams = useSearchParams();
  const resumeId = searchParams.get('resumeId');
  const [allTemplates, setAllTemplates] = useState<Template[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [keyword, setKeyword] = useState('');
  const [role, setRole] = useState('');
  const [industry, setIndustry] = useState('');
  const [experience, setExperience] = useState('');
  const [recommended, setRecommended] = useState(false);
  const [fallback, setFallback] = useState(false);
  const [showRecommend, setShowRecommend] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const next = (await api<{ templates: Template[] }>('/templates')).templates;
      setAllTemplates(next); setTemplates(next); setRecommended(false); setFallback(false);
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const displayed = useMemo(() => {
    const query = keyword.trim().toLowerCase();
    if (recommended) return templates;
    return templates.filter((template) => {
      const match = !query || [template.title, template.description, template.industry, ...template.tags].filter(Boolean).join(' ').toLowerCase().includes(query);
      return match;
    });
  }, [keyword, recommended, templates]);

  function changeCategory(category: typeof categories[number]) {
    setActiveCategory(category.key); setRecommended(false); setKeyword('');
    if (category.key === 'all') { setTemplates(allTemplates); return; }
    setTemplates(allTemplates.filter((template) => (category.style ? template.style === category.style : template.tags.includes(category.tag || category.key))));
  }

  async function recommend() {
    setLoading(true); setError(''); setRecommended(true);
    const query = new URLSearchParams();
    if (role) query.set('role', role); if (industry) query.set('industry', industry); if (experience) query.set('experience', experience);
    try {
      const response = await api<{ templates: Template[]; fallback?: boolean }>(`/templates/recommendations?${query}`);
      setTemplates(response.templates); setFallback(!!response.fallback); setActiveCategory('all');
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }

  return <div className="template-catalog-page">
    <div className="template-catalog-topbar"><div className="template-catalog-title"><span className="catalog-mark">▣</span><div><h1>简历模板</h1><p>挑选一个结构，把你的经历放进更清楚的版式。</p></div></div><label className="template-search"><span aria-hidden="true">⌕</span><input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索模板、岗位或风格" /><span className="search-hint">输入关键词</span></label><Link href={resumeId ? `/resumes/${resumeId}` : '/resumes'} className="button small">{resumeId ? '返回编辑' : '我的简历'}</Link></div>
    <div className="template-catalog-layout">
      <aside className="template-sidebar" aria-label="模板分类"><div className="sidebar-label">模板分类</div>{categories.map((category) => <button key={category.key} className={activeCategory === category.key ? 'active' : ''} onClick={() => changeCategory(category)}><span className="category-dot" />{category.label}{category.key === 'all' ? <span className="category-count">{allTemplates.length}</span> : null}</button>)}<div className="sidebar-divider" /><div className="sidebar-label">快速入口</div><button onClick={() => setShowRecommend((current) => !current)} className={showRecommend ? 'active' : ''}><span className="category-spark">✦</span>按岗位推荐</button><Link href="/resumes">我的简历</Link><div className="sidebar-note">模板只提供模块顺序、布局和风格参考。内容由你自己填写并确认。</div></aside>
      <main className="template-catalog-main">
        <div className="template-catalog-heading"><div><p className="panel-kicker">从结构开始</p><h2>{recommended ? '为你推荐的结构' : categories.find((category) => category.key === activeCategory)?.label || '精品推荐'}</h2></div><div className="catalog-tools"><label>排序<select defaultValue="latest"><option value="latest">最近收录</option><option value="popular">推荐优先</option></select></label></div></div>
        {showRecommend ? <form className="recommend-strip" onSubmit={(event) => { event.preventDefault(); void recommend(); }}><div className="recommend-copy"><span className="recommend-icon">✦</span><div><strong>告诉我你的求职方向</strong><small>根据岗位、行业和经历匹配结构，不需要 AI 也能工作。</small></div></div><div className="recommend-fields"><input value={role} maxLength={120} onChange={(event) => setRole(event.target.value)} placeholder="目标岗位，如：产品经理" /><input value={industry} maxLength={80} onChange={(event) => setIndustry(event.target.value)} placeholder="目标行业，如：互联网" /><input value={experience} maxLength={2000} onChange={(event) => setExperience(event.target.value)} placeholder="经历关键词，如：项目管理 用户研究" /><button className="button small" disabled={loading}>开始推荐</button></div></form> : null}
        {error ? <p className="notice error" role="alert">{error} <button className="text-button" onClick={() => void load()}>重新加载</button></p> : null}
        {recommended ? <p className="notice">{fallback ? '没有找到明显匹配的标签，先展示通用结构。' : '已按岗位、行业和经历关键词排序。'}</p> : null}
        {loading ? <div className="page-state" role="status"><span className="spinner" />正在整理模板…</div> : displayed.length ? <div className="template-wps-grid">{displayed.map((template, index) => <article className="template-wps-card" key={template.id}><Link tabIndex={-1} aria-hidden="true" href={`/templates/${template.id}${resumeId ? `?resumeId=${encodeURIComponent(resumeId)}` : ''}`}><div className="template-card-index">{String(index + 1).padStart(2, '0')}</div><TemplateVisual template={template} /></Link><div className="template-card-body"><div className="template-card-title"><h3><Link href={`/templates/${template.id}${resumeId ? `?resumeId=${encodeURIComponent(resumeId)}` : ''}`}>{template.title}</Link></h3><span className="template-style-label">{styleName[template.style] || template.style}</span></div><p>{template.description || '清晰的模块结构，适合整理自己的求职经历。'}</p><div className="tags">{template.tags.slice(0, 3).map((tag) => <span className="badge" key={tag}>{tag}</span>)}</div>{recommended && template.reasons?.length ? <div className="template-match">{template.reasons.join(' · ')}</div> : null}<Link className="template-use-link" href={`/templates/${template.id}${resumeId ? `?resumeId=${encodeURIComponent(resumeId)}` : ''}`}>{resumeId ? '套用到这份简历' : '查看并使用'} <span aria-hidden="true">↗</span></Link></div></article>)}</div> : !error ? <div className="empty-state"><h2>暂时没有符合条件的模板</h2><p className="muted">换一个关键词，或回到精品推荐。</p><button className="button secondary" onClick={() => { setKeyword(''); setActiveCategory('all'); setTemplates(allTemplates); setRecommended(false); }}>查看全部模板</button></div> : null}
        <p className="catalog-footnote">模板库会持续补充。第三方来源仅展示通过审核的公开结构信息，不复制受版权保护的正文或图片。</p>
      </main>
    </div>
  </div>;
}

export function TemplateDetail({ id }: { id: string }) {
  const { user } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const resumeIdFromQuery = params.get('resumeId');
  const [template, setTemplate] = useState<Template | null>(null);
  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [selected, setSelected] = useState(resumeIdFromQuery || 'new');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setTemplate((await api<{ template: Template }>(`/templates/${id}`)).template); }
    catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, [id]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!user) return;
    void api<{ resumes: ResumeDocument[] }>('/resumes').then((response) => {
      setResumes(response.resumes);
      if (resumeIdFromQuery && response.resumes.some((resume) => resume.id === resumeIdFromQuery)) setSelected(resumeIdFromQuery);
    }).catch((e) => setError(errorMessage(e)));
  }, [user, resumeIdFromQuery]);

  async function useStructure() {
    if (!user) { router.push(`/login?next=${encodeURIComponent(`/templates/${id}`)}`); return; }
    if (selected === 'new') { router.push(`/resumes/new?templateId=${encodeURIComponent(id)}`); return; }
    setBusy(true); setError('');
    try {
      const { resume } = await api<{ resume: ResumeDocument }>(`/resumes/${selected}`);
      const order = template?.sectionOrder || [];
      const sections = [...resume.sections].sort((a, b) => { const left = order.indexOf(a.type); const right = order.indexOf(b.type); return (left < 0 ? 99 : left) - (right < 0 ? 99 : right); }).map((section, index) => ({ ...section, order: index }));
      await api(`/resumes/${selected}`, json('PATCH', { title: resume.title, sections, templateId: id, revision: resume.revision }));
      router.push(`/resumes/${selected}`);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }

  if (loading) return <div className="page-state" role="status"><span className="spinner" />正在加载模板结构…</div>;
  if (!template) return <div className="page-state"><h1>模板暂不可用</h1><p role="alert">{error}</p><Link className="button" href="/templates">返回模板库</Link></div>;
  const source = safeUrl(template.sourceUrl);

  return <div className="page template-detail-page"><Link href={resumeIdFromQuery ? `/templates?resumeId=${encodeURIComponent(resumeIdFromQuery)}` : '/templates'} className="text-button">‹ 返回模板库</Link><div className="template-detail"><TemplateVisual template={template} /><div className="detail-info"><p className="panel-kicker">模板结构参考</p><h1>{template.title}</h1><p className="muted">{template.description || '参考清晰的模块顺序，整理属于你自己的求职经历。'}</p><div className="tags">{template.tags.map((tag) => <span className="badge" key={tag}>{tag}</span>)}<span className="badge">{styleName[template.style] || template.style}</span></div><h2>模块顺序</h2><div className="structure-list">{(template.sectionOrder || []).map((type) => <span key={type}>{sectionLabels[type] || type}</span>)}</div><p className="small-text muted">{source ? <a href={source} target="_blank" rel="noopener noreferrer">查看原始来源（新窗口）</a> : '来源：履历工坊原创结构'}<br />{template.license || '参考前请查看来源授权与适用范围。'}</p><div className="notice">只参考模块顺序、布局与风格。AI 生成结果先预览，经你确认后才写入简历。</div>{user && resumes.length ? <label className="field">应用到哪份简历<select value={selected} onChange={(event) => setSelected(event.target.value)}><option value="new">创建一份新简历</option>{resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}</option>)}</select></label> : null}{selected !== 'new' ? <p className="small-text muted">将调整所选简历的模块顺序，正文内容会保留。</p> : null}<button className="button teal" disabled={busy} onClick={() => void useStructure()}>{busy ? '正在应用结构…' : resumeIdFromQuery ? '套用到当前简历' : '使用此结构生成'}</button>{error ? <p className="notice error" role="alert">{error}</p> : null}</div></div></div>;
}
