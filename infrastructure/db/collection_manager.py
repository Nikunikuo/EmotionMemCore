"""
コレクション管理ユーティリティ
ChromaDBコレクションの生成・削除・バックアップ機能
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from infrastructure.config.logger import get_logger


class CollectionManager:
    """コレクション管理クラス"""
    
    def __init__(self, chroma_client, persist_directory: str = "./chroma_db"):
        self.logger = get_logger(__name__)
        self.chroma_client = chroma_client
        self.persist_directory = persist_directory
        self.backup_directory = os.path.join(persist_directory, "backups")
        
        # バックアップディレクトリ作成
        Path(self.backup_directory).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "collection_manager_initialized",
            persist_directory=persist_directory,
            backup_directory=self.backup_directory
        )
    
    def create_collection(
        self, 
        name: str, 
        description: str = "感情付き記憶データベース",
        force_recreate: bool = False
    ) -> bool:
        """コレクション作成"""
        try:
            # 既存チェック
            if not force_recreate:
                try:
                    existing = self.chroma_client.client.get_collection(name)
                    if existing:
                        self.logger.info(
                            "collection_already_exists",
                            collection_name=name,
                            count=existing.count()
                        )
                        return True
                except Exception:
                    # コレクションが存在しない場合は続行
                    pass
            
            # 強制再作成の場合は削除
            if force_recreate:
                self.delete_collection(name, backup_before_delete=True)
            
            # メタデータ準備
            metadata = {
                "description": description,
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "type": "emotion_memory"
            }
            
            # コレクション作成
            collection = self.chroma_client.get_or_create_collection(
                name=name,
                metadata=metadata
            )
            
            self.logger.info(
                "collection_created",
                collection_name=name,
                description=description,
                force_recreate=force_recreate
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "collection_creation_failed",
                collection_name=name,
                error=str(e)
            )
            return False
    
    def delete_collection(
        self, 
        name: str, 
        backup_before_delete: bool = True
    ) -> bool:
        """コレクション削除"""
        try:
            # バックアップ作成
            if backup_before_delete:
                backup_success = self.backup_collection(name)
                if not backup_success:
                    self.logger.warning(
                        "collection_backup_failed_before_delete",
                        collection_name=name
                    )
            
            # コレクション削除
            self.chroma_client.client.delete_collection(name)
            
            self.logger.info(
                "collection_deleted",
                collection_name=name,
                backup_created=backup_before_delete
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "collection_deletion_failed",
                collection_name=name,
                error=str(e)
            )
            return False
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """コレクション一覧取得"""
        try:
            collections = self.chroma_client.client.list_collections()
            
            collection_info = []
            for collection in collections:
                try:
                    stats = self.chroma_client.get_collection_stats(collection)
                    info = {
                        "name": collection.name,
                        "count": collection.count(),
                        "metadata": collection.metadata,
                        "stats": stats
                    }
                    collection_info.append(info)
                except Exception as e:
                    self.logger.warning(
                        "collection_info_partial_failure",
                        collection_name=collection.name,
                        error=str(e)
                    )
                    # 基本情報のみ追加
                    collection_info.append({
                        "name": collection.name,
                        "count": collection.count(),
                        "metadata": collection.metadata,
                        "stats": {"total_memories": collection.count()}
                    })
            
            self.logger.info(
                "collections_listed",
                collection_count=len(collection_info)
            )
            
            return collection_info
            
        except Exception as e:
            self.logger.error("collection_listing_failed", error=str(e))
            return []
    
    def backup_collection(self, name: str) -> bool:
        """コレクションバックアップ作成"""
        try:
            # バックアップディレクトリ作成
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                self.backup_directory, 
                f"{name}_backup_{timestamp}"
            )
            Path(backup_path).mkdir(parents=True, exist_ok=True)
            
            # コレクション取得
            collection = self.chroma_client.client.get_collection(name)
            
            # 全データエクスポート
            all_data = collection.get(include=["documents", "metadatas", "embeddings"])
            
            # バックアップデータ構造
            backup_data = {
                "collection_name": name,
                "backup_timestamp": timestamp,
                "backup_date": datetime.utcnow().isoformat(),
                "metadata": collection.metadata,
                "count": collection.count(),
                "data": {
                    "ids": all_data["ids"],
                    "documents": all_data["documents"],
                    "metadatas": all_data["metadatas"],
                    "embeddings": all_data["embeddings"]
                }
            }
            
            # JSONファイルに保存
            backup_file = os.path.join(backup_path, "backup.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # メタデータファイル作成
            metadata_file = os.path.join(backup_path, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "collection_name": name,
                    "backup_timestamp": timestamp,
                    "backup_date": datetime.utcnow().isoformat(),
                    "record_count": collection.count(),
                    "file_size_mb": round(os.path.getsize(backup_file) / 1024 / 1024, 2)
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(
                "collection_backup_created",
                collection_name=name,
                backup_path=backup_path,
                record_count=collection.count(),
                file_size_mb=round(os.path.getsize(backup_file) / 1024 / 1024, 2)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "collection_backup_failed",
                collection_name=name,
                error=str(e)
            )
            return False
    
    def restore_collection(self, backup_path: str, new_name: Optional[str] = None) -> bool:
        """バックアップからコレクション復元"""
        try:
            # バックアップファイル読み込み
            backup_file = os.path.join(backup_path, "backup.json")
            if not os.path.exists(backup_file):
                self.logger.error(
                    "backup_file_not_found",
                    backup_path=backup_path
                )
                return False
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 復元先コレクション名
            collection_name = new_name or backup_data["collection_name"]
            
            # コレクション作成
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata=backup_data["metadata"]
            )
            
            # データ復元
            data = backup_data["data"]
            if data["ids"]:
                collection.add(
                    ids=data["ids"],
                    documents=data["documents"],
                    metadatas=data["metadatas"],
                    embeddings=data["embeddings"]
                )
            
            self.logger.info(
                "collection_restored",
                original_name=backup_data["collection_name"],
                restored_name=collection_name,
                record_count=len(data["ids"]) if data["ids"] else 0,
                backup_date=backup_data["backup_date"]
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "collection_restore_failed",
                backup_path=backup_path,
                error=str(e)
            )
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧取得"""
        try:
            backups = []
            
            if not os.path.exists(self.backup_directory):
                return backups
            
            for backup_dir in os.listdir(self.backup_directory):
                backup_path = os.path.join(self.backup_directory, backup_dir)
                metadata_file = os.path.join(backup_path, "metadata.json")
                
                if os.path.isdir(backup_path) and os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backups.append({
                            "backup_name": backup_dir,
                            "backup_path": backup_path,
                            **metadata
                        })
                    except Exception as e:
                        self.logger.warning(
                            "backup_metadata_read_failed",
                            backup_dir=backup_dir,
                            error=str(e)
                        )
            
            # 日付順でソート（新しい順）
            backups.sort(key=lambda x: x.get("backup_timestamp", ""), reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error("backup_listing_failed", error=str(e))
            return []
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """古いバックアップのクリーンアップ"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return 0
            
            # 削除対象
            to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    shutil.rmtree(backup["backup_path"])
                    deleted_count += 1
                    self.logger.info(
                        "old_backup_deleted",
                        backup_name=backup["backup_name"],
                        backup_date=backup.get("backup_date", "unknown")
                    )
                except Exception as e:
                    self.logger.warning(
                        "backup_deletion_failed",
                        backup_path=backup["backup_path"],
                        error=str(e)
                    )
            
            self.logger.info(
                "backup_cleanup_completed",
                deleted_count=deleted_count,
                remaining_count=len(backups) - deleted_count
            )
            
            return deleted_count
            
        except Exception as e:
            self.logger.error("backup_cleanup_failed", error=str(e))
            return 0
    
    def get_storage_info(self) -> Dict[str, Any]:
        """ストレージ使用状況取得"""
        try:
            # データベースサイズ
            db_size = 0
            if os.path.exists(self.persist_directory):
                for dirpath, dirnames, filenames in os.walk(self.persist_directory):
                    for filename in filenames:
                        if not filename.startswith('.'):
                            filepath = os.path.join(dirpath, filename)
                            db_size += os.path.getsize(filepath)
            
            # バックアップサイズ
            backup_size = 0
            backup_count = 0
            if os.path.exists(self.backup_directory):
                for dirpath, dirnames, filenames in os.walk(self.backup_directory):
                    backup_count = len([d for d in dirnames if os.path.isdir(os.path.join(self.backup_directory, d))])
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        backup_size += os.path.getsize(filepath)
            
            # コレクション統計
            collections = self.list_collections()
            total_memories = sum(col.get("count", 0) for col in collections)
            
            storage_info = {
                "database_size_mb": round(db_size / 1024 / 1024, 2),
                "backup_size_mb": round(backup_size / 1024 / 1024, 2),
                "total_size_mb": round((db_size + backup_size) / 1024 / 1024, 2),
                "collection_count": len(collections),
                "total_memories": total_memories,
                "backup_count": backup_count,
                "persist_directory": self.persist_directory,
                "backup_directory": self.backup_directory
            }
            
            self.logger.info("storage_info_retrieved", **storage_info)
            
            return storage_info
            
        except Exception as e:
            self.logger.error("storage_info_failed", error=str(e))
            return {
                "database_size_mb": 0,
                "backup_size_mb": 0,
                "total_size_mb": 0,
                "collection_count": 0,
                "total_memories": 0,
                "backup_count": 0,
                "persist_directory": self.persist_directory,
                "backup_directory": self.backup_directory
            }