# backend/vision_engine.py
import os
import base64
from openai import OpenAI

def encode_image_to_base64(image_file) -> str:
    """将 Streamlit 接收到的图片文件转换为 Base64 编码字符串"""
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

def analyze_travel_image(image_file) -> str:
    """【视觉多模态核心】调用通义千问 VLM 模型，解析图片中的旅游意图"""
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return "错误：未配置阿里云百炼 API Key"
            
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 将图片转换为 Base64 格式
        base64_image = encode_image_to_base64(image_file)
        
        # 组装多模态消息体，向 VLM 发起视觉问答
        response = client.chat.completions.create(
            model="qwen-vl-max",  # 阿里云百炼的主力视觉大模型
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "你是一个专业的旅游视觉分析专家。请仔细观察这张图片（它可能是一张风景照、或者是一张小红书的旅游攻略截图）。请帮我提炼出这张图里涉及到的『目的地城市名称』以及所有能看出来的『具体景点名称』。最终请只回复我一句话，格式必须为：『我想去[城市名]玩，顺便去[景点1]、[景点2]』，不要有任何其他解释。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # 返回 VLM 从图片里提取出的纯文本旅游意图
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"视觉模态解析异常: {str(e)}")
        return ""