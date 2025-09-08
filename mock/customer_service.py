"""
Mock 客服系統模組
"""

import logging
import random
import time
import uuid
import shutil
from pathlib import Path

# 修正為從專案根目錄開始的絕對路徑導入
from config.settings import settings
from models.test_models import AudioFile
from utils.audio_utils import get_audio_duration

logger = logging.getLogger(__name__)


class CustomerServiceMock:
    """Mock 客服系統 - 模擬一個高保真度的錄音系統"""

    def __init__(self):
        """初始化 Mock 客服系統"""
        logger.info("Mock 客服系統初始化完成")

    def simulate_call(self, input_audio_path: str) -> AudioFile:
        """
        模擬客服通話，並回傳一個「完美錄音」的音檔。
        在該模式下，系統會直接複製輸入的音檔，以模擬100%保真度的錄音。

        Args:
            input_audio_path: 輸入音檔路徑（客戶語音）

        Returns:
            模擬的「錄音」檔案資訊
        """
        try:
            source_path = Path(input_audio_path)
            if not source_path.exists():
                raise FileNotFoundError(f"輸入音檔不存在: {input_audio_path}")

            logger.info("開始模擬客服通話 (錄音模式)，輸入音檔: %s", source_path.name)

            # 模擬系統處理所需的時間
            processing_time = random.uniform(0.5, 1.5)
            time.sleep(processing_time)

            # --- 核心邏輯：複製檔案以模擬完美錄音 ---
            # 創建一個新的、唯一的檔名來代表「錄音檔」
            filename = f"recorded_{uuid.uuid4().hex[:8]}{source_path.suffix}"
            recorded_file_path = settings.AUDIO_PATH / filename

            # 使用 shutil.copy2 直接複製輸入的音檔
            shutil.copy2(source_path, recorded_file_path)

            # 獲取新檔案（即「錄音檔」）的資訊
            duration = get_audio_duration(recorded_file_path)
            file_size = recorded_file_path.stat().st_size

            audio_file = AudioFile(
                file_path=str(recorded_file_path),
                duration=duration,
                file_size=file_size,
                format=source_path.suffix.lstrip("."),
            )

            logger.info("模擬錄音已生成: %s, 時長: %.1f秒", filename, duration)

            return audio_file

        except Exception as e:
            logger.error("模擬客服通話失敗: %s", e)
            raise RuntimeError(f"Mock 客服系統錯誤: {e}") from e
