"""
EmotionMemCore 初心者向けメッセージ定義
YouTube見るだけ層でも分かりやすいエラーメッセージ
"""

from typing import Dict, Any

class UserFriendlyMessages:
    """初心者向けの分かりやすいメッセージ"""
    
    # システム起動関連
    STARTUP_MESSAGES = {
        "starting": "🚀 EmotionMemCore を起動しています...",
        "started": "✨ 起動完了！ブラウザでダッシュボードをお楽しみください",
        "failed": "❌ 起動に失敗しました。以下をお試しください：\n1. 他のアプリを閉じてください\n2. パソコンを再起動してください\n3. 管理者として実行してください"
    }
    
    # API関連エラー
    API_ERRORS = {
        "connection_failed": {
            "title": "🔌 接続エラー",
            "message": "APIサーバーに接続できません",
            "solutions": [
                "メインAPIサーバーが起動しているか確認してください",
                "「start_emotionmemcore.bat」をダブルクリックで起動してください",
                "ファイアウォールでブロックされていないか確認してください",
                "ポート8000, 8080が他のアプリで使用されていないか確認してください"
            ]
        },
        "api_key_missing": {
            "title": "🔑 APIキーが設定されていません",
            "message": "本格的な機能を使うにはAPIキーが必要です",
            "solutions": [
                "今すぐ試したい場合：「設定」→「モックモード」を有効にしてください",
                "本格利用の場合：OpenAIのAPIキーを取得してください",
                "詳細は「設定ガイド」をご覧ください"
            ]
        },
        "rate_limit": {
            "title": "⏰ アクセス制限",
            "message": "短時間で多くのリクエストが送信されました",
            "solutions": [
                "1分ほどお待ちください",
                "自動化プログラムを一時停止してください",
                "設定で制限を緩和できます（上級者向け）"
            ]
        }
    }
    
    # データベース関連エラー
    DATABASE_ERRORS = {
        "save_failed": {
            "title": "💾 保存エラー",
            "message": "記憶の保存に失敗しました",
            "solutions": [
                "ディスクの空き容量を確認してください",
                "アンチウイルスソフトでブロックされていないか確認してください",
                "フォルダの権限を確認してください",
                "パソコンを再起動してください"
            ]
        },
        "search_failed": {
            "title": "🔍 検索エラー",
            "message": "記憶の検索に失敗しました",
            "solutions": [
                "保存された記憶があるか確認してください",
                "検索キーワードを変更してみてください",
                "「機能テスト」でサンプルデータを作成してください"
            ]
        }
    }
    
    # LLM関連エラー
    LLM_ERRORS = {
        "claude_error": {
            "title": "🤖 Claude AI エラー",
            "message": "Claude AIとの通信で問題が発生しました",
            "solutions": [
                "インターネット接続を確認してください",
                "Claude APIキーが正しいか確認してください",
                "少し時間を置いてから再試行してください",
                "モックモードで動作確認してください"
            ]
        },
        "openai_error": {
            "title": "🧠 OpenAI エラー",
            "message": "OpenAI との通信で問題が発生しました",
            "solutions": [
                "インターネット接続を確認してください",
                "OpenAI APIキーが正しいか確認してください",
                "APIキーの残高を確認してください",
                "少し時間を置いてから再試行してください"
            ]
        }
    }
    
    # 成功メッセージ
    SUCCESS_MESSAGES = {
        "memory_saved": "✅ 記憶を保存しました！感情分析も完了です",
        "memory_searched": "🔍 記憶を検索しました！関連する記憶が見つかりました",
        "test_completed": "🎉 テストが正常に完了しました！",
        "settings_saved": "⚙️ 設定を保存しました。再起動後に有効になります"
    }
    
    # 初心者向けヒント
    BEGINNER_TIPS = {
        "first_visit": {
            "title": "🎉 EmotionMemCore へようこそ！",
            "message": "初めてご利用いただきありがとうございます",
            "tips": [
                "まずは「機能テスト」でシステムを体験してみてください",
                "「記憶検索」で自然な日本語で検索できます",
                "「記憶可視化」で美しいグラフを楽しめます",
                "困ったときは「設定ガイド」をご覧ください"
            ]
        },
        "no_memories": {
            "title": "💭 記憶がまだありません",
            "message": "記憶を作成して EmotionMemCore を体験しましょう",
            "tips": [
                "「機能テスト」でサンプル記憶を作成できます",
                "「ユーザーメッセージ」と「AIメッセージ」を入力して保存してみてください",
                "自動で感情分析が行われ、後で検索できるようになります"
            ]
        }
    }
    
    # トラブルシューティング
    TROUBLESHOOTING = {
        "common_issues": {
            "browser_not_opening": {
                "problem": "ブラウザが自動で開かない",
                "solution": "手動で http://localhost:8080 にアクセスしてください"
            },
            "slow_performance": {
                "problem": "動作が重い・遅い",
                "solution": "他のアプリを閉じるか、パソコンを再起動してください"
            },
            "windows_defender": {
                "problem": "Windows Defenderで警告が出る",
                "solution": "「詳細情報」→「実行」で起動できます（安全なソフトです）"
            },
            "port_occupied": {
                "problem": "ポートが使用中のエラー",
                "solution": "他のアプリを終了するか、パソコンを再起動してください"
            }
        }
    }

    @staticmethod
    def get_error_message(error_type: str, error_key: str) -> Dict[str, Any]:
        """エラータイプとキーから分かりやすいメッセージを取得"""
        error_messages = {
            "api": UserFriendlyMessages.API_ERRORS,
            "database": UserFriendlyMessages.DATABASE_ERRORS,
            "llm": UserFriendlyMessages.LLM_ERRORS
        }
        
        if error_type in error_messages and error_key in error_messages[error_type]:
            return error_messages[error_type][error_key]
        
        # デフォルトエラーメッセージ
        return {
            "title": "❓ 不明なエラー",
            "message": "予期しない問題が発生しました",
            "solutions": [
                "画面を更新してください（F5キー）",
                "アプリを再起動してください",
                "パソコンを再起動してください",
                "問題が続く場合はGitHubでご報告ください"
            ]
        }
    
    @staticmethod
    def format_error_for_display(error_dict: Dict[str, Any]) -> str:
        """エラー情報を表示用にフォーマット"""
        title = error_dict.get("title", "エラー")
        message = error_dict.get("message", "問題が発生しました")
        solutions = error_dict.get("solutions", [])
        
        formatted = f"{title}\n\n{message}\n\n"
        
        if solutions:
            formatted += "💡 解決方法:\n"
            for i, solution in enumerate(solutions, 1):
                formatted += f"{i}. {solution}\n"
        
        return formatted

# 便利関数
def get_user_friendly_error(error_type: str, error_key: str) -> str:
    """初心者向けエラーメッセージを取得"""
    error_dict = UserFriendlyMessages.get_error_message(error_type, error_key)
    return UserFriendlyMessages.format_error_for_display(error_dict)

def get_success_message(key: str) -> str:
    """成功メッセージを取得"""
    return UserFriendlyMessages.SUCCESS_MESSAGES.get(key, "✅ 操作が完了しました")

def get_beginner_tip(key: str) -> Dict[str, Any]:
    """初心者向けヒントを取得"""
    return UserFriendlyMessages.BEGINNER_TIPS.get(key, {
        "title": "💡 ヒント",
        "message": "不明な点があれば設定ガイドをご覧ください",
        "tips": []
    })