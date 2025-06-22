"""
Embedding パッケージ
"""

from .openai_client import OpenAIEmbeddingClient
from .mock_client import MockEmbeddingClient

__all__ = [
    "OpenAIEmbeddingClient",
    "MockEmbeddingClient"
]