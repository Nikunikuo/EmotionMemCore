"""
構造化ログ設定モジュール
デバッグしやすい形式でログを出力
"""

import os
import sys
from typing import Any, Dict

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """構造化ログの初期設定"""
    
    # プロセッサーの設定
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    # 出力形式の選択
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # structlogの設定
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """ロガーインスタンスの取得"""
    return structlog.get_logger(name)


# デバッグ用のログデコレータ
def log_execution(func):
    """関数の実行をログに記録するデコレータ"""
    logger = get_logger(func.__module__)
    
    def wrapper(*args, **kwargs):
        logger.info(
            "function_called",
            function=func.__name__,
            args=args,
            kwargs=kwargs
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "function_completed",
                function=func.__name__,
                result_type=type(result).__name__
            )
            return result
        except Exception as e:
            logger.exception(
                "function_error",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
    
    return wrapper


# パフォーマンス計測用のコンテキストマネージャ
import time
from contextlib import contextmanager


@contextmanager
def log_performance(operation: str, logger: structlog.stdlib.BoundLogger, **extra_fields):
    """処理時間を計測してログに記録"""
    start_time = time.time()
    logger.info(f"{operation}_started", **extra_fields)
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{operation}_completed",
            duration_ms=round(duration_ms, 2),
            **extra_fields
        )