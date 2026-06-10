# backend/asr_engine.py
import os
from io import BytesIO
from openai import OpenAI

def transcribe_audio(audio_bytes: bytes) -> str:
    """调用阿里云百炼Paraformer 引擎进行语音转文字"""
    try:
        api_key = os.getenv("DASHSCOPE_API_KEY") 
        
        if not api_key:
            print("❌ 未检测到 DASHSCOPE_API_KEY 环境变量，请检查配置！")
            return ""

        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        audio_file = BytesIO(audio_bytes)
        audio_file.name = "user_voice.wav"
        
        # 调用阿里百炼的语音识别接口
        transcript = client.audio.transcriptions.create(
            model="paraformer-realtime-v1", 
            file=audio_file
        )
        
        return transcript.text.strip()
    except Exception as e:
        print(f"阿里云 ASR 识别发生工程异常: {str(e)}")
        return ""