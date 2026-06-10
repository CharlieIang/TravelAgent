# TravelAgent 🌍

一个基于 AI 的智能旅行规划助手，融合 LangChain、DeepSeek API 和多个工具集成。

## 📋 项目结构

```
TravelAgent/
│
├── backend/                  # 后端核心逻辑文件夹
│   ├── nlp_engine.py         # NLPProcessor 文本清洗类
│   ├── agent_core.py         # 工具定义、Agent 构建逻辑
│   ├── asr_engine.py         # 语音识别引擎
│   └── vision_engine.py       # 图像识别和视觉处理引擎
│
├── frontend/                 # 前端界面文件夹
│   └── app.py                # 前端 UI 渲染与交互
│
└── README.md                 # 项目说明文档
```

## 🛠 核心功能

- ✨ AI 驱动的旅行规划建议
- 🌤️ 实时天气查询
- 🗺️ 地图导航集成
- 💬 自然语言交互
- 🎤 语音输入识别（ASR）
- 👁️ 图像识别与分析（Vision）
