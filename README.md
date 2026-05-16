# Git Sync

本地项目一键同步到 GitHub — 自动创建仓库、commit、push。

## 功能

- **自动创建仓库** — 检测 GitHub 上是否存在同名 repo，不存在则自动创建
- **自动推送** — git init → add → commit → push 全流程自动化
- **Web UI** — 暗色风格可视化界面，支持同步操作和仓库检查
- **REST API** — 可被其他工具/脚本调用

## 快速开始

```bash
# 安装依赖
cd git-sync
uv sync

# 配置 GitHub Token（需要 repo 权限）
# 方式一：环境变量
export GITHUB_TOKEN=ghp_xxx
export GITHUB_USER=your-username

# 方式二：自动从 ~/.hermes/.env 读取

# 启动服务
uv run python app.py
```

浏览器打开 http://127.0.0.1:5050

## API

### POST /sync

同步项目到 GitHub。

```bash
curl -X POST http://127.0.0.1:5050/sync \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/project", "message": "feat: update", "private": false}'
```

响应：
```json
{
  "ok": true,
  "repo": "https://github.com/user/project",
  "steps": ["git_init", "repo_created: user/project", "remote_configured", "committed: feat: update", "pushed"]
}
```

### GET /check/\<repo_name\>

检查仓库是否存在。

```bash
curl http://127.0.0.1:5050/check/my-project
```

响应：
```json
{"repo": "my-project", "exists": true, "url": "https://github.com/user/my-project"}
```

## 项目结构

```
git-sync/
├── app.py                  # Flask 路由入口
├── git_sync/
│   ├── config.py           # GitHub 用户/Token/API 配置
│   ├── github.py           # GitHub API 操作
│   ├── git_ops.py          # Git 命令封装
│   └── syncer.py           # 核心同步逻辑
├── templates/
│   └── index.html          # Web UI
└── pyproject.toml
```

## 技术栈

- Python 3.11+ / Flask
- uv 包管理
- GitHub REST API v3
