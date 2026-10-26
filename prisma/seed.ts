import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const sectionOrder = ['basic', 'intent', 'education', 'work', 'projects', 'skills', 'certificates', 'summary'];
const originals = [
  { slug: 'clean', title: '清晰起点', description: '原创单栏结构，以教育与项目呈现成长路径，适合应届生与初入职场者。', tags: ['应届生', '清爽', '单栏'], style: 'minimal', layout: 'single-column', sectionOrder },
  { slug: 'professional', title: '专业履历', description: '原创职业履历结构，先呈现工作成果与项目经验，适合有经验的求职者。', tags: ['职场', '专业', '技术'], style: 'professional', layout: 'single-column', sectionOrder: ['basic', 'intent', 'work', 'projects', 'skills', 'education', 'certificates', 'summary'] },
  { slug: 'compact', title: '精炼表达', description: '原创紧凑结构，突出核心技能与关键经历，适合技术与产品方向。', tags: ['技术', '产品', '紧凑'], style: 'compact', layout: 'single-column', sectionOrder: ['basic', 'intent', 'skills', 'work', 'projects', 'education', 'certificates', 'summary'] },
  { slug: 'campus', title: '校招清爽', description: '原创校招结构，先讲学习背景和项目实践，适合应届生展示成长线索。', tags: ['应届生', '校园', '简约'], style: 'minimal', layout: 'single-column', sectionOrder: ['basic', 'intent', 'education', 'projects', 'skills', 'work', 'certificates', 'summary'] },
  { slug: 'product', title: '产品成果', description: '原创成果导向结构，按工作、项目和技能组织内容，适合产品与运营岗位。', tags: ['产品', '运营', '成果'], style: 'professional', layout: 'single-column', sectionOrder: ['basic', 'intent', 'work', 'projects', 'skills', 'education', 'summary', 'certificates'] },
  { slug: 'engineering', title: '技术紧凑', description: '原创技术岗位结构，把技能和项目放在前面，便于快速扫描技术栈与产出。', tags: ['技术', '研发', '项目'], style: 'compact', layout: 'single-column', sectionOrder: ['basic', 'intent', 'skills', 'projects', 'work', 'education', 'certificates', 'summary'] },
  { slug: 'business', title: '商务留白', description: '原创商务结构，保留清晰的时间线和信息留白，适合咨询、金融与职能岗位。', tags: ['商务', '咨询', '金融'], style: 'professional', layout: 'single-column', sectionOrder: ['basic', 'intent', 'education', 'work', 'projects', 'certificates', 'skills', 'summary'] },
  { slug: 'creative', title: '创意表达', description: '原创创意岗位结构，用项目和技能讲清作品方法，适合设计与内容方向。', tags: ['设计', '创意', '作品'], style: 'minimal', layout: 'single-column', sectionOrder: ['basic', 'intent', 'projects', 'work', 'skills', 'education', 'certificates', 'summary'] },
];

async function main() {
  for (const template of originals) {
    await prisma.template.upsert({ where: { slug: template.slug }, create: { ...template, status: 'APPROVED', license: '项目原创模板，可自由参考结构' }, update: {} });
  }
  console.log(`已准备 ${originals.length} 个原创模板；未启用任何第三方采集来源。`);
}

main().catch(() => { console.error('模板初始化失败，请检查数据库配置与迁移。'); process.exitCode = 1; }).finally(async () => prisma.$disconnect());
