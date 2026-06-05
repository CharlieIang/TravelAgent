# backend/agent_core.py
import os
import requests
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

AMAP_KEY = os.getenv("AMAP_KEY")

def get_agent_executor():
    """初始化并返回配置好的API AgentExecutor"""
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        return None

    llm = ChatOpenAI(
        model="deepseek-chat",                      
        openai_api_key=DEEPSEEK_API_KEY,           
        openai_api_base="https://api.deepseek.com", 
        temperature=0.0                             
    )

    @tool
    def get_current_weather(city: str) -> str:
        """获取指定城市当前的天气预报、温度状况及出行穿衣、带伞建议。"""
        try:
            # 1. 查城市编码
            geo_url = f"https://restapi.amap.com/v3/config/district?keywords={city}&key={AMAP_KEY}"
            geo_res = requests.get(geo_url, timeout=5).json()
            adcode = geo_res["districts"][0]["adcode"]
            
            # 2. 查天气预报
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=all"
            weather_res = requests.get(weather_url, timeout=5).json()
            
            if weather_res["status"] == "1" and weather_res["forecasts"]:
                cast = weather_res["forecasts"][0]["casts"][0]
                return (
                    f"【真实高德天气数据】{city}今日天气状况：白天 {cast['dayweather']}，"
                    f"晚上 {cast['nightweather']}；白天最高气温 {cast['daytemp']}°C，"
                    f"夜间最低气温 {cast['nighttemp']}°C。请根据此天气给用户合理的出行带伞或防晒建议。"
                )
        except Exception as e:
            return f"暂时无法联网获取{city}的实时天气（原因:{str(e)}），请基于通用常识为用户规划。"

    @tool
    def get_places_and_routes(city: str) -> str:
        """查询指定城市的热门旅游景点名称和详细地址信息。"""
        try:
            places_url = f"https://restapi.amap.com/v3/place/text?keywords=景点&city={city}&key={AMAP_KEY}&output=json"
            res = requests.get(places_url, timeout=5).json()
            
            if res.get("status") == "1":
                pois = res.get("pois", [])
                if not pois:
                    return f"已联网，但未查到{city}的精细景点数据。"
                
                cleaned_spots = []
                # for poi in pois[:4]:
                for poi in pois:
                    name = poi.get("name")
                    address = poi.get("address")
                    
                    if name:
                        # 把容易破坏 JSON 结构的所有双引号、单引号、中括号全部删去或替换
                        name = name.replace('"', '“').replace("'", "‘").replace("[", "【").replace("]", "】")
                        if address and isinstance(address, str):
                            address = address.replace('"', '“').replace("'", "‘").replace("[", "【").replace("]", "】")
                        else:
                            address = '市中心附近'
                            
                        cleaned_spots.append(f"景点: {name} (地址: {address})")
                
                return f"【真实高德地图数据】{city}的核心热门景点如下：\n" + "\n".join(cleaned_spots)
            else:
                return f"未能联网查到{city}的精细景点数据。"
        except Exception as e:
            return f"暂时无法联网获取{city}的地图数据（原因:{str(e)}）。"

    tools = [get_current_weather, get_places_and_routes]

    json_format_instruction = (
        "你是一个极其专业的智能旅游行程规划助手。\n"
        "当用户让你规划某地旅游行程时，你必须按以下步骤思考和行动：\n"
        "1. 使用 get_current_weather 工具查询目的地的天气状况。\n"
        "2. 使用 get_places_and_routes 工具查询目的地的热门景点及交通路线耗时。\n"
        "3. 严谨地结合这两种工具返回的真实数据，并在【最终回答】时，必须且只能输出一个符合以下 JSON 格式的字符串，绝不要带有任何 JSON 块之外的闲聊或解释性文本：\n"
        "{{\n"
        '  "destination": "目的地城市名称",\n'
        '  "weather_tips": "结合工具返回天气给出的精细穿衣和带伞防晒避坑建议",\n'
        '  "itinerary": [\n'
        "    {{\n"
        '      "day": "Day 1",\n'
        '      "morning": "上午具体的景点行程编排与交通建议",\n'
        '      "afternoon": "下午具体的景点行程编排与交通建议",\n'
        '      "evening": "晚上具体的景点行程编排与餐饮夜景建议"\n'
        "    }},\n"
        "    {{\n"
        '      "day": "Day 2",\n'
        '      "morning": "...",\n'
        '      "afternoon": "...",\n'
        '      "evening": "..."\n'
        "    }}\n"
        "  ]\n"
        "}}\n"
        "注意：如果用户只是进行日常礼貌问候，你不需要调用工具，也不需要输出 JSON，直接自然语言回复即可。"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", json_format_instruction),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
