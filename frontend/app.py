# frontend/app.py
import sys
import os
import json
import re
import streamlit as ui
from langchain_core.messages import HumanMessage, AIMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.nlp_engine import NLPProcessor
from backend.agent_core import get_agent_executor

# 初始化前端页面配置
ui.set_page_config(page_title="AI智能旅游行程规划助手", page_icon="✈️", layout="centered")
ui.title("✈️ 智能旅游行程规划 Agent")
ui.caption("标准分层架构：前端(Tabs卡片化渲染) + 后端NLP预处理管道 + JSON结构化智能体")

# 初始化组件
nlp_processor = NLPProcessor()
agent_executor = get_agent_executor()

if not agent_executor:
    ui.error("❌ 未检测到环境变量 DEEPSEEK_API_KEY，请先配置！")
    ui.stop()

def clean_json_string(bad_json_str: str) -> str:
    """
    避免大模型文案中存在英文双引号，导致破坏JSON结构
    """
    if not bad_json_str:
        return ""
        
    # 利用贪婪匹配提取出真正包含在最外层 {} 内部的字符串块
    json_match = re.search(r"\{.*\}", bad_json_str, re.DOTALL)
    if not json_match:
        return bad_json_str
    
    target_str = json_match.group(0)
    
    # 匹配孤立英文双引号，安全替换为中文双引号 “
    cleaned = re.sub(r'(?<![:,\{\[\]\s])"(?![,\}\]:\s])', '“', target_str)
    return cleaned


# 维护对话状态
if "messages" not in ui.session_state:
    ui.session_state.messages = [{"role": "assistant", "content": "你好！我是架构与视觉全面重构的智能旅游 Agent。请告诉我你想去哪儿玩，我会为您生成精美的卡片行程单！"}]

# 渲染历史聊天气泡
for msg in ui.session_state.messages:
    with ui.chat_message(msg["role"]):
        try:
            # 1. 第一道防御：尝试寻找文本中是否潜伏着 JSON
            if "{" in msg["content"] and "}" in msg["content"]:
                # 2. 第二道防御：提取并使用黑魔法正则清洗历史记录里的“脏引号”
                fixed_json_str = clean_json_string(msg["content"])
                data = json.loads(fixed_json_str)
                
                # 开始渲染历史精美卡片
                ui.success(f"📍 **您的专属定制路线：{data.get('destination')}**")
                ui.info(f"💡 **出行避坑与天气提示**：\n{data.get('weather_tips')}")
                
                # 标签页切换卡
                itinerary_list = data.get("itinerary", [])
                tab_titles = [item.get("day", f"Day {i+1}") for i, item in enumerate(itinerary_list)]
                
                if tab_titles:
                    tabs = ui.tabs(tab_titles)
                    for idx, tab in enumerate(tabs):
                        with tab:
                            day_info = itinerary_list[idx]
                            ui.markdown(f"🌅 **上午安排**：\n{day_info.get('morning', '自由活动')}")
                            ui.markdown(f"☀️ **下午安排**：\n{day_info.get('afternoon', '自由活动')}")
                            ui.markdown(f"🌙 **晚上安排**：\n{day_info.get('evening', '自由活动')}")
            else:
                # 普通文本直接渲染
                ui.markdown(msg["content"])
        except Exception:
            # 极致容错：如果清洗后由于别的不可控原因依然报错，降级为普通纯文本渲染，确保界面绝对不崩溃
            ui.markdown(msg["content"])

# 接收用户新输入
if user_input := ui.chat_input("输入你的旅行规划想法..."):
    with ui.chat_message("user"):
        ui.markdown(user_input)
    ui.session_state.messages.append({"role": "user", "content": user_input})

    with ui.chat_message("assistant"):
        message_placeholder = ui.empty()
        
        # 后端 NLP 管道安全拦截
        if not nlp_processor.check_safety(user_input):
            message_placeholder.error("🚨 **【NLP安全拦截】** 输入包含违规词汇，已自动拒绝处理。")
            ui.session_state.messages.append({"role": "assistant", "content": "您的输入未通过系统安全审查。"})
        else:
            # 后端 NLP 管道数据清洗与分析
            cleaned_input = nlp_processor.clean_text(user_input)
            slots = nlp_processor.extract_travel_slots(cleaned_input)
            nlp_tips = f"（本地正则解析出游玩时长：{slots['extracted_days']}天）" if slots["extracted_days"] else ""
            
            message_placeholder.markdown(f"🧠 **[NLP预处理完毕]**\n* 核心输入：`{cleaned_input}` {nlp_tips}\n\n🤔 Agent正在为您提炼结构化行程...")
            
            try:
                # 提取历史记录并转交 Agent 执行
                langchain_history = []
                for m in ui.session_state.messages[:-1]:
                    if m["role"] == "user":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                # 唤醒 Agent 大脑
                response = agent_executor.invoke({"input": cleaned_input, "chat_history": langchain_history})
                ai_reply = response["output"]
                
                # 判断大模型的回复中是否存在 JSON 块
                if "{" in ai_reply and "}" in ai_reply:
                    # 对大模型即时生成的正文双引号进行拦截并洗白
                    fixed_live_json = clean_json_string(ai_reply)
                    
                    # 进行安全的 JSON 解析
                    structured_data = json.loads(fixed_live_json)
                    
                    # 刷新占位符，渲染前端高级组件
                    message_placeholder.empty()
                    
                    ui.success(f"📍 **您的专属定制路线：{structured_data.get('destination')}**")
                    ui.info(f"💡 **出行避坑与天气提示**：\n{structured_data.get('weather_tips')}")
                    
                    # 生成点击切换天数的标签页卡片
                    itinerary_list = structured_data.get("itinerary", [])
                    tab_titles = [item.get("day", f"Day {i+1}") for i, item in enumerate(itinerary_list)]
                    
                    if tab_titles:
                        tabs = ui.tabs(tab_titles)
                        for idx, tab in enumerate(tabs):
                            with tab:
                                day_info = itinerary_list[idx]
                                ui.markdown(f"🌅 **上午安排**：\n{day_info.get('morning')}")
                                ui.markdown(f"☀️ **下午安排**：\n{day_info.get('afternoon')}")
                                ui.markdown(f"🌙 **晚上安排**：\n{day_info.get('evening')}")
                    
                    # 保存原始生成的完整内容到会话历史
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    
                else:
                    # 如果只是正常的闲聊或没能生成标准的 JSON，降级回普通的文本渲染
                    message_placeholder.markdown(ai_reply)
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                # 若出现异常，打印错误，并把原始文本贴到前端 st.code 框中
                message_placeholder.error(f"❌ 运行时出错了：{str(e)}")
                with ui.expander("查看原始异常响应快照"):
                    ui.code(ai_reply, language="json")
