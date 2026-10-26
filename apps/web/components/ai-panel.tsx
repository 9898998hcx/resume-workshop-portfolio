'use client';

import { useEffect, useRef, useState } from 'react';
import { api, errorMessage, json } from '../lib/api';
import {
  fieldDefinitions,
  sectionLabels,
  type AiSettings,
  type Generation,
  type Quota,
  type ResumeDocument,
  type SectionType,
} from '../lib/types';

const BYOK_HINT = '为了保护您的隐私及获得无限制的生成体验，您可以在 DeepSeek 官网申请 API Key 并填入此处。留空则使用系统默认额度（每日限 3 次）。';
type AiScenario = 'generate-section' | 'polish' | 'summary' | 'suggestions';

function sectionContent(resume: ResumeDocument, sectionType: SectionType) {
  return resume.sections.find((section) => section.type === sectionType)?.content
    .map((item) => Object.entries(item)
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n'))
    .join('\n\n') || '';
}

export function AiPanel({
  resume,
  onClose,
  beforeGenerate,
  onAccept,
  initialScenario = 'generate-section',
  initialSectionType = 'work',
}: {
  resume: ResumeDocument;
  onClose: () => void;
  beforeGenerate: () => Promise<boolean>;
  onAccept: (generation: Generation) => void;
  initialScenario?: AiScenario;
  initialSectionType?: SectionType;
}) {
  const [scenario, setScenario] = useState<AiScenario>(initialScenario);
  const [sectionType, setSectionType] = useState<SectionType>(initialSectionType);
  const [jd, setJd] = useState('');
  const [experience, setExperience] = useState('');
  const [busy, setBusy] = useState(false);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [error, setError] = useState('');
  const [settingsMessage, setSettingsMessage] = useState('');
  const [quota, setQuota] = useState<Quota | null>(null);
  const [settings, setSettings] = useState<AiSettings | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [result, setResult] = useState<Generation | null>(null);
  const [accepted, setAccepted] = useState(false);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
    let active = true;
    void Promise.all([api<Quota>('/ai/quota'), api<AiSettings>('/ai/settings')])
      .then(([nextQuota, nextSettings]) => {
        if (!active) return;
        setQuota(nextQuota);
        setSettings(nextSettings);
      })
      .catch((e) => { if (active) setError(errorMessage(e)); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !busy && !settingsBusy) onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose, busy, settingsBusy]);

  async function saveSettings(value: string | null) {
    setSettingsBusy(true);
    setError('');
    setSettingsMessage('');
    try {
      const saved = await api<AiSettings>('/ai/settings', json('PUT', { apiKey: value }));
      setSettings(saved);
      setApiKey('');
      setSettingsMessage(saved.configured ? 'API Key 已加密保存。' : '已清除自定义 Key，将使用系统默认额度。');
      setQuota(await api<Quota>('/ai/quota'));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSettingsBusy(false);
    }
  }

  function saveEnteredKey() {
    const value = apiKey.trim();
    if (!value && settings?.configured) {
      setSettingsMessage('当前 Key 保持不变。需要更换时请输入新的 Key；需要清除请使用下方按钮。');
      return;
    }
    void saveSettings(value || null);
  }

  async function generate() {
    setBusy(true);
    setError('');
    setAccepted(false);
    try {
      if (!await beforeGenerate()) {
        setError('简历尚未保存成功，请先处理编辑器中的保存错误。');
        return;
      }
      const target = scenario === 'summary' ? 'summary' : sectionType;
      const content = sectionContent(resume, target);
      const endpoint = scenario === 'polish' ? '/ai/polish' : '/ai/generate';
      const response = await api<Generation>(endpoint, json('POST', {
        resumeId: resume.id,
        scenario,
        sectionType: target,
        jd,
        experience,
        content,
        ...(resume.templateId ? { templateId: resume.templateId } : {}),
      }));
      setResult(response);
      setQuota((current) => current
        ? { ...current, remaining: response.quota.remaining, dailyLimit: response.quota.dailyLimit, budgetWarning: response.quota.budgetWarning }
        : current);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const quotaExhausted = quota?.remaining !== null && quota?.remaining !== undefined && quota.remaining <= 0;
  const isPolish = scenario === 'polish';

  return <>
    <button className="panel-overlay" aria-label="关闭 AI 助手" onClick={onClose} />
    <aside className="side-panel ai-panel" role="dialog" aria-modal="true" aria-labelledby="ai-title">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">辅助表达，不代替你做决定</p>
          <h2 id="ai-title" tabIndex={-1} ref={titleRef}>AI 写作助手</h2>
        </div>
        <button className="icon-button" aria-label="关闭 AI 助手" onClick={onClose}>×</button>
      </div>
      <p className="muted small-text">先生成预览，核对事实后再采纳到简历。AI 不会自动覆盖你的内容。</p>

      <section className="byok-settings" aria-labelledby="byok-title">
        <div className="panel-section-title"><span className="panel-icon">⌘</span><h3 id="byok-title">使用自己的 DeepSeek Key</h3></div>
        <p className="muted small-text">{BYOK_HINT}</p>
        {settings?.configured ? <p className="small-text">当前已配置：<code>{settings.maskedKey}</code></p> : null}
        <label className="field">
          API Key
          <input type="password" value={apiKey} disabled={settingsBusy} maxLength={256} autoComplete="off" onChange={(event) => setApiKey(event.target.value)} placeholder={settings?.configured ? '留空表示保持当前 Key' : 'sk-...'} />
        </label>
        <div className="button-row">
          <button className="button secondary small" disabled={settingsBusy} onClick={saveEnteredKey}>{settingsBusy ? '保存中…' : '保存 Key'}</button>
          {settings?.configured ? <button className="text-button danger" disabled={settingsBusy} onClick={() => void saveSettings(null)}>清除并使用系统额度</button> : null}
        </div>
        {settingsMessage ? <p className="notice success" role="status">{settingsMessage}</p> : null}
      </section>

      <div className="quota-line"><span>{quota?.usingCustomKey ? '正在使用您的 API Key，系统每日额度不适用' : quota ? `今日剩余 ${quota.remaining} / ${quota.dailyLimit} 次` : '正在读取额度…'}</span><span>由 DeepSeek 提供</span></div>
      {quota && !quota.configured ? <div className="notice warning">AI 服务尚未配置。请配置自己的 Key，或联系管理员设置系统 Key。</div> : null}

      <div className="ai-mode-switch" role="tablist" aria-label="AI 工作方式">
        <button role="tab" aria-selected={isPolish} className={isPolish ? 'active' : ''} disabled={busy} onClick={() => { setScenario('polish'); setResult(null); setAccepted(false); }}>润色当前模块</button>
        <button role="tab" aria-selected={!isPolish} className={!isPolish ? 'active' : ''} disabled={busy} onClick={() => { setScenario('generate-section'); setResult(null); setAccepted(false); }}>生成与建议</button>
      </div>

      <label className="field">辅助场景
        <select value={scenario} disabled={busy} onChange={(event) => { setScenario(event.target.value as AiScenario); setResult(null); setAccepted(false); }}>
          <option value="polish">润色已有内容</option>
          <option value="generate-section">根据经历生成模块</option>
          <option value="summary">生成自我评价</option>
          <option value="suggestions">查看改进建议</option>
        </select>
      </label>
      {scenario !== 'summary' ? <label className="field">目标模块
        <select value={sectionType} disabled={busy} onChange={(event) => { setSectionType(event.target.value as SectionType); setResult(null); }}>
          {Object.entries(sectionLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select>
      </label> : null}
      <label className="field">目标职位描述（可选）<textarea value={jd} disabled={busy} maxLength={8000} onChange={(event) => setJd(event.target.value)} placeholder="粘贴职位要求，让表达更贴近目标岗位。" /></label>
      {!isPolish ? <label className="field">你的真实经历<textarea value={experience} disabled={busy} maxLength={10000} onChange={(event) => setExperience(event.target.value)} placeholder="写下你做了什么、用了什么方法、带来什么成果。请勿提供身份证等敏感信息。" /></label> : <div className="notice">当前模块内容会自动带入润色请求，你只需要核对事实、数字和时间。</div>}
      {resume.templateId ? <p className="notice">已参考所选模板的模块顺序与风格。不会向模型提供模板正文或图片。</p> : null}
      <button className="button teal full" disabled={busy || quotaExhausted} onClick={() => void generate()}>{busy ? <><span className="spinner" />正在生成，请稍候…</> : result ? '重新生成预览' : isPolish ? `润色${sectionLabels[sectionType]}` : '生成并预览'}</button>
      {error ? <div className="notice error" role="alert">{error}<br /><button className="text-button" onClick={() => void generate()} disabled={busy}>重试</button></div> : null}

      {result ? <section className="ai-result" aria-live="polite">
        <div className="ai-result-heading"><div><p className="panel-kicker">待你确认</p><h3>{result.scenario === 'suggestions' ? '改进建议' : '生成内容预览'}</h3></div><span className="ai-preview-badge">未写入简历</span></div>
        <p className="small-text muted">请先核对事实和数字。只有点击“采纳”后，内容才会回到左侧编辑器。</p>
        {result.result.items.map((item, index) => <div className="ai-result-entry" key={index}>{Object.entries(item).map(([key, value]) => <div className="ai-result-text" key={key}><strong>{fieldDefinitions[result.result.sectionType]?.find(([field]) => field === key)?.[1] || key}：</strong>{value}</div>)}</div>)}
        {result.result.suggestions.length ? <ul className="small-text ai-suggestions">{result.result.suggestions.map((suggestion, index) => <li key={index}>{suggestion}</li>)}</ul> : null}
        {result.scenario === 'suggestions' ? <div className="notice">这些建议仅供参考，不会直接写入简历。请根据真实经历手动修改。</div> : accepted ? <p className="notice success" role="status">已采纳到编辑器，可继续修改；系统将自动保存。</p> : <div className="button-row"><button className="button teal" disabled={!result.result.items.length} onClick={() => { onAccept(result); setAccepted(true); }}>采纳到{sectionLabels[result.result.sectionType]}</button><button className="button secondary" onClick={() => setResult(null)}>放弃此结果</button></div>}
      </section> : null}
    </aside>
  </>;
}
