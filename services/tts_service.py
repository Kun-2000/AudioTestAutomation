"""
TTS 服務模組 - 使用 Yating TTS (非同步版本)
"""

import base64
import logging
import uuid
import httpx

from config.settings import settings
from models.test_models import TestScript, SpeakerRole, AudioFile
from utils.audio_utils import (
    combine_audio_segments,
    create_silence,
    save_audio_file,
    get_audio_duration,
)

logger = logging.getLogger(__name__)


class TTSService:
    """Yating TTS 服務"""

    def __init__(self):
        """初始化 Yating TTS 服務"""
        try:
            if not settings.YATING_API_KEY:
                raise ValueError("Yating API Key 未設定")

            self.endpoint = settings.YATING_TTS_ENDPOINT
            self.headers = {
                "Content-Type": "application/json",
                "key": settings.YATING_API_KEY,
            }
            self.client = httpx.AsyncClient(headers=self.headers, timeout=120.0)

            self.voice_mapping = {
                SpeakerRole.CUSTOMER: settings.YATING_TTS_MODEL_CUSTOMER,
                SpeakerRole.AGENT: settings.YATING_TTS_MODEL_AGENT,
            }
            self.speed = settings.YATING_TTS_SPEED
            self.pitch = settings.YATING_TTS_PITCH
            self.energy = settings.YATING_TTS_ENERGY
            self.encoding = settings.YATING_TTS_ENCODING
            self.sample_rate = settings.YATING_TTS_SAMPLE_RATE

            logger.info("Yating TTS 服務 (非同步) 初始化成功")

        except Exception as e:
            logger.error("Yating TTS 服務初始化失敗: %s", e)
            raise

    async def generate_dialogue_audio(self, test_script: TestScript) -> AudioFile:
        """從測試腳本生成對話音檔 (非同步版本)"""
        dialogue_lines = test_script.parse_content()
        if not dialogue_lines:
            raise ValueError("腳本中沒有可識別的對話內容")

        logger.info("開始生成對話音檔 (Yating)，共 %d 行對話", len(dialogue_lines))

        audio_segments = []
        for i, line in enumerate(dialogue_lines):
            # 循序執行 TTS 請求
            speech_audio = await self._synthesize_speech(line.text, line.speaker)
            audio_segments.append(speech_audio)

            # 在對話之間插入靜音
            if i < len(dialogue_lines) - 1:
                silence = create_silence(line.pause_after)
                audio_segments.append(silence)

        combined_audio = combine_audio_segments(audio_segments)

        filename = f"dialogue_yating_{uuid.uuid4().hex[:8]}.mp3"
        file_path = settings.AUDIO_PATH / filename
        save_audio_file(combined_audio, file_path)

        duration = get_audio_duration(file_path)
        file_size = file_path.stat().st_size

        audio_file = AudioFile(
            file_path=str(file_path),
            duration=duration,
            file_size=file_size,
            format="mp3" if self.encoding == "MP3" else "wav",
        )
        logger.info("對話音檔生成成功 (Yating): %s, 時長: %.1f秒", filename, duration)
        return audio_file

    async def _synthesize_speech(self, text: str, speaker: SpeakerRole) -> bytes:
        """使用 Yating TTS API 將單段文字合成語音 bytes (非同步版本)"""
        try:
            model = self.voice_mapping[speaker]
            request_data = {
                "input": {"text": text.strip(), "type": "text"},
                "voice": {
                    "model": model,
                    "speed": self.speed,
                    "pitch": self.pitch,
                    "energy": self.energy,
                },
                "audioConfig": {
                    "encoding": self.encoding,
                    "sampleRate": self.sample_rate,
                },
            }
            response = await self.client.post(self.endpoint, json=request_data)
            response.raise_for_status()
            result = response.json()

            if "audioContent" not in result:
                raise RuntimeError("Yating TTS 回應無音頻內容")

            return base64.b64decode(result["audioContent"])

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                "Yating TTS API 請求失敗: %s - %s", e.response.status_code, error_detail
            )
            raise RuntimeError(f"Yating TTS API 錯誤: {error_detail}") from e
        except Exception as e:
            logger.error("Yating TTS 底層合成失敗: %s", e)
            raise

    async def test_connection(self) -> bool:
        """測試 Yating TTS 連接 (非同步版本)"""
        try:
            await self._synthesize_speech("測試", SpeakerRole.CUSTOMER)
            logger.info("Yating TTS 連接測試成功")
            return True
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                "Yating TTS API 請求失敗: %s - %s", e.response.status_code, error_detail
            )
            raise RuntimeError(f"Yating TTS API 錯誤: {error_detail}") from e
        except httpx.RequestError as e:
            logger.error("Yating TTS API 請求錯誤: %s", e)
            raise RuntimeError("Yating TTS API 請求錯誤") from e
        except ValueError as e:
            logger.error("Yating TTS 回應解析錯誤: %s", e)
            raise RuntimeError("Yating TTS 回應解析錯誤") from e
