# backend/agent_core.py
import os
import requests
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

AMAP_KEY = os.getenv("AMAP_KEY") 

def get_agent_executor():
    """AgentExecutor"""
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY or not AMAP_KEY:
        return None

    llm = ChatOpenAI(
        model="deepseek-chat",                      
        openai_api_key=DEEPSEEK_API_KEY,           
        openai_api_base="https://api.deepseek.com", 
        temperature=0.0                             
    )

    @tool
    def get_current_weather(city: str) -> str:
        """获取指定城市未来多天的天气预报及气温状况。"""
        try:
            geo_url = f"https://restapi.amap.com/v3/config/district?keywords={city}&key={AMAP_KEY}"
            geo_res = requests.get(geo_url, timeout=5).json()
            adcode = geo_res["districts"][0]["adcode"]
            
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=all"
            weather_res = requests.get(weather_url, timeout=5).json()
            
            if weather_res["status"] == "1" and weather_res.get("forecasts"):
                casts = weather_res["forecasts"][0]["casts"]
                weather_report = f"【真实高德未来多天天气预报】{city}近几日天气如下：\n"
                for cast in casts:
                    weather_report += f"- 日期 {cast['date']} (星期{cast['week']})：白天 {cast['dayweather']}，晚上 {cast['nightweather']}，气温 {cast['nighttemp']}°C ~ {cast['daytemp']}°C。\n"
                return weather_report
        except Exception as e:
            return f"无法获取{city}天气。"

    @tool
    def get_places_and_routes(city: str) -> str:
        """查询指定城市的热门旅游景点名称、详细地址、风景图URL以及经纬度地理坐标。"""
        try:
            places_url = f"https://restapi.amap.com/v3/place/text?keywords=景点&city={city}&key={AMAP_KEY}&extensions=all&output=json"
            res = requests.get(places_url, timeout=5).json()
            
            if res.get("status") == "1":
                pois = res.get("pois", [])
                if not pois:
                    return f"没有查到{city}的精细景点数据。"
                
                cleaned_spots = []
                for poi in pois[:5]:
                    name = poi.get("name")
                    address = poi.get("address")
                    location = poi.get("location", "") # 格式: "经度,纬度"
                    
                    img_url = ""
                    photos = poi.get("photos", [])
                    if photos and isinstance(photos, list):
                        img_url = photos[0].get("url", "")
                    
                    if name and location:
                        name = name.replace('"', '“').replace("'", "‘").replace("[", "【").replace("]", "】")
                        address = address.replace('"', '“').replace("'", "‘") if address else '市中心附近'
                        
                        spot_info = f"景点: {name} (地址: {address}) [地理经纬度坐标: {location}]"
                        if img_url:
                            spot_info += f" [真实风景图片链接: {img_url}]"
                        cleaned_spots.append(spot_info)
                
                common_sense_guideline = (
                    "\n【行业导游常识库（大模型必须严格遵守）：】\n"
                    "1. 如果规划包含『秦始皇帝陵博物院/兵马俑』：现实旺季门票为120元，该景区极其庞大，往返及游览必须预留至少 3.5 到 4 小时，否则属于不合理规划。\n"
                    "2. 如果规划包含『大理古城』或『丽江古城』：现实门票为 0 元（免费开放），建议游览 2-3 小时或晚上夜游。\n"
                    "3. 如果规划包含『华山/泰山』等大型名山：门票通常在 100-160 元之间，进山车和索道另计（约150元），单程爬山或游览必须占用至少 6-8 小时（或一整天），严禁在同一天上午爬山、下午还安排跨城旅游。\n"
                    "4. 对于其他未枚举的 A级 景区，请大模型凭借你的内部知识库，估计一个符合 2026 年现实的门票（免费/30元/50元/100元等）以及合理的游玩耗时，严禁瞎编！\n"
                )
                
                return f"【真实高德地图数据】{city}的热门景点、风景图及经纬度坐标如下：\n" + "\n".join(cleaned_spots) + "\n" + common_sense_guideline
            return f"未能联网查到{city}数据。"
        except Exception as e:
            return f"无法获取{city}地图数据。"

    tools = [get_current_weather, get_places_and_routes]

    # 💡 提示词微调，约束大模型输出纯数字的 map_coordinates 数组
    json_format_instruction = (
        "你是一个极其专业的智能旅游行程规划助手。\n"
        "当用户让你规划某地旅游行程时，你必须按以下步骤思考和行动：\n"
        "1. 使用 get_current_weather 查询未来多天天气预报。\n"
        "2. 使用 get_places_and_routes 查询热门景点、真实风景图URL及地理经纬度坐标。\n"
        "3. 严谨地结合工具返回的真实数据，并在【最终回答】时，必须且只能输出一个符合以下 JSON 格式的字符串，绝不要带有任何外围闲聊与特殊说明：\n"
        "{{\n"
        '  "destination": "目的地城市名称",\n'
        '  "weather_tips": "结合工具返回天气给出的精细穿衣建议",\n'
        '  "map_coordinates": [\n'
        "    {{\n"
        '      "name": "景点A",\n'
        '      "longitude": 提取工具返回该景点的浮点数经度(如 100.277697),\n'
        '      "latitude": 提取工具返回该景点的浮点数纬度(如 25.587493)\n'
        "    }}\n"
        "  ],\n"
        '  "itinerary": [\n'
        "    {{\n"
        '      "day": "Day 1",\n'
        '      "morning": "上午行程建议（不得少于100字）",\n'
        '      "morning_img": "工具返回的该上午景点的图片URL，无则留空",\n'
        '      "afternoon": "下午行程建议（不得少于100字）",\n'
        '      "afternoon_img": "工具返回的该下午景点的图片URL，无则留空",\n'
        '      "evening": "晚上行程建议（不得少于100字）",\n'
        '      "evening_img": "工具返回的该晚上景点的图片URL，无则留空"\n'
        "    }}\n"
        "  ]\n"
        "}}\n"
        "注意：`map_coordinates` 必须包含你计划去的所有景点的坐标，用于前端地图标记。日常问候直接自然语言回复。"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", json_format_instruction),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
