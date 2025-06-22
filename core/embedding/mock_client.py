"""
モック Embedding クライアント - 開発・テスト用
"""

import random
import asyncio
from typing import List

from infrastructure.config.logger import get_logger


class MockEmbeddingClient:
    """モック Embedding クライアント - OpenAI API Key不要"""
    
    def __init__(self, model: str = "mock-embedding"):
        self.logger = get_logger(__name__)
        self.model = model
        self.dimension = 1536  # OpenAI text-embedding-3-small互換
        
        self.logger.info(
            "mock_embedding_initialized",
            model=model,
            dimension=self.dimension
        )
    
    async def get_embedding(self, text: str) -> List[float]:
        """モック埋め込みベクトルを生成"""
        # 人工的な遅延（リアルなAPI感）
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # テキストの長さベースでシード設定（一貫性のため）
        seed = hash(text) % (2**31)
        random.seed(seed)
        
        # 正規化されたランダムベクトル生成
        vector = [random.gauss(0, 1) for _ in range(self.dimension)]
        
        # L2正規化
        magnitude = sum(x**2 for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        
        self.logger.debug(
            "mock_embedding_generated",
            text_length=len(text),
            vector_dimension=len(vector)
        )
        
        return vector
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """複数テキストの埋め込み取得"""
        return [await self.get_embedding(text) for text in texts]
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        return True