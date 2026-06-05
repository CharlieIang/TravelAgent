# backend/nlp_engine.py
import re

class NLPProcessor:
    def __init__(self):
        # 定义本地敏感词/违规词库
        self.sensitive_words = ["破坏", "作弊", "发票", "贷款", "赌博", "政治", "暴力", "买卖"]
        
        # 定义旅游口头禅/语气词停用词列表
        self.stopwords = ["那个", "呃", "啊", "请问", "麻烦", "帮我", "谢谢", "一下", "哈", "呀", "吧"]

    def clean_text(self, text: str) -> str:
        """先洗停用词，再用正则洗掉多余和重复的标点"""
        if not text:
            return ""
        
        # 先过滤掉无意义的语气口头禅
        for word in self.stopwords:
            text = text.replace(word, "")
            
        # 利用正则表达式，只保留中英文、数字和常用标点
        text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。？！、]", "", text)
        
        # 标点清洗去重
        text = re.sub(r"，+", "，", text)
        text = re.sub(r"。+", "。", text)
        
        # 掐头去尾
        text = text.strip("，。？！、")
            
        return text

    def check_safety(self, text: str) -> bool:
        """安全拦截"""
        for word in self.sensitive_words:
            if word in text:
                return False
        return True

    def extract_travel_slots(self, text: str) -> dict:
        """槽位/实体预提取"""
        days_match = re.search(r"(\d+)\s*(天|日)", text)
        days = int(days_match.group(1)) if days_match else None
        
        return {"extracted_days": days}
