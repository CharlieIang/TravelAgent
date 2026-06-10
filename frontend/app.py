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
ui.caption("多模态框架：语音/文本输入 + Langchain 框架 + 后端NLP管道")

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
    return text.replace("~", "至").replace("—", "-")

def clean_json_string(raw_str: str) -> str:
    """多级清洗管道：剥离 Markdown 标记，精准截取 {} 核心块并洗涤破坏性双引号"""
    if not raw_str:
        return ""
    text = re.sub(r"```json", "", raw_str, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
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
                ui.markdown(f"🌅 **上午安排**：\n{day_info.get('morning', '自由活动')}")
                if day_info.get('morning_img'):
                    ui.image(day_info.get('morning_img'), caption=f"{day_info.get('day')} 上午风景", width='stretch')
                ui.write("---")
                ui.markdown(f"☀️ **下午安排**：\n{day_info.get('afternoon', '自由活动')}")
                if day_info.get('afternoon_img'):
                    ui.image(day_info.get('afternoon_img'), caption=f"{day_info.get('day')} 下午风景", width='stretch')
                ui.write("---")
                ui.markdown(f"🌙 **晚上安排**：\n{day_info.get('evening', '自由活动')}")
                if day_info.get('evening_img'):
                    ui.image(day_info.get('evening_img'), caption=f"{day_info.get('day')} 晚上风景", width='stretch')

    # ==================== 🗺️ 地图纯净渲染 ====================
    coords_list = data.get("map_coordinates", [])
    if coords_list:
        ui.write("---")
        ui.subheader("🗺️ 智能行程地理路线大地图")
        try:
            df = pd.DataFrame(coords_list)
            if not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
                df = df.dropna(subset=['latitude', 'longitude'])
                df['latitude'] = df['latitude'].astype(float)
                df['longitude'] = df['longitude'].astype(float)
                ui.map(df, size=20, color='#ff4b4b')
        except Exception as e:
            ui.warning(f"🗺️ 地图层渲染时受到轻微干扰（原因: {str(e)}），请刷新重试。")

# 维护对话状态
if "messages" not in ui.session_state:
    ui.session_state.messages = [{"role": "assistant", "content": "你好！我是你的的智能旅游 Agent。现在你既可以打字、直接点击下方录音按钮对我说话、或者在左侧边栏上传图片让我识别！"}]

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

# ==================== 🖼️ 左侧边栏视觉多模态通道 ====================
with ui.sidebar:
    ui.subheader("🖼️ 视觉多模态输入")
    uploaded_image = ui.file_uploader(
        "上传攻略截图或景点照片：", 
        type=["png", "jpg", "jpeg"]
    )
    if uploaded_image is not None:
        ui.image(uploaded_image, caption="待解析素材", use_container_width=True)

# ==================== 🎤 底部独立大框多模态网关拦截 ====================
audio_file = ui.audio_input("🎤 点击录音并对 Agent 说话：")
text_input = ui.chat_input("或者在这里输入你的旅行规划想法...")

# ==================== 🧠 多模态路由网关拦截逻辑 ====================
user_input = None
input_mode = "text"  # 可选：text, voice, vision

# 优先判定视觉上传：通过对比文件名与 session_state 锁实现单次解析防抖
if uploaded_image is not None:
    current_img_id = f"{uploaded_image.name}_{uploaded_image.size}"
    if ui.session_state.get("last_processed_image") != current_img_id:
        with ui.spinner("👁️ 视觉大模型正在深度解析图片语义..."):
            try:
                from backend.vision_engine import analyze_travel_image
                extracted_text = analyze_travel_image(uploaded_image)
                if extracted_text and "错误" not in extracted_text:
                    user_input = extracted_text
                    input_mode = "vision"
                    ui.session_state["last_processed_image"] = current_img_id
            except Exception as e:
                ui.error(f"❌ 视觉模块调用失败，请检查 backend/vision_engine.py 配置: {str(e)}")

# 清除图片时释放锁
if uploaded_image is None and "last_processed_image" in ui.session_state:
    del ui.session_state["last_processed_image"]

# 处理语音拦截（仅在无全新视觉输入时判定）
if not user_input and audio_file is not None:
    audio_bytes = audio_file.read()
    with ui.spinner("🧠 正在识别您的语音语义..."):
        try:
            from backend.asr_engine import transcribe_audio
            user_input = transcribe_audio(audio_bytes)
            input_mode = "voice"
        except Exception as e:
            ui.error(f"❌ 语音识别模块调用失败: {str(e)}")

# 处理标准的文本框输入
if not user_input and text_input:
    user_input = text_input
    input_mode = "text"

# ==================== 🚀 核心路由与 Agent 执行体 ====================
if user_input:
    # 前端用户侧气泡回显
    with ui.chat_message("user"):
        if input_mode == "vision":
            display_text = f"🖼️ (图片解析结果) {user_input}"
        elif input_mode == "voice":
            display_text = f"🎤 (语音输入) {user_input}"
        else:
            display_text = user_input
        ui.markdown(display_text)
        
    ui.session_state.messages.append({"role": "user", "content": user_input})

    # 后端智能体决策链
    with ui.chat_message("assistant"):
        message_placeholder = ui.empty()
        
        if not nlp_processor.check_safety(user_input):
            message_placeholder.error("🚨 **【NLP安全拦截】** 输入包含违规词汇。")
            ui.session_state.messages.append({"role": "assistant", "content": "您的输入未通过系统安全审查。"})
        else:
            cleaned_input = nlp_processor.clean_text(user_input)
            message_placeholder.markdown(f"🧠 **[NLP预处理完毕]** 已锁定语义，Agent 正在多套工具连环调度...")
            
            try:
                langchain_history = []
                for m in ui.session_state.messages[:-1]:
                    if m["role"] == "user":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                response = agent_executor.invoke({"input": cleaned_input, "chat_history": langchain_history})
                ai_reply = response["output"]
                
                if "{" in ai_reply and "}" in ai_reply:
                    fixed_live_json = clean_json_string(ai_reply)
                    structured_data = json.loads(fixed_live_json)
                    message_placeholder.empty()
                    render_itinerary_card(structured_data)
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
                else:
                    message_placeholder.markdown(ai_reply)
                    ui.session_state.messages.append({"role": "assistant", "content": ai_reply})
            except Exception as e:
                message_placeholder.error(f"❌ 结构化渲染出错了：{str(e)}")
