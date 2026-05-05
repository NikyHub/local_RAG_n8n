# 工厂 RAG 知识库系统

基于 n8n 工作流的工厂智能知识库，支持文档检索、经验回流、审核管理。

## 架构概览

```
前端 Chat Widget / 管理后台
        ↓ Webhook
n8n 工作流编排层 (5 个 workflow)
    ↙    ↓    ↓    ↘
Qdrant  PostgreSQL  文档处理服务  Embedding 服务
(向量库)  (元数据)   (PDF/OCR)    (bge-large-zh)
                              ↘
                          DeepSeek API (云)
```

## 快速开始

### 前置条件
- Docker & Docker Compose
- DeepSeek API Key

### 1. 配置环境变量

编辑 `.env` 文件，填入实际值：

```env
N8N_ADMIN_PASSWORD=your_password
N8N_HOST=your_server_ip
N8N_ENCRYPTION_KEY=random_32_char_string
DEEPSEEK_API_KEY=sk-your_deepseek_key
```

### 2. 启动所有服务

```bash
docker compose up -d
```

首次启动会自动：
- 初始化 PostgreSQL 数据库表
- 下载 Embedding 模型 (bge-large-zh-v1.5)
- 下载 PaddleOCR 模型

### 3. 初始化 Qdrant 向量库

```bash
bash scripts/init-qdrant.sh
```

### 4. 导入 n8n 工作流

1. 访问 `http://your_server:5678`，用配置的密码登录
2. 进入 **Settings → Credentials**，创建两个凭证：
   - **PostgreSQL**: host=postgres, port=5432, database=n8n, user=n8n, password=n8n_secret
   - **Header Auth**: name=deepseek-api, key=Authorization, value=Bearer sk-your_key
3. 进入 **Workflows → Import from File**，依次导入：
   - `n8n-workflows/doc-ingest.json`
   - `n8n-workflows/query.json`
   - `n8n-workflows/experience-submit.json`
   - `n8n-workflows/review.json`
   - `n8n-workflows/experience-ingest.json`
4. 每个 workflow 导入后，检查并修正节点中的凭证引用
5. **Activate** 所有 workflow（切换开关到 active）

### 5. 验证

```bash
# 测试查询接口
curl -X POST http://localhost:5678/webhook/query \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"注塑机如何保养？","session_id":"test1"}'

# 测试文档入库（先放一个 PDF 到 files/ 目录）
curl -X POST http://localhost:5678/webhook/doc-ingest \
  -H "Content-Type: application/json" \
  -d '{"title":"注塑机操作手册","doc_type":"manual","file_path":"/data/files/manual.pdf","mime_type":"application/pdf","machine_type":"注塑机","category":"operation","uploaded_by":"admin"}'
```

## 目录结构

```
├── docker-compose.yml          # 服务编排
├── .env                        # 环境变量
├── init-db.sql                 # 数据库建表
├── embedding-service/          # Embedding 服务 (bge-large-zh)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── document-service/           # 文档处理服务 (PyMuPDF + PaddleOCR)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── n8n-workflows/              # n8n 工作流 JSON
│   ├── doc-ingest.json         # 文档入库流
│   ├── query.json              # 知识查询流
│   ├── experience-submit.json  # 经验提交流
│   ├── review.json             # 审核处理流
│   └── experience-ingest.json  # 经验入库流
├── frontend/                   # 前端
│   ├── chat-widget.html        # Chat Widget (iframe 嵌入)
│   └── admin.html              # 管理后台
├── scripts/
│   └── init-qdrant.sh          # Qdrant 初始化
└── files/                      # 文档存储目录
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/webhook/query` | POST | 知识查询 |
| `/webhook/doc-ingest` | POST | 文档入库 |
| `/webhook/experience-submit` | POST | 提交经验 |
| `/webhook/review` | POST | 审核经验 |
| `/webhook/experience-ingest` | POST | 经验入库（内部触发） |

请求/响应格式详见各 workflow 的 Code 节点。

## 前端嵌入

```html
<!-- iframe 嵌入 Chat Widget -->
<iframe src="http://your_server:8080/chat-widget.html?user_id=worker_001&role=worker"
        style="width:400px;height:600px;border:none;" />
```

## 自定义通知

在 `experience-submit.json` 和 `review.json` 中，将 `NOTIFICATION_WEBHOOK_URL` 环境变量改为实际的通知 webhook：
- 企业微信机器人
- 钉钉机器人
- 邮件服务

## 服务端口

| 服务 | 端口 |
|------|------|
| n8n | 5678 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |
| PostgreSQL | 5432 |
| Embedding Service | 8001 |
| Document Service | 8002 |
