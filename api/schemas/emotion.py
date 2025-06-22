"""
感情タグの定義
日本のAI Vtuber文脈でよく使われる感情を網羅
"""

from enum import Enum


class Emotion(str, Enum):
    """感情タグEnum"""
    
    # ポジティブな感情
    JOY = "喜び"
    HAPPINESS = "幸せ"
    EXCITEMENT = "興奮"
    LOVE = "愛情"
    GRATITUDE = "感謝"
    HOPE = "希望"
    PRIDE = "誇り"
    RELIEF = "安心"
    SATISFACTION = "満足"
    AMUSEMENT = "楽しさ"
    CONFIDENCE = "自信"
    INSPIRATION = "感動"
    
    # ネガティブな感情
    SADNESS = "悲しみ"
    ANGER = "怒り"
    FEAR = "恐れ"
    ANXIETY = "不安"
    FRUSTRATION = "苛立ち"
    DISAPPOINTMENT = "失望"
    LONELINESS = "孤独"
    GUILT = "罪悪感"
    SHAME = "恥"
    REGRET = "後悔"
    JEALOUSY = "嫉妬"
    
    # ニュートラルな感情
    SURPRISE = "驚き"
    CURIOSITY = "好奇心"
    CONFUSION = "困惑"
    NOSTALGIA = "懐かしさ"
    EMPATHY = "共感"
    SYMPATHY = "同情"
    ANTICIPATION = "期待"
    
    # AI Vtuber特有の感情
    MISCHIEF = "いたずら心"
    SHYNESS = "恥ずかしさ"
    DETERMINATION = "決意"
    REUNION = "再会"
    FAREWELL = "別れ"
    ENCOURAGEMENT = "励まし"
    SUPPORT = "支え"
    TRUST = "信頼"
    
    @classmethod
    def from_japanese(cls, value: str) -> 'Emotion':
        """日本語から感情タグを取得"""
        for emotion in cls:
            if emotion.value == value:
                return emotion
        raise ValueError(f"Unknown emotion: {value}")
    
    @classmethod
    def get_positive_emotions(cls) -> list['Emotion']:
        """ポジティブな感情のリストを取得"""
        return [
            cls.JOY, cls.HAPPINESS, cls.EXCITEMENT, cls.LOVE,
            cls.GRATITUDE, cls.HOPE, cls.PRIDE, cls.RELIEF,
            cls.SATISFACTION, cls.AMUSEMENT, cls.CONFIDENCE, cls.INSPIRATION
        ]
    
    @classmethod
    def get_negative_emotions(cls) -> list['Emotion']:
        """ネガティブな感情のリストを取得"""
        return [
            cls.SADNESS, cls.ANGER, cls.FEAR, cls.ANXIETY,
            cls.FRUSTRATION, cls.DISAPPOINTMENT, cls.LONELINESS,
            cls.GUILT, cls.SHAME, cls.REGRET, cls.JEALOUSY
        ]