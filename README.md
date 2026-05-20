# 工厂 RAG 知识库系统

基于 n8n 工作流的工厂智能知识库，支持文档检索、经验提交、邮件审批、图片识别与展示。

## 架构概览

```
工人 Chat Widget ──→ n8n 工作流编排 ──→ DeepSeek API (云端大模型)
  │                      │
  │           ┌──────────┼──────────┐
  │           ↓          ↓           ↓
  │        Qdrant    PostgreSQL   Document Service
  │       (向量库)    (元数据)    (PDF/OCR/文件存储)
  │           ↑                      │
  │           └─── Embedding Service ─┘
  │               (bge-large-zh-v1.5)
  │
  └── 班长 ← 邮件审批 ← 工人提交故障方案
```

## 快速部署

### 前置条件
- Docker & Docker Compose
- DeepSeek API Key（或其他兼容 OpenAI 格式的 API）

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 N8N_ADMIN_PASSWORD、DEEPSEEK_API_KEY 等
```

### 2. 一键启动

```bash
docker compose up -d
```

首次启动约 5-10 分钟（下载镜像 + 构建 Embedding 模型）。

### 3. 初始化 Qdrant 向量库

```bash
bash scripts/init-qdrant.sh
```

### 4. 初始化数据库表

```bash
docker exec -i pg_daoshu psql -U n8n -d n8n < init-db.sql
```

### 5. 导入 n8n 工作流

访问 `http://<服务器IP>:5678`，登录后：

**先配置凭证**（Settings → Credentials）：
- **PostgreSQL**：Host=`postgres`, Port=`5432`, Database=`n8n`, User=`n8n`, Password=`.env` 中的 DB_PASSWORD
- **DeepSeek API**：Header Auth 类型，Name=`Authorization`，Value=`Bearer sk-xxx`
- **SMTP**（可选）：用于邮件审批通知

**再导入工作流**（Import from File），按顺序：
| 文件 | 用途 |
|------|------|
| `n8n-workflows/RAG - 文档入库流.json` | PDF/图片上传 → 向量化入库 |
| `n8n-workflows/RAG - 知识查询流.json` | 问题检索 → 大模型生成答案 |
| `n8n-workflows/RAG - 经验提交流+审核处理流+入库流.json` | 工人提交 → 邮件审批 → 入库 |
| `n8n-workflows/RAG - 管理数据查询.json` | 后台看板数据 |

导入后每个工作流点击 **Activate** 激活。

### 6. 访问前端

- **工人端**：`http://<服务器IP>:9000/chat-widget.html?user_id=worker_001&role=worker`
- **管理后台**：`http://<服务器IP>:9000/admin.html`

前端需单独部署静态文件（如 Nginx 或 Python http.server）：
```bash
cd frontend && python -m http.server 9000
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| n8n | 5678 | 工作流编辑器 + Webhook |
| Qdrant HTTP | 6333 | 向量检索 API |
| Qdrant gRPC | 6334 | 向量写入 |
| PostgreSQL | 15432 | 元数据库 |
| Embedding Service | 8001 | 中文文本向量化 |
| Document Service | 8002 | PDF/OCR + 文件服务 |

## 目录结构

```
├── docker-compose.yml          # 一键部署
├── init-db.sql                 # 数据库表结构
├── README.md
├── embedding-service/          # Embedding 模型 (bge-large-zh-v1.5)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── document-service/           # 文档处理 (PyMuPDF + PaddleOCR)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── n8n-workflows/              # n8n 工作流 JSON
│   ├── RAG - 文档入库流.json
│   ├── RAG - 知识查询流.json
│   ├── RAG - 经验提交流+审核处理流+入库流.json
│   └── RAG - 管理数据查询.json
├── frontend/                   # 前端页面
│   ├── chat-widget.html        # 工人查询 + 经验提交
│   └── admin.html              # 管理看板 + 文档上传
└── scripts/
    └── init-qdrant.sh          # Qdrant 向量库初始化
```

## 核心业务流程

### 文档入库
```
组长上传 PDF/图片 → 解析文本 + OCR → 分块 → 向量化 → 写入 Qdrant
```

### 知识查询
```
工人提问 → 转向量 → Qdrant 检索 → Prompt 组装 → DeepSeek 生成 → 返回答案 + 来源 + 图片
```

### 经验闭环
```
工人提交故障方案(含图片) → 存入 PG → 邮件通知班长 → 班长点击批准
  → 图片 OCR → 文本向量化 → 写入 Qdrant → 查询可检索
```

## 硬件要求

| 项目 | 最低 | 推荐 |
|------|------|------|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GB | 16 GB |
| 磁盘 | 50 GB | 100 GB |
| 适用规模 | 50 人 | 200 人 |

## 运维说明

- **数据备份**：定期备份 `postgres_data` 和 `qdrant_data` 两个 volume
- **模型更新**：`docker compose build --no-cache embedding-service` 重建即可
- **工作流更新**：在 n8n 界面直接编辑，或重新导入 JSON
- **日志查看**：`docker compose logs -f n8n`
