"""
Mock 音檔存放系統模組
"""

import logging
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any

from config.settings import settings
from models.test_models import AudioFile
from utils.audio_utils import get_audio_duration

logger = logging.getLogger(__name__)


class AudioStorageMock:
    """Mock 音檔存放系統"""

    def __init__(self):
        """初始化 Mock 音檔存放系統"""
        # 模擬的音檔後設資料存儲
        self.audio_metadata = {}

        # 確保存放目錄存在
        settings.AUDIO_PATH.mkdir(parents=True, exist_ok=True)

        logger.info("Mock 音檔存放系統初始化完成")

    def store_audio(
        self, audio_file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        儲存音檔並回傳檔案 ID

        Args:
            audio_file_path: 音檔路徑
            metadata: 額外的後設資料

        Returns:
            音檔 ID
        """
        try:
            source_path = Path(audio_file_path)

            if not source_path.exists():
                raise FileNotFoundError(f"音檔不存在: {audio_file_path}")

            # 生成唯一的檔案 ID
            file_id = str(uuid.uuid4())

            # 創建目標檔案路徑
            file_extension = source_path.suffix
            target_filename = f"{file_id}{file_extension}"
            target_path = settings.AUDIO_PATH / target_filename

            # 複製檔案到存放目錄
            shutil.copy2(source_path, target_path)

            # 獲取檔案資訊
            file_size = target_path.stat().st_size
            duration = get_audio_duration(target_path)

            # 儲存後設資料
            self.audio_metadata[file_id] = {
                "file_id": file_id,
                "original_filename": source_path.name,
                "stored_filename": target_filename,
                "file_path": str(target_path),
                "file_size": file_size,
                "duration": duration,
                "format": file_extension[1:],  # 移除點號
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            logger.info("音檔已儲存: %s (ID: %s)", target_filename, file_id)

            return file_id

        except Exception as e:
            logger.error("儲存音檔失敗: %s", e)
            raise RuntimeError(f"音檔儲存錯誤: {e}") from e

    def retrieve_audio(self, file_id: str) -> Optional[AudioFile]:
        """
        根據檔案 ID 讀取音檔

        Args:
            file_id: 音檔 ID

        Returns:
            音檔資訊，若找不到則回傳 None
        """
        try:
            if file_id not in self.audio_metadata:
                raise KeyError(f"找不到音檔 ID: {file_id}")

            metadata = self.audio_metadata[file_id]
            file_path = Path(metadata["file_path"])

            # 檢查檔案是否仍然存在
            if not file_path.exists():
                logger.error("音檔檔案已遺失: %s", metadata["stored_filename"])
                # 從後設資料中移除
                del self.audio_metadata[file_id]
                raise FileNotFoundError(
                    f"音檔檔案已遺失: {metadata['stored_filename']}"
                )

            # 創建 AudioFile 物件
            audio_file = AudioFile(
                file_path=str(file_path),
                duration=metadata["duration"],
                file_size=metadata["file_size"],
                format=metadata["format"],
            )

            logger.info("音檔讀取成功: %s", metadata["stored_filename"])

            return audio_file

        except (FileNotFoundError, KeyError, OSError) as e:
            logger.error("讀取音檔失敗: %s", e)
        return None

    def delete_audio(self, file_id: str) -> bool:
        """
        刪除音檔

        Args:
            file_id: 音檔 ID

        Returns:
            刪除是否成功
        """

        try:
            # 檢查 file_id 是否存在
            metadata = self._get_metadata(file_id)
            if not metadata:
                return False

            file_path = Path(metadata["file_path"])

            # 刪除實體檔案
            if file_path.exists():
                file_path.unlink()
                logger.info("實體檔案已刪除: %s", metadata["stored_filename"])

            # 從後設資料中移除
            del self.audio_metadata[file_id]

            logger.info("音檔已完全刪除: ID %s", file_id)

            return True

        except FileNotFoundError as e:
            logger.error("刪除音檔失敗（檔案未找到）: %s", e)
        except KeyError as e:
            logger.error("刪除音檔失敗（鍵錯誤）: %s", e)
        except OSError as e:
            logger.error("刪除音檔失敗（系統錯誤）: %s", e)
        return False

    def _get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根據 file_id 獲取後設資料，若不存在則記錄警告並返回 None

        Args:
            file_id: 音檔 ID

        Returns:
            後設資料字典，若不存在則返回 None
        """
        if file_id not in self.audio_metadata:
            logger.warning("找不到音檔 ID: %s", file_id)
            return None
        return self.audio_metadata[file_id]

    def list_audio_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出音檔清單

        Args:
            limit: 限制回傳數量

        Returns:
            音檔資訊列表
        """
        try:
            audio_list = []

            # 依創建時間排序（最新在前）
            sorted_items = sorted(
                self.audio_metadata.items(),
                key=lambda x: x[1]["created_at"],
                reverse=True,
            )

            for file_id, metadata in sorted_items[:limit]:
                audio_list.append(
                    {
                        "file_id": file_id,
                        "original_filename": metadata["original_filename"],
                        "file_size": metadata["file_size"],
                        "duration": metadata["duration"],
                        "format": metadata["format"],
                        "created_at": metadata["created_at"],
                    }
                )

            return audio_list

        except KeyError as e:
            logger.error("列出音檔清單失敗（鍵錯誤）: %s", e)
        except OSError as e:
            logger.error("列出音檔清單失敗（系統錯誤）: %s", e)
        return []

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        獲取存放系統統計資訊

        Returns:
            統計資訊字典
        """
        try:
            total_files = len(self.audio_metadata)
            total_size = sum(meta["file_size"] for meta in self.audio_metadata.values())
            total_duration = sum(
                meta["duration"] for meta in self.audio_metadata.values()
            )

            # 計算平均檔案大小
            avg_file_size = total_size / total_files if total_files > 0 else 0

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "total_duration_seconds": round(total_duration, 2),
                "total_duration_minutes": round(total_duration / 60, 2),
                "average_file_size_kb": round(avg_file_size / 1024, 2),
                "storage_path": str(settings.AUDIO_PATH),
            }

        except KeyError as e:
            logger.error("獲取存放統計失敗（鍵錯誤）: %s", e)
        except ZeroDivisionError as e:
            logger.error("獲取存放統計失敗（除以零錯誤）: %s", e)
        except OSError as e:
            logger.error("獲取存放統計失敗（系統錯誤）: %s", e)
        except ValueError as e:
            logger.error("獲取存放統計失敗（值錯誤）: %s", e)

            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "total_duration_seconds": 0,
                "total_duration_minutes": 0,
                "average_file_size_kb": 0,
                "storage_path": str(settings.AUDIO_PATH),
            }

    def cleanup_old_files(self, days: int = 7) -> int:
        """
        清理舊檔案

        Args:
            days: 保留天數

        Returns:
            清理的檔案數量
        """
        try:

            cutoff_date = datetime.now() - timedelta(days=days)
            cleanup_count = 0

            # 找出要清理的檔案
            files_to_delete = []
            for file_id, metadata in self.audio_metadata.items():
                created_at = datetime.fromisoformat(metadata["created_at"])
                if created_at < cutoff_date:
                    files_to_delete.append(file_id)

            # 執行清理
            for file_id in files_to_delete:
                if self.delete_audio(file_id):
                    cleanup_count += 1

            logger.info("清理完成，共清理了 %d 個舊檔案", cleanup_count)

            return cleanup_count

        except KeyError as e:
            logger.error("清理舊檔案失敗（鍵錯誤）: %s", e)
        except ValueError as e:
            logger.error("清理舊檔案失敗（值錯誤）: %s", e)
        except OSError as e:
            logger.error("清理舊檔案失敗（系統錯誤）: %s", e)
        except RuntimeError as e:
            logger.error("清理舊檔案失敗（執行錯誤）: %s", e)

        return 0
