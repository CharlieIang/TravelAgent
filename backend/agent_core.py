# backend/agent_core.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def get_agent_executor():
    """工厂函数：初始化并返回配置好的 AgentExecutor"""
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        return None

    # 初始化大模型大脑
    llm = ChatOpenAI(
        model="deepseek-chat",                      
        openai_api_key=DEEPSEEK_API_KEY,           
        openai_api_base="https://api.deepseek.com", 
        temperature=0.0                             
    )

    # 【工具 1】：天气工具
    @tool
    def get_current_weather(city: str) -> str:
        """获取指定城市当前的天气、温度状况及出行穿衣、带伞建议。"""
        city_data = {
            "北京": "晴转多云, 22°C, 适合户外出行",
            "成都": "阴天有小雨, 19°C, 建议携带雨伞, 局部有积水",
            "厦门": "大晴天, 28°C, 体感较热, 注意防晒"
        }
        return city_data.get(city, f"{city}当前天气晴，15°C，出行请注意保暖。")

    # 【工具 2】：景点地图工具
    @tool
    def get_places_and_routes(city: str) -> str:
        """查询指定城市的核心旅游景点、推荐游玩时长、景点间的距离和交通耗时信息。"""
        scenic_data = {
            "成都": "1. 大熊猫繁育研究基地：建议游玩4小时。2. 宽窄巷子：建议游玩2小时。3. 武侯祠/锦里：建议游玩3小时。交通：熊猫基地离市区15公里，打车40分钟。",
            "北京": "1. 故宫博物院：建议游玩1天。2. 颐和园：建议游玩4小时。3. 南锣鼓巷：建议游玩2小时。交通：建议地铁4号线直达。",
            "厦门": "1. 鼓浪屿：建议游玩1天。2. 中山路步行街：建议游玩3小时。3. 环岛路：建议骑行2小时。"
        }
        return scenic_data.get(city, f"抱歉，暂未收录{city}的精细化地图景点数据。")

    tools = [get_current_weather, get_places_and_routes]

    # 组装提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个极其专业的智能旅游行程规划助手。\n"
            "当用户让你规划某地旅游行程时，你必须按以下步骤思考和行动：\n"
            "1. 使用 get_current_weather 工具查询目的地的天气状况。\n"
            "2. 使用 get_places_and_routes 工具查询目的地的热门景点及交通路线耗时。\n"
            "3. 严谨地结合这两种工具返回的真实数据，生成一份全套旅游行程方案。"
        )),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)