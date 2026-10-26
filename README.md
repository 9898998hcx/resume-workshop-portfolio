# 履历工坊 Resume Workshop

一个面向中文求职者的本地优先简历工作台。它把结构化简历编辑、模板结构参考、DeepSeek AI 辅助和中文 PDF 导出放在同一个工作流里，适合个人使用、求职展示和作为全栈开源项目学习。

## 项目背景与目标

求职者通常需要在多个文档工具之间反复修改简历，既难以保持内容结构，也很难快速针对职位描述调整表达。本项目把“记录真实经历、选择结构、辅助润色、导出投递文件”串成一条可重复的本地工作流。

这是一个面向招聘方展示的个人全栈作品集项目，重点体现需求拆解、权限边界、AI 安全接入、响应式交互和工程化测试能力。目标用户是中文求职者，重点适配产品、研发、运营和应届校招等场景；当前版本不包含支付、多人协作和在线模板源文件分发。

## 在线演示

TODO：请在部署完成后补充公开演示地址。当前版本以本地运行和源码审阅为主，未声明任何线上服务地址。

## 核心功能

- 账号注册、登录、会话与 CSRF 防护。
- 简历创建、编辑、复制、删除、自动保存、版本快照和恢复。
- 基本信息、求职意向、教育、工作、项目、技能、证书、自我评价等模块的排序与显示控制。
- 左侧表单 + 右侧实时预览的响应式在线编辑器。
- DeepSeek 生成模块、润色、自我评价和改进建议；生成结果必须先预览，用户确认后才写入简历。
- BYOK（Bring Your Own Key）：用户可以在 AI 助手中保存自己的 DeepSeek API Key，服务端使用 AES-256-GCM 加密存储，接口和日志只显示脱敏值。
- 系统 Key 的每日额度、每分钟限流和月度 token 预算控制；自定义 Key 不占用系统每日额度。
- 多种模板结构、标签筛选、模板详情和“使用此结构生成”。模板只提供公开元数据和结构参考，爬虫默认关闭。
- 服务端 HTML + Playwright 生成 A4 中文 PDF，支持分页、中文字体和安全文件名。
- 最小管理后台：模板来源管理、抓取任务触发、审核、下架和审计日志。
- 完整测试：单元测试、HTTP 集成测试、爬虫合规测试和桌面/移动端 Playwright E2E。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Web | Next.js 16、React 19、TypeScript |
| API | NestJS 11、Node.js、Zod |
| 数据 | Prisma 6、SQLite（本地默认）、PostgreSQL（可选部署配置） |
| 限流/队列 | 内存适配器（本地默认）、Redis、BullMQ worker（可选） |
| AI | DeepSeek Chat Completions；后端 JSON Schema/Zod 校验、超时、重试和错误映射 |
| PDF | Playwright/Chromium、服务端 HTML 模板、Noto Sans CJK 或系统中文字体 |
| 测试 | Vitest、Node test runner、Supertest、Playwright |
| 存储/安全 | 本地 SQLite；可选 S3 兼容归档；AES-256-GCM 密钥加密、Cookie 会话、CSRF、审计日志 |

### 选型理由

- **Next.js 16 + React 19**：用 App Router 同时承载页面和对后端的 rewrite 代理，减少跨域与额外部署配置；服务端组件负责首屏与 SEO，客户端组件只承载编辑器、实时预览和 AI 面板等交互密集区域。
- **NestJS 11 + Zod**：按 auth、resume、ai、pdf、template、admin 划分领域模块，依赖注入便于替换限流器和存储实现；Zod 在运行时校验请求体与模型输出，补上 TypeScript 编译期覆盖不到的外部数据。
- **Prisma 6 + SQLite/PostgreSQL**：本地 SQLite 零依赖启动、迁移文件可审阅；生产环境可切换到 PostgreSQL 而业务代码不变，符合个人项目“先能跑、再可部署”的取舍。
- **DeepSeek Chat Completions + BYOK**：中文写作场景成本低、响应稳定；系统 Key 只提供受限的体验额度，用户可自带 Key，降低作品集长期演示的维护成本。
- **Playwright**：同一套 Chromium 既用于端到端测试，也用于服务端 A4 PDF 渲染，减少浏览器依赖的重复安装。
- **不引入重型状态管理**：页面状态集中在少量 hooks 和局部组件状态，当前规模下 Redux/Zustand 的抽象成本高于收益。

## 系统架构与核心数据流

项目采用单仓库、模块化单体结构，便于个人维护和求职展示：

```text
Next.js Web（3000）
  ├─ 注册/登录、简历列表、在线编辑器
  ├─ AI 助手、模板库、模板详情、管理后台
  └─ 通过 rewrite 调用 NestJS API（3001）
       ├─ Auth：会话、CSRF、权限与用户隔离
       ├─ Resume：简历 CRUD、版本快照、乐观并发
       ├─ AI：DeepSeek、BYOK、额度、预览采纳和脱敏日志
       ├─ PDF：服务端 HTML + Playwright + 中文字体
       ├─ Template/Admin：模板推荐、审核、下架和审计
       └─ Worker：合规爬虫与队列（默认关闭）
              ↓
       Prisma → SQLite（本地）/ PostgreSQL（部署配置）
       Redis → 多进程限流和 worker 协调（本地可用内存适配器）
```

核心数据流是：用户登录后创建简历 → 编辑器自动保存结构化模块 → 选择模板只改变模块顺序与版式约束 → AI 服务读取当前用户自己的简历并返回结构化预览 → 用户明确采纳后才写回 → PDF 服务再次按用户 ID 校验权限并生成 A4 文件。模板正文、完整图片和用户的 API Key 不进入模型提示词或普通日志。

## 页面与模块说明

- 首页：说明产品定位、编辑流程、模板结构和隐私边界。
- 注册/登录/邮箱验证：创建账号、会话登录和生产环境验证提示。
- 我的简历：新建、复制、删除和继续编辑简历。
- 简历编辑器：左侧分模块表单，右侧 A4 预览；支持显示/隐藏、排序、自动保存、版本恢复和 PDF 下载。
- AI 助手：按模块生成、润色、自我评价和改进建议；结果先预览，再采纳或放弃。
- 模板库/模板详情：按风格和岗位筛选、标签推荐、查看来源、套用模块结构。
- 管理后台：模板审核、来源配置、采集任务、下架和审计记录。

## 项目制作过程

1. **需求分析**：先拆分注册登录、简历 CRUD、AI 辅助、PDF、模板库和后台审核等 MVP，明确“AI 不能自动覆盖内容”和“爬虫默认关闭”两条安全约束。
2. **原型与视觉方向**：根据简历编辑器的表单/预览工作流，以及模板目录的分类、搜索、卡片网格模式，建立暖色编辑工作台和模板选择页面；只借鉴交互模式，不复制第三方模板正文或图片。
3. **项目搭建**：采用 Next.js + NestJS + Prisma 的单仓库结构，配置共享类型、SQLite 本地迁移、PostgreSQL 迁移目录、环境变量模板和 Windows/macOS 启动脚本。
4. **核心功能实现**：完成用户会话、用户隔离的简历接口、乐观并发保存、版本快照、模块排序/显示控制和移动端编辑视图。
5. **AI 接入**：抽象 DeepSeek 调用，加入 JSON Schema/Zod 校验、超时、重试、限流、预算统计、错误映射和 BYOK AES-256-GCM 加密；前端采用“生成预览 → 用户采纳”的状态流转。
6. **PDF 与模板**：使用服务端 HTML 和 Playwright 生成 A4 PDF，检查中文字体和分页；模板只存结构、标签和风格，套用时保留用户正文，并把样式同步到预览与 PDF。
7. **接口联调与排错**：通过健康检查、集成测试和浏览器 E2E 验证注册、编辑、刷新恢复、模板套用、AI mock、PDF 下载和删除流程；针对移动端按钮布局、Next Suspense 和 PDF 偶发连接关闭做了回归验证。
8. **响应式、性能与可访问性**：加入移动端编辑/预览切换、键盘 Escape 关闭面板、焦点管理、语义标签、加载/空状态、错误重试和基础 SEO metadata；生产构建使用 Next.js 优化输出。
9. **测试与部署准备**：运行 TypeScript 检查、Vitest、Node 爬虫合规测试、Playwright 桌面/移动端 E2E，并提供 Nginx、Compose 和 CI 示例；正式部署前仍需补充真实环境的密钥、备份、监控和域名配置。

## 关键难点与解决方案

- **AI 结果不能破坏原简历**：后端限制输出字段和场景，前端把生成内容当作草稿；润色采纳时按条目合并非空字段，保留模型未返回的姓名、时间和数字事实。
- **BYOK 密钥安全**：浏览器只发送一次明文 Key，服务端使用 AES-256-GCM 加密保存；设置接口只返回 `sk-****abcd`，AI 日志只记录场景、状态、耗时和 token 估算。
- **额度和并发**：系统 Key 使用每日/每分钟/月度预算限制，自定义 Key 不占用系统每日额度；数据库事务和 Redis/内存适配器共同避免并发超额。
- **模板合规**：爬虫默认关闭，来源必须有授权依据并通过 robots/ToS 检查；模板库展示结构元数据，审核后才能发布，支持下架和审计。
- **中文 PDF**：生成前检查 Chromium 和中文字体，服务端 HTML 做转义和输入大小限制，文件名清洗并按用户 ID 校验权限。

## 工程化与代码规范

- `apps/web` 按页面、组件和数据 hooks 拆分；`apps/api` 按 auth、resume、ai、pdf、template、admin 等领域模块拆分。
- `packages/shared` 维护简历 section 类型、字段定义和 AI schema，减少前后端契约漂移。
- 业务数据通过 Prisma/Alembic 迁移管理；配置只从 `.env` 读取，`.env.example` 只放占位值。
- UI 状态统一处理 loading、empty、error、retry 和 confirm；危险操作使用二次确认。
- 提交建议使用 `feat:`、`fix:`、`test:`、`docs:` 等前缀，保持一次提交只聚焦一个可审阅主题；禁止提交密钥、数据库、截图产物和依赖目录。
- 代码合并前至少运行 `npm run typecheck`、`npm test` 和相关 E2E；真实第三方 AI 在测试中使用 mock，避免产生费用。

## 运行前提

- Node.js **22.12 或更高版本**（推荐 Node.js 24）和 npm。
- Windows、macOS 或 Linux。默认不需要 Docker、PostgreSQL、Redis、SMTP 或云服务器。
- PDF 导出需要 Playwright 浏览器。脚本会尝试准备浏览器；手动运行时可执行 `npm run browser:install`。
- AI 功能需要 DeepSeek API Key；不配置 Key 时，注册、简历编辑、模板浏览和 PDF 导出仍可使用。

## 一键启动

在 GitHub 下载或克隆仓库后：

- Windows：双击项目根目录的 `start.bat`，或在 PowerShell 执行 `./start.bat`。
- macOS/Linux：在终端执行 `chmod +x start.sh && ./start.sh`。

启动脚本会检查 Node 版本、创建 `.env`（不会覆盖已有配置）、安装 npm 依赖、生成 Prisma Client、执行 SQLite 迁移，然后启动 API 和 Web。启动后打开：

```text
http://127.0.0.1:3000
```

首次启动建议保持终端窗口打开，以便查看 API、Next.js 和 PDF 浏览器错误。

后续重复启动会复用已有的 `node_modules` 和 Playwright 浏览器缓存；如果你更新了分支或 `package-lock.json`，请先手动执行 `npm ci`。

## 手动本地运行

如果不使用一键脚本，可以按以下步骤操作。

### 1. 安装依赖并复制环境变量

```bash
npm ci
cp .env.example .env
# Windows PowerShell：Copy-Item .env.example .env
```

如果 `.env` 已存在，请不要覆盖它。至少生成一个本地加密密钥：

```bash
node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"
```

将输出的 **64 位十六进制字符串**填入：

```dotenv
USER_SECRET_ENCRYPTION_KEY=这里填入上一步生成的64位字符串
```

这个值用于加密用户自定义 DeepSeek Key。丢失它将无法解密已经保存的用户 Key；本地开发请妥善备份，但不要提交到 GitHub。

### 2. 初始化数据库

```bash
npm run db:setup
```

本地默认数据库是 `prisma/dev.db`。它是持久化 SQLite 文件，不是临时内存数据库；不要把包含个人简历的数据库提交到公开仓库。

### 3. 准备 PDF 浏览器并启动

```bash
npm run browser:install
npm run dev
```

浏览器访问 `http://127.0.0.1:3000`。API 默认在 `http://127.0.0.1:3001`，Web 会通过 Next.js rewrite 访问 API。

## DeepSeek API Key 配置

项目支持两种 Key，用途不同。

### 方式 A：系统默认 Key（维护者或本地单用户）

1. 登录 [DeepSeek 开放平台](https://platform.deepseek.com/) 创建 API Key。
2. 打开项目根目录的 `.env`，填写服务端变量：

   ```dotenv
   DEEPSEEK_API_KEY=sk-你的系统Key
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   DEEPSEEK_MODEL=deepseek-flash
   ```

3. 保存文件并重启 `npm run dev`。

该 Key 只在 API 进程读取，**不要**写成 `NEXT_PUBLIC_DEEPSEEK_API_KEY`，也不要放进前端代码、截图、Issue 或提交记录。未配置系统 Key 时，AI 面板会提示用户配置自己的 Key。

### 方式 B：用户自己的 Key（BYOK）

1. 启动网站并注册/登录。
2. 打开任意简历的“AI 助手”。
3. 在“DeepSeek API Key”设置区域粘贴自己的 `sk-...` Key，点击“保存 Key”。
4. 页面只显示类似 `sk-****abcd` 的脱敏结果；服务端使用 `USER_SECRET_ENCRYPTION_KEY` 加密后写入数据库。
5. 留空或点击“清除并使用系统额度”后，用户会回退到系统 Key 和默认每日 3 次额度。

BYOK Key 永远不会返回给浏览器、写入 AI 生成日志或出现在异常响应中。上游返回 401 时，界面会显示“您的 API Key 无效，请检查后重试”。请只粘贴 DeepSeek Key，不要粘贴其他服务的 Token。

## 可选配置

`.env.example` 已列出完整配置。常用项如下：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `file:./dev.db` | 本地 SQLite；生产 PostgreSQL 使用独立 schema 和迁移 |
| `REDIS_URL` | `memory://` | 本地单进程限流；多进程/worker 时使用 Redis |
| `AI_DAILY_LIMIT` | `3` | 系统 Key 的每日生成次数 |
| `AI_REQUESTS_PER_MINUTE` | `5` | 每用户每分钟生成次数 |
| `USER_SECRET_ENCRYPTION_KEY` | 必填 | 32 字节 AES-256-GCM 密钥，64 位十六进制 |
| `PDF_FONT_PATH` | 空 | 需要时指定 Noto Sans CJK 或其他中文字体文件 |
| `CRAWLER_ENABLED` | `false` | 合规爬虫总开关，保持关闭直到来源授权完成 |

## 管理员与模板审核

本地注册后，在项目根目录执行以下命令将账号设为管理员：

```bash
npm run admin -- your-email@example.com
```

然后重新登录并访问 `/admin`。模板采集默认关闭；只有明确获得授权、通过 robots.txt/ToS 检查并在后台审核通过的公开元数据才会展示。项目不绕过登录、验证码或访问控制，也不复制受版权保护的模板源文件、完整图片或正文。

## 项目截图（发布前补充）

建议把图片放在 `docs/screenshots/`，并在此处替换占位符。最能体现项目完成度的截图是：

1. 首页或登录页：展示产品定位和简洁视觉风格。
2. 简历编辑器桌面端：左侧模块表单、右侧实时预览、模块排序/显示控制同屏可见。
3. AI 助手面板：展示“生成内容预览”以及“采纳/放弃”按钮，突出不会自动覆盖简历。
4. BYOK 设置：展示脱敏 Key、额度提示和隐私说明，切勿截入真实 Key。
5. 模板详情：展示结构标签、来源链接和“使用此结构生成”入口。
6. PDF 成品：展示中文字体、A4 分页和专业模板效果。
7. 移动端编辑器：展示响应式布局和 AI 面板可用性。

```markdown
<!-- 发布前将文件放入 docs/screenshots/ 后取消注释 -->
![简历编辑器](docs/screenshots/resume-editor.png)
![AI 预览与采纳](docs/screenshots/ai-preview.png)
![模板详情](docs/screenshots/template-detail.png)
![中文 PDF](docs/screenshots/pdf-preview.png)
```

截图注意事项：使用演示账号和虚构经历；Key、邮箱、手机号、公司内部信息和本地文件路径都要打码。

## 测试与质量检查

```bash
npm run typecheck
npm test
npm run build
npm run test:e2e
npm audit
```

E2E 测试会覆盖桌面和移动视口；AI 成功响应使用受控 mock，不会产生模型费用。HTTP 集成测试使用 `artifacts/` 下的临时 SQLite 文件。真实 DeepSeek、SMTP、S3 和 Docker 服务不在默认本地测试中调用。

## 常见问题（FAQ）

### Node 版本不对怎么办？

查看版本：

```bash
node -v
```

项目要求 Node.js `>=22.12`。如果使用 nvm：

```bash
nvm install 22.12.0
nvm use 22.12.0
npm ci
```

Windows 也可以使用 nvm-windows；安装后重新打开终端，再执行 `node -v` 确认生效。

### 双击脚本后窗口立即关闭怎么办？

从 PowerShell 或终端运行脚本以保留错误输出：

```powershell
./start.bat
```

常见原因是 Node 版本过低、端口被占用或依赖安装失败。先执行 `node -v`、`npm -v`，再重新运行 `npm ci`。

### 端口 3000 或 3001 被占用怎么办？

Windows：

```powershell
Get-NetTCPConnection -LocalPort 3000,3001 -ErrorAction SilentlyContinue
```

macOS/Linux：

```bash
lsof -i :3000
lsof -i :3001
```

停止占用端口的进程，或在 `.env` 修改 `PORT` 并同步调整 `APP_ORIGIN`/`API_INTERNAL_URL`。

### AI 提示未配置或额度用完怎么办？

确认 `.env` 中的 `DEEPSEEK_API_KEY` 没有引号、空格或换行，并重启 API。个人用户也可以直接在 AI 助手中配置自己的 Key；系统 Key 默认每日 3 次，BYOK 不占用系统每日额度。Key 无效时请重新从 DeepSeek 控制台复制。

### PDF 中文乱码或浏览器找不到怎么办？

先安装浏览器：

```bash
npm run browser:install
```

Linux 还需要中文字体，例如 Debian/Ubuntu：

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk
```

必要时在 `.env` 设置 `PLAYWRIGHT_EXECUTABLE_PATH` 和 `PDF_FONT_PATH`。Windows 通常会自动检测 Edge 与系统中文字体。

### 没有 Redis 能不能运行？

可以。本地默认 `REDIS_URL=memory://`，适用于单进程开发。多 API 进程、独立 worker 或正式部署时应使用 Redis，否则限流状态不会跨进程共享。

### 手机能访问本地网站吗？

默认开发服务绑定 `127.0.0.1`，只能本机访问。需要手机联调时，将 Web 绑定到局域网地址（例如 `0.0.0.0`）、把 `.env` 的 `APP_ORIGIN` 改为电脑局域网 IP，并允许防火墙放行 3000 端口；然后用手机打开 `http://电脑局域网IP:3000`。不要把开发端口直接暴露到公网。

### 模板爬虫为什么没有数据？

这是默认安全策略。`CRAWLER_ENABLED=false`，且每个来源还必须明确授权、通过 robots/ToS 检查并经过管理员审核。未知或不允许采集的来源会被跳过，不会通过绕过登录或验证码来强行抓取。

### 如何清空本地开发数据？

停止开发服务后删除 `prisma/dev.db`，再执行：

```bash
npm run db:setup
```

此操作会删除本地账号、简历和模板，只适合没有需要保留的数据时使用。公开展示前请确认 `.gitignore` 未被修改，并且没有提交 `.env`、数据库或测试产物。

## 目录概览

```text
apps/web       Next.js 页面、编辑器、AI 面板和模板库
apps/api       NestJS API、认证、简历、AI、PDF、模板和后台模块
apps/worker    BullMQ/爬虫独立 worker
packages/shared 共享类型、校验 schema 和简历初始模块
prisma         SQLite schema、PostgreSQL schema 和迁移
tests          HTTP 集成、E2E 和爬虫合规测试
docs           PRD、架构、API、验收和部署记录
```

## 后续优化计划

1. TODO：补充线上演示地址、域名和部署截图。
2. 接入生产邮件、短信和 Turnstile，并完善手机号登录与邮箱验证策略。
3. 将 Redis、对象存储、备份和监控接入正式环境，增加数据库迁移回滚演练。
4. 在获得明确授权的前提下扩展模板来源，增加模板预览图和审核证据管理。
5. 增加更多 PDF 版式、打印质量回归和真实 DeepSeek 供应商契约测试。
6. 根据真实用户反馈优化模板推荐、AI 提示词和简历字段校验。

## 个人贡献与收获

本项目由个人完成，覆盖从需求澄清、数据模型、前后端实现到测试和部署准备的完整链路。作品集重点展示：

- 能把模糊的简历产品需求拆成可验收的模块和接口。
- 能在 AI 功能中处理结构化输出、额度、超时、重试、BYOK 密钥和日志脱敏。
- 能同时关注桌面端、移动端、无障碍、错误状态和数据越权等产品细节。
- 能用自动化测试验证关键流程，并基于真实失败日志修复回归问题。
- 能识别模板采集的版权和 robots/ToS 风险，建立默认关闭、审核和下架机制。

这套实现帮助我系统练习了 Next.js、React、NestJS、Prisma、Playwright、SQLite/PostgreSQL 迁移、AI 服务封装和安全工程，也为后续线上部署和持续迭代留下了清晰边界。

## 开源说明

这是一个本地优先的求职展示项目。默认不上传简历内容、不自动调用第三方模板站点，也不包含支付和多人协作。项目以 **MIT License** 开源，协议全文见根目录 `LICENSE`；如需其他协议可直接替换该文件。发布前已检查提交历史中没有 API Key、加密密钥、个人简历或测试账号。
