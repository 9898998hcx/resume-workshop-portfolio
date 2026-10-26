# 简历工坊 FastAPI 基础后端

这是阶段一新增的 Python 后端基础。它与现有 NestJS API 并行存在，默认监听 `127.0.0.1:8000`，不会修改现有 `apps/`、`prisma/` 或前端代码。

## 环境要求

- Python 3.11+
- Windows PowerShell
- SQLite（Python 内置）
- MySQL 8.0 仅在生产切换时需要

## 创建虚拟环境

在仓库根目录执行：

```powershell
cd D:\codex-1
& "<Python 3.11 路径>\python.exe" -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\backend[dev]
```

如果本机安装了 Python Launcher，也可以使用：

```powershell
py -3.11 -m venv .venv
```

`backend/.env` 已提供本地空密钥配置；真实密钥不要写入代码或 Git。

## 迁移 SQLite

```powershell
\.venv\Scripts\alembic.exe -c .\backend\alembic.ini upgrade head
```

数据库文件：

```text
D:\codex-1\data\resume_workshop.db
```

查看迁移状态：

```powershell
\.venv\Scripts\alembic.exe -c .\backend\alembic.ini current
```

## 启动 FastAPI

```powershell
\.venv\Scripts\uvicorn.exe app.main:app `
  --app-dir .\backend `
  --host 127.0.0.1 `
  --port 8000
```

测试地址：

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/health/db
- http://127.0.0.1:8000/docs

## MySQL 切换

不要在同一环境同时把 SQLite 和 MySQL 当作主库。切换前设置同一个 `DATABASE_URL`：

```powershell
$env:DATABASE_URL="mysql+pymysql://user:password@127.0.0.1:3306/resume_workshop?charset=utf8mb4"
\.venv\Scripts\alembic.exe -c .\backend\alembic.ini upgrade head
```

MySQL 数据库需要提前创建为 `utf8mb4`。阶段一不会自动创建远程数据库，也不会把本地 SQLite 数据导入 MySQL。

## 阶段一接口

- `GET /health`：进程健康检查
- `GET /api/health/db`：数据库连接检查
- `POST /api/ai/polish`：Mock 润色预览，不会写入简历
- `POST /api/resume/render`：Mock PDF 渲染占位
- `POST /api/auth/phone/send-code`：短信占位，当前不发送验证码
- `POST /api/auth/phone/verify-code`：手机号登录占位

## 测试

```powershell
\.venv\Scripts\pytest.exe .\backend\tests -q
```

## 模板采集与模板库接口

模板采集器位于 `backend/scripts/fetch_templates.py`，来源配置位于
`backend/scripts/template_sources.json`。默认只处理配置中已启用、且许可证在
allowlist 中的 GitHub 来源；公开网页来源默认关闭。采集器不会登录、绕过验证码、
下载第三方图片或执行模板 HTML。

先安装采集器依赖：

```powershell
python -m pip install -r .\backend\requirements.txt
```

建议先做不写文件的检查：

```powershell
\.venv\Scripts\python.exe .\backend\scripts\fetch_templates.py `
  --max-templates 5 `
  --min-interval 3 `
  --dry-run
```

GitHub API 未认证时有较低的公共速率限制。需要批量采集时，在当前 PowerShell 会话
中设置个人 GitHub Token（只读权限即可，不要提交到 Git）：

```powershell
$env:GITHUB_TOKEN="ghp_your_read_only_token"
\.venv\Scripts\python.exe .\backend\scripts\fetch_templates.py `
  --max-templates 20 `
  --output .\data\templates
```

输出目录中的每个模板包含 `template.json`、清洗后的 `index.html`/`style.css` 或
`schema.json`，并生成聚合文件 `data/templates/templates.json`。记录默认是待审核状态，
不会自动在前台展示。网页来源只有在完成当前 robots.txt 和 ToS 审核后，才可在配置中
启用并使用 `--allow-web`：

```powershell
\.venv\Scripts\python.exe .\backend\scripts\fetch_templates.py `
  --allow-web --max-templates 20 --output .\data\templates
```

接口只返回已审核且启用的模板：

```text
GET http://127.0.0.1:8000/api/templates
GET http://127.0.0.1:8000/api/templates/{id}
```

列表接口只返回名称、分类、来源和预览图等元数据；详情接口才返回清洗后的 HTML、
CSS 和 JSON Schema。导入数据库时应保留 `source_url`、`source_commit`、`license`、
`license_url`，并由管理员审核后把 `status` 设为 `approved`、`is_active` 设为 `true`。
