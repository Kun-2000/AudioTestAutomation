"""
客服測試系統配置模組
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# 基礎路徑
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# 建立必要目錄
for folder in ["audio", "reports", "temp"]:
    (STORAGE_DIR / folder).mkdir(parents=True, exist_ok=True)


class Settings:
    """系統設定類別"""

    # OpenAI 設定
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    STT_MODEL: str = os.getenv("STT_MODEL", "gpt-4o-transcribe")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    STT_PROMPT: str = os.getenv("STT_PROMPT", "繁體中文")

    # Yating TTS 設定
    YATING_API_KEY: str = os.getenv("YATING_API_KEY", "")
    YATING_TTS_ENDPOINT: str = os.getenv(
        "YATING_TTS_ENDPOINT", "https://tts.api.yating.tw/v2/speeches/short"
    )
    YATING_TTS_MODEL_CUSTOMER: str = os.getenv(
        "YATING_TTS_MODEL_CUSTOMER", "zh_en_female_1"
    )
    YATING_TTS_MODEL_AGENT: str = os.getenv("YATING_TTS_MODEL_AGENT", "zh_en_male_1")
    YATING_TTS_SPEED: float = float(os.getenv("YATING_TTS_SPEED", "1.0"))
    YATING_TTS_PITCH: float = float(os.getenv("YATING_TTS_PITCH", "1.0"))
    YATING_TTS_ENERGY: float = float(os.getenv("YATING_TTS_ENERGY", "1.0"))
    YATING_TTS_ENCODING: str = os.getenv("YATING_TTS_ENCODING", "MP3")
    YATING_TTS_SAMPLE_RATE: str = os.getenv("YATING_TTS_SAMPLE_RATE", "16K")

    # 系統設定
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    MAX_AUDIO_DURATION: int = int(os.getenv("MAX_AUDIO_DURATION", "300"))

    # 路徑設定
    STORAGE_PATH: Path = STORAGE_DIR
    AUDIO_PATH: Path = STORAGE_DIR / "audio"
    REPORTS_PATH: Path = STORAGE_DIR / "reports"
    TEMP_PATH: Path = STORAGE_DIR / "temp"

    @classmethod
    def validate_config(cls) -> bool:
        """驗證必要配置"""
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 未設定")
        if not cls.YATING_API_KEY:
            errors.append("YATING_API_KEY 未設定")

        if errors:
            raise ValueError(f"配置錯誤: {', '.join(errors)}")
        return True


settings = Settings()
