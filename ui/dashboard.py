"""
EmotionMemCore 初心者向けWebダッシュボード
シンプルで直感的なWebインターフェース
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json
from datetime import datetime, timedelta
import asyncio

from api.dependencies import get_memory_service
from services.memory_service import MemoryService

# テンプレートとスタティックファイル設定
templates = Jinja2Templates(directory="ui/templates")

class DashboardService:
    """ダッシュボード用サービス"""
    
    def __init__(self):
        self.memory_service: Optional[MemoryService] = None
    
    async def initialize(self):
        """サービス初期化"""
        self.memory_service = await get_memory_service()
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """ダッシュボード統計情報取得"""
        try:
            if not self.memory_service:
                await self.initialize()
            
            # システム統計
            health_stats = await self.memory_service.health_check()
            
            # 仮の統計データ（実際の実装では real data を取得）
            stats = {
                "system": {
                    "status": health_stats.get("status", "unknown"),
                    "uptime": "24時間",
                    "version": "0.1.0"
                },
                "memories": {
                    "total_count": 150,
                    "today_count": 12,
                    "week_count": 78
                },
                "emotions": {
                    "top_emotions": [
                        {"name": "喜び", "count": 45, "percentage": 30},
                        {"name": "興奮", "count": 30, "percentage": 20},
                        {"name": "感謝", "count": 24, "percentage": 16},
                        {"name": "期待", "count": 18, "percentage": 12},
                        {"name": "安心", "count": 15, "percentage": 10}
                    ]
                },
                "performance": {
                    "avg_response_time": "0.2秒",
                    "success_rate": "99.5%",
                    "daily_requests": 245
                }
            }
            
            return stats
            
        except Exception as e:
            return {
                "error": str(e),
                "system": {"status": "error"},
                "memories": {"total_count": 0},
                "emotions": {"top_emotions": []},
                "performance": {}
            }
    
    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近の記憶一覧取得"""
        try:
            if not self.memory_service:
                await self.initialize()
            
            # 仮のデータ（実際の実装では real data を取得）
            memories = [
                {
                    "id": f"mem_{i}",
                    "summary": f"サンプル記憶 {i}: ユーザーとの楽しい会話",
                    "emotions": ["喜び", "楽しさ"],
                    "timestamp": (datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M"),
                    "user_id": f"user_{i % 3 + 1}"
                }
                for i in range(limit)
            ]
            
            return memories
            
        except Exception as e:
            return []
    
    async def search_memories_simple(
        self, 
        query: str, 
        user_id: str = "all",
        emotions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """簡単な記憶検索"""
        try:
            if not self.memory_service:
                await self.initialize()
            
            # 仮の検索結果
            results = [
                {
                    "id": "search_result_1",
                    "summary": f"『{query}』に関連する記憶: 楽しい会話の思い出",
                    "emotions": ["喜び", "楽しさ"],
                    "score": 0.95,
                    "timestamp": "2024-01-15 10:30",
                    "user_id": "user_1"
                },
                {
                    "id": "search_result_2", 
                    "summary": f"『{query}』について話した時の記憶",
                    "emotions": ["興味", "期待"],
                    "score": 0.87,
                    "timestamp": "2024-01-14 15:45",
                    "user_id": "user_2"
                }
            ]
            
            # 感情フィルター適用
            if emotions:
                results = [
                    r for r in results 
                    if any(emotion in r["emotions"] for emotion in emotions)
                ]
            
            return results
            
        except Exception as e:
            return []

# ダッシュボードサービスインスタンス
dashboard_service = DashboardService()

def create_dashboard_app() -> FastAPI:
    """ダッシュボードアプリケーション作成"""
    
    app = FastAPI(
        title="EmotionMemCore Dashboard",
        description="初心者向け簡単ダッシュボード",
        version="0.1.0"
    )
    
    # 静的ファイル設定
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
    
    @app.on_event("startup")
    async def startup_event():
        """起動時初期化"""
        await dashboard_service.initialize()
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home(request: Request):
        """ダッシュボードホーム"""
        stats = await dashboard_service.get_dashboard_stats()
        recent_memories = await dashboard_service.get_recent_memories(5)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats,
            "recent_memories": recent_memories,
            "page_title": "EmotionMemCore ダッシュボード"
        })
    
    @app.get("/welcome", response_class=HTMLResponse)
    async def welcome_page(request: Request):
        """初回起動ウェルカムページ"""
        return templates.TemplateResponse("welcome.html", {
            "request": request,
            "page_title": "EmotionMemCore へようこそ"
        })
    
    @app.get("/memories", response_class=HTMLResponse)
    async def memories_page(request: Request):
        """記憶管理ページ"""
        recent_memories = await dashboard_service.get_recent_memories(20)
        
        return templates.TemplateResponse("memories.html", {
            "request": request,
            "memories": recent_memories,
            "page_title": "記憶管理"
        })
    
    @app.get("/search", response_class=HTMLResponse)
    async def search_page(request: Request):
        """記憶検索ページ"""
        return templates.TemplateResponse("search.html", {
            "request": request,
            "page_title": "記憶検索",
            "emotions": [
                "喜び", "幸せ", "興奮", "愛情", "感謝", "希望", "誇り", "安心",
                "悲しみ", "怒り", "恐れ", "不安", "苛立ち", "失望", "孤独",
                "驚き", "好奇心", "困惑", "懐かしさ", "共感", "同情", "期待"
            ]
        })
    
    @app.post("/api/search")
    async def api_search_memories(
        query: str = Form(...),
        user_id: str = Form("all"),
        emotions: str = Form("")
    ):
        """記憶検索API"""
        try:
            emotion_list = [e.strip() for e in emotions.split(",") if e.strip()] if emotions else []
            
            results = await dashboard_service.search_memories_simple(
                query=query,
                user_id=user_id,
                emotions=emotion_list
            )
            
            return JSONResponse({
                "success": True,
                "results": results,
                "total": len(results)
            })
            
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e),
                "results": []
            }, status_code=500)
    
    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        """設定ページ"""
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "page_title": "設定",
            "current_settings": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug_mode": os.getenv("DEBUG_MODE", "false"),
                "llm_mock_mode": os.getenv("LLM_MOCK_MODE", "false"),
                "auth_enabled": os.getenv("AUTH_ENABLED", "false"),
                "rate_limit_enabled": os.getenv("RATE_LIMIT_ENABLED", "false")
            }
        })
    
    @app.get("/api/stats")
    async def api_get_stats():
        """統計情報API"""
        try:
            stats = await dashboard_service.get_dashboard_stats()
            return JSONResponse(stats)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
    
    @app.get("/api/memories")
    async def api_get_memories(limit: int = 10):
        """記憶一覧API"""
        try:
            memories = await dashboard_service.get_recent_memories(limit)
            return JSONResponse({
                "success": True,
                "memories": memories,
                "total": len(memories)
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e),
                "memories": []
            }, status_code=500)
    
    @app.get("/visualization", response_class=HTMLResponse)
    async def visualization_page(request: Request):
        """記憶可視化ページ"""
        return templates.TemplateResponse("visualization.html", {
            "request": request,
            "page_title": "記憶可視化ツール"
        })
    
    @app.get("/logs", response_class=HTMLResponse)
    async def logs_page(request: Request):
        """ログ表示ページ"""
        return templates.TemplateResponse("logs.html", {
            "request": request,
            "page_title": "リアルタイムログ"
        })
    
    @app.get("/test", response_class=HTMLResponse)
    async def test_page(request: Request):
        """機能テストページ"""
        return templates.TemplateResponse("test.html", {
            "request": request,
            "page_title": "機能テスト"
        })
    
    @app.post("/api/test-save")
    async def api_test_save(
        user_message: str = Form(...),
        ai_message: str = Form(...),
        user_id: str = Form("test_user")
    ):
        """テスト記憶保存"""
        try:
            if not dashboard_service.memory_service:
                await dashboard_service.initialize()
            
            result = await dashboard_service.memory_service.save_memory(
                user_message=user_message,
                ai_message=ai_message,
                user_id=user_id,
                session_id=f"dashboard_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            return JSONResponse({
                "success": True,
                "message": "記憶保存が成功しました！",
                "result": {
                    "memory_id": result.get("memory_id"),
                    "summary": result.get("summary"),
                    "emotions": result.get("emotions", [])
                }
            })
            
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": f"記憶保存に失敗しました: {str(e)}",
                "result": None
            }, status_code=500)
    
    return app

# ダッシュボードアプリケーション
dashboard_app = create_dashboard_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8080)