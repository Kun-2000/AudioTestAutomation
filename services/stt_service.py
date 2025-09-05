"""
STT 服務模組 - 使用 OpenAI GPT-4o-transcribe (非同步版本)
"""

import logging
from pathlib import Path
from typing import Tuple
from openai import AsyncOpenAI, APIError  # 改為 AsyncOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)


class STTService:
    """OpenAI GPT-4o-transcribe STT 服務"""

    def __init__(self):
        """初始化 STT 服務"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API Key 未設定")

            # 改為 AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.STT_MODEL
            self.prompt = settings.STT_PROMPT

            logger.info("STT 服務 (非同步) 初始化成功")

        except Exception as e:
            logger.error(f"STT 服務初始化失敗: {e}")
            raise

    async def transcribe_audio(self, audio_file_path: str) -> Tuple[str, float]:
        """使用 OpenAI GPT-4o-transcribe 轉錄音檔 (非同步版本)"""
        try:
            audio_path = Path(audio_file_path)

            if not audio_path.exists():
                raise FileNotFoundError(f"音檔不存在: {audio_file_path}")

            file_size = audio_path.stat().st_size
            max_size = 25 * 1024 * 1024

            if file_size > max_size:
                raise ValueError(
                    f"檔案過大: {file_size / 1024 / 1024:.1f}MB，超過 25MB 限制"
                )

            if file_size < 1024:
                raise ValueError("檔案過小，可能沒有有效的音檔內容")

            logger.info(f"開始轉錄音檔: {audio_path.name} ({file_size / 1024:.1f} KB)")

            with open(audio_file_path, "rb") as audio_file:
                # 改為 await
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language="zh",
                    prompt=self.prompt,
                    response_format="json",
                    temperature=0.0,
                )

            transcript = response.text.strip()

            if not transcript:
                raise ValueError("無法識別語音內容，檔案可能損壞或不包含語音")

            confidence = 1.0

            logger.info(
                f"轉錄成功: {transcript[:50]}{'...' if len(transcript) > 50 else ''}"
            )

            return transcript, confidence

        except APIError as e:
            logger.error(f"OpenAI API 錯誤: {e}")
            raise RuntimeError(f"語音轉錄失敗: {e}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"檔案處理錯誤: {e}")
            raise
        except Exception as e:
            logger.error(f"STT 服務錯誤: {e}")
            raise RuntimeError(f"語音轉錄失敗: {e}")

    async def test_connection(self) -> bool:
        """測試 OpenAI GPT-4o-transcribe 連接 (非同步版本)"""
        try:
            logger.info("測試 OpenAI GPT-4o-transcribe 連接...")
            # 改為 await
            models = await self.client.models.list()
            available_models = [model.id for model in models.data]
            model_available = self.model in available_models

            if model_available:
                logger.info(f"OpenAI {self.model} 連接測試成功")
                return True
            else:
                logger.warning(f"未找到 {self.model} 模型")
                return False
        except Exception as e:
            logger.error(f"OpenAI GPT-4o-transcribe 連接測試失敗: {e}")
            return False
