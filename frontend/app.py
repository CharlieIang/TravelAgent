# frontend/app.py
import sys
import os
import json
import re
import pandas as pd
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

def escape_markdown_symbols(text: str) -> str:
    """将文本中的波浪号 ~ 替换为无害的连字符，防止 Streamlit 将其误解析为 Markdown 删除线"""
    if not text:
        return ""
    # 将可能引发闭合删除线的 ~ 统一替换为普通的波浪号或减号
    return text.replace("~", "至").replace("—", "-")

def clean_json_string(raw_str: str) -> str:
    """多级清洗管道：剥离 Markdown 标记，精准截取 {} 核心块并洗涤破坏性双引号"""
    if not raw_str:
        return ""
    
    # 去除 ```json 和 ``` 标记
    text = re.sub(r"```json", "", raw_str, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    
    # 截取第一个 '{' 到最后一个 '}' 之间的内容
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return raw_str
        
    target_str = text[start_idx:end_idx + 1]
    
    cleaned = re.sub(r'(?<![:,\{\[\]\s])"(?![,\}\]:\s])', '“', target_str)
    return cleaned

def render_itinerary_card(data):
    """统一渲染文本、多日Tabs和 Streamlit 原生稳定标点地图"""
    ui.success(f"📍 **您的专属定制路线：{data.get('destination')}**")
    
    raw_tips = data.get('weather_tips', '暂无天气提示')
    safe_tips = escape_markdown_symbols(raw_tips)
    ui.info(f"💡 **出行避坑与天气提示**：\n{safe_tips}")
    
    # 动态生成切换天数的标签页卡片
    itinerary_list = data.get("itinerary", [])
    tab_titles = [item.get("day", f"Day {i+1}") for i, item in enumerate(itinerary_list)]
    
    if tab_titles:
        tabs = ui.tabs(tab_titles)
        for idx, tab in enumerate(tabs):
            with tab:
                day_info = itinerary_list[idx]
                
                # 🌅 上午安排
                ui.markdown(f"🌅 **上午安排**：\n{day_info.get('morning', '自由活动')}")
                if day_info.get('morning_img'):
                    ui.image(day_info.get('morning_img'), caption=f"{day_info.get('day')} 上午风景", width='stretch')
                
                ui.write("---")
                
                # ☀️ 下午安排
                ui.markdown(f"☀️ **下午安排**：\n{day_info.get('afternoon', '自由活动')}")
                if day_info.get('afternoon_img'):
                    ui.image(day_info.get('afternoon_img'), caption=f"{day_info.get('day')} 下午风景", width='stretch')
                
                ui.write("---")
                
                # 🌙 晚上安排
                ui.markdown(f"🌙 **晚上安排**：\n{day_info.get('evening', '自由活动')}")
                if day_info.get('evening_img'):
                    ui.image(day_info.get('evening_img'), caption=f"{day_info.get('day')} 晚上风景", width='stretch')

    coords_list = data.get("map_coordinates", [])
    if coords_list:
        ui.write("---")
        ui.subheader("🗺️ 智能行程地理路线大地图")
        ui.caption("提示：可在上方大地图上使用鼠标滚轮任意放大、缩小或平移拖拽，查看各个景点的相对地理位置。")
        
        try:
            # 将大模型传回的经纬度字典列表转化为 Pandas DataFrame
            df = pd.DataFrame(coords_list)
            
            # 确保数据帧不为空且包含所需列名
            if not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
                # 过滤掉可能为空的坏数据行
                df = df.dropna(subset=['latitude', 'longitude'])
                
                # 强行转换数据类型为浮点数，彻底规避大模型吐出字符串引号导致的地图崩溃
                df['latitude'] = df['latitude'].astype(float)
                df['longitude'] = df['longitude'].astype(float)
                
                # 调用原生地图组件进行无缝二维渲染
                ui.map(df, size=20, color='#ff4b4b')
        except Exception as e:
            ui.warning(f"🗺️ 地图层渲染时受到轻微干扰（原因: {str(e)}），请刷新重试。")

# 维护对话状态
if "messages" not in ui.session_state:
    ui.session_state.messages = [{"role": "assistant", "content": "你好！我是智能旅游 Agent。请告诉我你想去哪儿玩，我会为您生成精美的卡片行程单！"}]

# 渲染历史聊天气泡
for msg in ui.session_state.messages:
    with ui.chat_message(msg["role"]):
        if "{" in msg["content"] and "}" in msg["content"]:
            try:
                fixed_json_str = clean_json_string(msg["content"])
                data = json.loads(fixed_json_str)
                render_itinerary_card(data)
            except Exception:
                ui.markdown(msg["content"])
        else:
            ui.markdown(msg["content"])

# 接收用户新输入
if user_input := ui.chat_input("输入你的旅行规划想法..."):
    with ui.chat_message("user"):
        ui.markdown(user_input)
    ui.session_state.messages.append({"role": "user", "content": user_input})

    with ui.chat_message("assistant"):
        message_placeholder = ui.empty()
        
        # 后端 NLP 安全拦截
        if not nlp_processor.check_safety(user_input):
            message_placeholder.error("🚨 **【NLP安全拦截】** 输入包含违规词汇，已自动拒绝处理。")
            ui.session_state.messages.append({"role": "assistant", "content": "您的输入未通过系统安全审查。"})
        else:
            # 后端 NLP 数据清洗
            cleaned_input = nlp_processor.clean_text(user_input)
            slots = nlp_processor.extract_travel_slots(cleaned_input)
            nlp_tips = f"（本地正则解析出游玩时长：{slots['extracted_days']}天）" if slots["extracted_days"] else ""
            
            message_placeholder.markdown(f"🤔 Agent 正在多套工具连环调度，正在提炼地理标点并渲染大地图...")
            
            try:
                # 提取历史记录转交 Agent 执行
                langchain_history = []
                for m in ui.session_state.messages[:-1]:
                    if m["role"] == "user":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                # 唤醒 Agent 思考
                response = agent_executor.invoke({"input": cleaned_input, "chat_history": langchain_history})
                ai_reply = response["output"]
                
                if "{" in ai_reply and "}" in ai_reply:
                    # 洗涤潜在的脏文本和 Markdown 标签
                    fixed_live_json = clean_json_string(ai_reply)
                    structured_data = json.loads(fixed_live_json)
                    
                    # 刷新占位符，渲染完全体
                    message_placeholder.empty()
                    render_itinerary_card(structured_data)
                    
                    # 保存到历史记录
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                else:
                    message_placeholder.markdown(ai_reply)
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
            except Exception as e:
                message_placeholder.error(f"❌ 结构化渲染出错了：{str(e)}")
                with ui.expander("查看原始大模型故障快照"):
                    ui.code(ai_reply, language="json")
