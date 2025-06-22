"""
プロンプトテンプレート管理
"""

from typing import List, Dict, Optional


class PromptTemplate:
    """プロンプトテンプレート管理クラス"""
    
    def __init__(self):
        self.memory_prompt_template = """あなたはAI Vtuberの記憶システムです。以下の会話を分析して、要約と感情タグを抽出してください。

# 会話内容
ユーザー: {user_message}
AI: {ai_message}

{context_section}

# 出力形式
以下の形式で出力してください：

要約: [この会話の内容を50文字以内で要約]
感情: [検出された感情を日本語で列挙（例：喜び、不安、感謝）]

# 感情タグ一覧
以下の感情タグから適切なものを選んでください（複数選択可、最大5個）：

【ポジティブ感情】
喜び、幸せ、興奮、愛情、感謝、希望、誇り、安心、満足、楽しさ、自信、感動

【ネガティブ感情】
悲しみ、怒り、恐れ、不安、苛立ち、失望、孤独、罪悪感、恥、後悔、嫉妬

【ニュートラル感情】
驚き、好奇心、困惑、懐かしさ、共感、同情、期待

【AI Vtuber特有感情】
いたずら心、恥ずかしさ、決意、再会、別れ、励まし、支え、信頼

# 注意事項
- 要約は簡潔に、感情は正確に抽出してください
- 複数の感情が混在している場合は、主要なものを選んでください
- 文脈を考慮して適切な感情を判断してください"""

        self.search_prompt_template = """検索クエリに基づいて、記憶データベースを検索するためのキーワードを生成してください。

検索クエリ: {query}

以下の観点でキーワードを抽出してください：
1. 感情に関連するキーワード
2. 状況や場面に関連するキーワード  
3. 人物や関係性に関連するキーワード

抽出したキーワード: """

    def build_memory_prompt(
        self, 
        user_message: str, 
        ai_message: str, 
        context_window: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """記憶処理用プロンプトを構築"""
        
        # 文脈情報の組み立て
        context_section = ""
        if context_window:
            context_section = "# 会話の文脈\n"
            for i, ctx in enumerate(context_window[-3:]):  # 直近3件まで
                speaker = "ユーザー" if ctx.get("role") == "user" else "AI"
                context_section += f"前の会話{i+1}: {speaker}: {ctx.get('content', '')}\n"
            context_section += "\n"
        
        return self.memory_prompt_template.format(
            user_message=user_message,
            ai_message=ai_message,
            context_section=context_section
        )
    
    def build_search_prompt(self, query: str) -> str:
        """検索用プロンプトを構築"""
        return self.search_prompt_template.format(query=query)
    
    def get_system_prompt(self) -> str:
        """システムプロンプトを取得"""
        return """あなたはAI Vtuberの感情記憶システムです。
ユーザーとAI Vtuberの会話を分析し、感情的な文脈を理解して記憶として保存することが役目です。
日本語で自然な表現を心がけ、AI Vtuberらしい感情表現を適切に捉えてください。"""
    
    def customize_prompt(
        self, 
        template_type: str, 
        custom_emotions: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> str:
        """プロンプトのカスタマイズ"""
        
        if template_type == "memory":
            base_template = self.memory_prompt_template
            
            # カスタム感情タグの追加
            if custom_emotions:
                emotion_section = "\n【カスタム感情】\n" + "、".join(custom_emotions)
                base_template = base_template.replace(
                    "# 注意事項", 
                    emotion_section + "\n\n# 注意事項"
                )
            
            # カスタム指示の追加
            if custom_instructions:
                base_template += f"\n\n# 追加指示\n{custom_instructions}"
            
            return base_template
        
        return self.memory_prompt_template
    
    def get_validation_prompt(self, summary: str, emotions: List[str]) -> str:
        """要約・感情の妥当性チェック用プロンプト"""
        return f"""以下の要約と感情タグが適切かチェックしてください：

要約: {summary}
感情: {', '.join(emotions)}

チェック項目：
1. 要約は内容を適切に表現しているか
2. 感情タグは会話内容と一致しているか
3. 冗長な表現や誤解を招く表現はないか

判定: 適切/要修正
修正提案: [必要に応じて修正案を提示]"""