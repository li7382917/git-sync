# Git Sync — Design Document

## 概述

Git Sync 是一个轻量级 Flask 服务，用于将本地项目自动同步到 GitHub 个人仓库。核心场景：用户指定一个本地目录路径，服务自动判断 GitHub 上是否存在同名仓库，不存在则创建，然后完成 commit 和 push。

## 架构设计

```
┌──────────────┐     HTTP      ┌──────────────┐
│  Web UI      │ ────────────> │  Flask App   │
│  (browser)   │ <──────────── │  (app.py)    │
└──────────────┘    JSON       └──────┬───────┘
                                      │
                               ┌──────▼───────┐
                               │   syncer.py   │  ← 编排层
                               └──┬────────┬───┘
                                  │        │
                          ┌───────▼──┐ ┌───▼────────┐
                          │ git_ops  │ │  github.py  │
                          │ (本地git)│ │ (GitHub API)│
                          └──────────┘ └─────────────┘
```

### 分层职责

| 层           | 文件            | 职责                         |
|-------------|----------------|------------------------------|
| **路由层**   | `app.py`       | HTTP 请求解析、响应序列化      |
| **编排层**   | `syncer.py`    | 同步流程编排，步骤记录          |
| **Git 操作** | `git_ops.py`   | 本地 git 命令封装              |
| **GitHub API** | `github.py` | 远程仓库检查、创建              |
| **配置**     | `config.py`    | Token/用户名加载与管理          |

### 设计原则

1. **单一职责** — 每个模块只做一件事
2. **无状态** — 服务不持久化任何数据，每次请求独立执行
3. **幂等性** — 重复调用 sync 不会产生副作用（已存在就跳过创建，无变更就跳过 commit）
4. **渐进式** — 每个步骤独立执行并记录，方便排查

## 同步流程

```
POST /sync {"path": "/path/to/project"}
     │
     ▼
  ① git init（如果不是 git 仓库）
  ② 创建 .gitignore（如果不存在）
     │
     ▼
  ③ 查询 GitHub API: GET /repos/{user}/{repo}
     ├── 200 → repo 已存在，继续
     └── 404 → POST /user/repos 创建
     │
     ▼
  ④ 配置 origin remote（add 或 set-url）
     │
     ▼
  ⑤ git add -A → git diff --cached --quiet
     ├── 无变更 → 跳过 commit
     └── 有变更 → git commit -m "message"
     │
     ▼
  ⑥ git push -u origin main
     ├── 失败 → 尝试 master 分支
     └── 再失败 → force push main
     │
     ▼
  返回 {"ok": true, "repo": "url", "steps": [...]}
```

## 配置加载策略

Token 加载优先级：

1. 环境变量 `GITHUB_TOKEN`
2. `~/.hermes/.env` 文件中的 `GITHUB_TOKEN=xxx`

用户名：

1. 环境变量 `GITHUB_USER`
2. 默认值（硬编码 fallback）

## API 设计

### POST /sync

| 字段       | 类型    | 必填 | 说明                     |
|-----------|---------|------|--------------------------|
| path      | string  | ✓    | 本地项目绝对路径           |
| message   | string  |      | commit message，默认 "auto-sync" |
| private   | boolean |      | 是否创建私有仓库，默认 false |

### GET /check/{repo_name}

仅查询，不修改任何状态。

## 安全考虑

- GitHub Token 仅在服务端使用，不暴露给前端
- Token 通过 HTTPS 传输到 GitHub API
- remote URL 中嵌入 token 用于 push（git credential 方式）
- 服务默认绑定 `0.0.0.0:5050`，生产环境应限制为 `127.0.0.1`

## 未来扩展

- [ ] 批量同步（扫描目录下所有子项目）
- [ ] 定时同步（cron 模式）
- [ ] 同步历史持久化（SQLite）
- [ ] 支持 GitLab / Gitee
- [ ] Webhook 触发同步
