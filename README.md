# TravelAgent 🌍

一个基于 AI 的智能旅行规划助手，融合 LangChain、DeepSeek API 和多个工具集成。

## 📋 项目结构

```
travel-agent-project/
├── backend/                  # 后端核心逻辑
│   ├── main.py               # Web 服务入口 (FastAPI)
│   ├── agent.py              # LangChain / Agent 核心逻辑
│   ├── tools/                # MCP 工具集 (天气、地图 API 封装)
│   └── config.py             # 配置文件 (存放 DeepSeek API Key 等)
├── frontend/                 # 前端展示
│   └── app.py                # 你的 Gradio 或 Streamlit 运行脚本
├── requirements.txt          # 项目依赖包列表
└── README.md                 # 项目说明文档
```

## 📁 目录说明

| 目录/文件 | 说明 |
|---------|------|
| `backend/main.py` | FastAPI Web 服务的入口文件，处理 HTTP 请求 |
| `backend/agent.py` | LangChain Agent 的核心逻辑，实现 AI 决策 |
| `backend/tools/` | MCP 工具集，包含天气、地图等 API 的封装 |
| `backend/config.py` | 环境变量和配置常量（API Keys、模型参数等） |
| `frontend/app.py` | 用户界面（Gradio 或 Streamlit）的运行脚本 |
| `requirements.txt` | Python 依赖包列表 |

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip 或 conda

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
编辑 `backend/config.py`，设置：
- DeepSeek API Key
- 地图 API Key
- 天气 API Key

### 运行服务

**后端（FastAPI）：**
```bash
cd backend
python main.py
```

**前端（Gradio/Streamlit）：**
```bash
cd frontend
python app.py
```

## 🛠 核心功能

- ✨ AI 驱动的旅行规划建议
- 🌤️ 实时天气查询
- 🗺️ 地图导航集成
- 💬 自然语言交互

## 📝 License

MIT
