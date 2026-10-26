import Link from 'next/link';
import { MiniPaper } from '../components/resume-preview';

const showcaseTemplates = [
  { title: '经典蓝白', style: 'professional', tags: ['清晰分区', '双列信息'], sections: ['工作经历', '项目经历', '教育经历'] },
  { title: '现代斜条', style: 'modern', tags: ['轻量留白', '强调成果'], sections: ['个人优势', '工作经历', '项目经历'] },
  { title: '金领商务', style: 'executive', tags: ['稳重排版', '重点突出'], sections: ['核心能力', '工作经历', '教育经历'] },
  { title: '深蓝大气', style: 'compact', tags: ['时间线', '专业表达'], sections: ['工作经历', '项目经历', '证书荣誉'] },
  { title: '经典简约', style: 'clean', tags: ['通用结构', '易读清爽'], sections: ['自我评价', '技能', '教育经历'] },
];

export default function Home() {
  return <div className="home">
    <section className="hero hero-sunrise">
      <div className="hero-inner">
        <div className="hero-copy">
          <p className="intro-label">专注中文求职的简历工作台</p>
          <h1>做一份好简历，<br />让好工作找到你。</h1>
          <p className="hero-description">填写经历、挑选合适的结构，几分钟就能整理出一份清楚、可信、可以直接投递的 PDF 简历。</p>
          <div className="button-row">
            <Link href="/resumes" className="button hero-primary">免费开始制作 <span aria-hidden="true">→</span></Link>
            <Link href="/login" className="button hero-secondary">已有账号登录</Link>
          </div>
          <p className="hero-note"><span>实时预览</span><span>自动保存</span><span>中文 PDF</span></p>
        </div>
        <div className="hero-preview" aria-label="简历成品示意">
          <div className="paper-label"><span className="status-dot" />从经历到一页清晰的表达</div>
          <article className="sample-paper">
            <div className="sample-name">李轩辕</div>
            <p className="sample-role">产品经理 · 上海</p>
            <p className="sample-contact">chen@example.com　|　138 0000 0000</p>
            <h2>个人优势</h2>
            <p>连接用户需求与产品价值，用清晰的思考推进每一次迭代。</p>
            <h2>工作经历</h2>
            <div className="sample-line"><strong>远山科技</strong><span>2023.06 — 至今</span></div>
            <p>产品经理</p>
            <ul><li>负责企业协作产品的需求分析与迭代规划。</li><li>建立用户反馈机制，让真实需求驱动产品决策。</li></ul>
            <h2>项目经历</h2>
            <strong>让复杂工作，更有条理</strong>
            <p>从业务调研到功能落地，推动跨团队协作流程优化。</p>
            <h2>教育经历</h2>
            <div className="sample-line"><strong>同济大学</strong><span>管理学学士</span></div>
          </article>
          <div className="preview-caption">内容由你决定，表达可以更进一步。</div>
        </div>
      </div>
    </section>

    <section className="steps-strip" aria-label="制作步骤">
      <div className="home-inner steps-inner">
        <div className="step-item"><span>1</span><div><strong>填写内容</strong><small>基本信息、经历按提示填写</small></div></div>
        <div className="step-arrow" aria-hidden="true">→</div>
        <div className="step-item"><span>2</span><div><strong>选择结构</strong><small>参考模块顺序，随时可更换</small></div></div>
        <div className="step-arrow" aria-hidden="true">→</div>
        <div className="step-item"><span>3</span><div><strong>下载 PDF</strong><small>生成清晰排版，直接投递</small></div></div>
      </div>
    </section>

    <section className="home-metrics" aria-label="产品特点">
      <div className="home-inner metrics-inner">
        <div><strong>模块化</strong><span>经历自由排序</span></div>
        <div><strong>免费</strong><span>本地优先运行</span></div>
        <div><strong>实时</strong><span>编辑即刻预览</span></div>
        <div><strong>A4</strong><span>中文 PDF 导出</span></div>
      </div>
    </section>

    <section className="home-template-section" aria-labelledby="template-showcase-title">
      <div className="home-inner">
        <div className="home-section-heading"><h2 id="template-showcase-title">挑一个喜欢的简历结构</h2><p>每一款都为清楚表达而设计，选好结构后把内容交给你自己。</p></div>
        <div className="home-template-grid">
          {showcaseTemplates.map(template => <article className={`home-template-card ${template.style}`} key={template.title}>
            <Link className="home-template-visual" href="/templates" aria-label={`查看${template.title}结构`}><MiniPaper title="你的职业故事" sections={template.sections} /></Link>
            <div className="home-template-content"><h3>{template.title}</h3><p>{template.tags.join(' · ')}</p><Link href="/templates" className="button small">使用此结构</Link></div>
          </article>)}
        </div>
        <div className="showcase-more"><Link href="/templates" className="text-button">查看全部结构参考 →</Link></div>
      </div>
    </section>

    <section className="home-details" aria-labelledby="why-title">
      <div className="home-inner">
        <div className="home-section-heading"><h2 id="why-title">简单、清楚、由你决定</h2><p>从第一行经历到最后一页 PDF，每一步都看得见，也留给你确认。</p></div>
        <div className="detail-grid">
          <div className="detail-card"><span className="detail-symbol" aria-hidden="true">✦</span><h3>精心设计</h3><p>结构清楚、层次易读，让招聘者更快找到你的重点。</p></div>
          <div className="detail-card"><span className="detail-symbol" aria-hidden="true">↗</span><h3>高效便捷</h3><p>在线编辑、实时预览、自动保存，想到哪里写到哪里。</p></div>
          <div className="detail-card"><span className="detail-symbol" aria-hidden="true">✓</span><h3>隐私保护</h3><p>简历按账号隔离保存，AI 结果先预览，不会自动覆盖内容。</p></div>
          <div className="detail-card"><span className="detail-symbol" aria-hidden="true">＋</span><h3>本地优先</h3><p>不租服务器也能运行，源码、数据和配置都掌握在你手里。</p></div>
        </div>
      </div>
    </section>

    <section className="home-trust" id="trust" aria-labelledby="trust-title">
      <div className="home-inner trust-inner"><div className="trust-copy"><p className="intro-label">你的经历值得被认真对待</p><h2 id="trust-title">先写真实经历，<br />再让表达更清楚。</h2><p>AI 只提供建议，模板只提供结构参考。每一处写入都由你确认，每一份简历都可以继续编辑。</p><div className="trust-pills"><span>服务端权限校验</span><span>Key 加密存储</span><span>中文 PDF</span></div></div><div className="trust-card"><div className="trust-card-head"><span className="trust-lock">⌁</span><div><strong>履历工坊</strong><small>你的本地简历工作台</small></div><span className="trust-check">✓ 安全提示</span></div><div className="trust-row"><span>AI 生成结果</span><strong>先预览，再采纳</strong></div><div className="trust-row"><span>自定义 DeepSeek Key</span><strong>加密保存 · 脱敏展示</strong></div><div className="trust-row"><span>模板来源</span><strong>公开元数据 · 审核后展示</strong></div></div></div>
    </section>

    <section className="home-cta"><div className="home-inner"><h2>现在就动手，做一份心仪的简历吧</h2><p>选个合适的结构，几分钟就能下载一份整洁的 PDF 简历。</p><Link href="/resumes" className="button hero-primary">立即开始制作简历 <span aria-hidden="true">→</span></Link></div></section>
  </div>;
}
