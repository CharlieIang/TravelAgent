# TravelAgent

# Project structure
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
