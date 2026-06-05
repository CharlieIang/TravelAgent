# frontend/app.py
"AI智能旅游行程规划助手 - 前端界面"

import sys
import os
import streamlit as ui
from langchain_core.messages import HumanMessage, AIMessage

# 【核心工程细节】：确保 Python 能够跨文件夹找到 backend 目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.nlp_engine import NLPProcessor
from backend.agent_core import get_agent_executor

# 初始化前端页面
ui.set_page_config(page_title="AI智能旅游行程规划助手", page_icon="✈️", layout="centered")
ui.title("✈️ 智能旅游行程规划 Agent")
ui.caption("标准分层架构：前端(Streamlit) + 后端NLP预处理管道 + LangChain Agent")

# 初始化组件
nlp_processor = NLPProcessor()
agent_executor = get_agent_executor()

if not agent_executor:
    ui.error("❌ 未检测到环境变量 DEEPSEEK_API_KEY，请先配置！")
    ui.stop()

# 维护对话状态
if "messages" not in ui.session_state:
    ui.session_state.messages = [{"role": "assistant", "content": "你好！我是分层架构升级版的智能旅游 Agent。请告诉我你想去哪儿玩！"}]

for msg in ui.session_state.messages:
    with ui.chat_message(msg["role"]):
        ui.markdown(msg["content"])

# 接收输入
if user_input := ui.chat_input("输入你的旅行规划想法..."):
    with ui.chat_message("user"):
        ui.markdown(user_input)
    ui.session_state.messages.append({"role": "user", "content": user_input})

    with ui.chat_message("assistant"):
        message_placeholder = ui.empty()
        
        # 1. 后端 NLP 管道安全拦截
        if not nlp_processor.check_safety(user_input):
            message_placeholder.error("🚨 **【NLP安全拦截】** 输入包含违规词汇，已自动拒绝处理。")
            ui.session_state.messages.append({"role": "assistant", "content": "您的输入未通过系统安全审查。"})
        else:
            # 2. 后端 NLP 管道数据清洗与分析
            cleaned_input = nlp_processor.clean_text(user_input)
            slots = nlp_processor.extract_travel_slots(cleaned_input)
            nlp_tips = f"（本地正则解析游玩时长：{slots['extracted_days']}天）" if slots["extracted_days"] else ""
            
            message_placeholder.markdown(f"🧠 **[NLP预处理完毕]**\n* 清洗后核心输入：`{cleaned_input}` {nlp_tips}\n\n🤔 Agent 正在拼命调度工具...")
            
            try:
                # 3. 提取历史记录并转交 Agent 执行
                langchain_history = []
                for m in ui.session_state.messages[:-1]:
                    if m["role"] == "user":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                # 唤醒 Agent大脑
                response = agent_executor.invoke({"input": cleaned_input, "chat_history": langchain_history})
                ai_reply = response["output"]
                
                message_placeholder.markdown(ai_reply)
                ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                message_placeholder.markdown(f"❌ 运行时出错了：{str(e)}")
