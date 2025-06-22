"""
OpenAI Embedding クライアント実装
"""

import os
import time
from typing import List, Optional

from openai import AsyncOpenAI

from infrastructure.config.logger import get_logger


class OpenAIEmbeddingClient:
    """OpenAI Embedding クライアント"""
    
    def __init__(self, model: str = "text-embedding-3-small"):
        self.logger = get_logger(__name__)
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # モデル情報
        self.model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        self.dimension = self.model_dimensions.get(model, 1536)
        
        self.logger.info(
            "openai_embedding_initialized",
            model=model,
            dimension=self.dimension
        )
    
    async def get_embedding(self, text: str) -> List[float]:
        """テキストのベクトル埋め込みを取得"""
        start_time = time.time()
        
        try:
            # テキストの前処理
            text = text.replace("\n", " ").strip()
            
            if not text:
                raise ValueError("Empty text provided for embedding")
            
            # OpenAI API呼び出し
            response = await self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                "embedding_generated",
                model=self.model,
                text_length=len(text),
                dimension=len(embedding),
                processing_time_ms=round(processing_time, 2)
            )
            
            return embedding
            
        except Exception as e:
            self.logger.error(
                "embedding_generation_failed",
                model=self.model,
                text_length=len(text) if text else 0,
                error=str(e)
            )
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """複数テキストのベクトル埋め込みを一括取得"""
        start_time = time.time()
        
        try:
            # テキストの前処理
            processed_texts = []
            for text in texts:
                processed_text = text.replace("\n", " ").strip()
                if processed_text:
                    processed_texts.append(processed_text)
            
            if not processed_texts:
                raise ValueError("No valid texts provided for embedding")
            
            # OpenAI API呼び出し（バッチ）
            response = await self.client.embeddings.create(
                input=processed_texts,
                model=self.model
            )
            
            embeddings = [data.embedding for data in response.data]
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                "batch_embeddings_generated",
                model=self.model,
                batch_size=len(processed_texts),
                total_chars=sum(len(t) for t in processed_texts),
                processing_time_ms=round(processing_time, 2)
            )
            
            return embeddings
            
        except Exception as e:
            self.logger.error(
                "batch_embedding_generation_failed",
                model=self.model,
                batch_size=len(texts),
                error=str(e)
            )
            raise
    
    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """コサイン類似度を計算"""
        try:
            import numpy as np
            
            # ベクトルの正規化
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # コサイン類似度
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error("similarity_calculation_failed", error=str(e))
            return 0.0
    
    async def health_check(self) -> bool:
        """Embedding APIのヘルスチェック"""
        try:
            # 簡単なテスト
            test_embedding = await self.get_embedding("health check test")
            
            # ベクトルの次元確認
            if len(test_embedding) == self.dimension:
                self.logger.info("openai_embedding_health_check_passed")
                return True
            else:
                self.logger.error(
                    "openai_embedding_dimension_mismatch",
                    expected=self.dimension,
                    actual=len(test_embedding)
                )
                return False
                
        except Exception as e:
            self.logger.error("openai_embedding_health_check_failed", error=str(e))
            return False
    
    def get_model_info(self) -> dict:
        """モデル情報を取得"""
        return {
            "model": self.model,
            "dimension": self.dimension,
            "provider": "openai"
        }