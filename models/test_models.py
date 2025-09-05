"""
客服測試系統資料模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from pathlib import Path


class TestStatus(Enum):
    """測試狀態列舉"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SpeakerRole(Enum):
    """對話角色列舉"""

    CUSTOMER = "customer"
    AGENT = "agent"


@dataclass
class DialogueLine:
    """對話行資料"""

    speaker: SpeakerRole
    text: str
    pause_after: float = 1.0


@dataclass
class TestScript:
    """測試腳本資料"""

    content: str
    dialogue_lines: List[DialogueLine] = field(default_factory=list)

    def parse_content(self) -> List[DialogueLine]:
        """解析腳本內容為對話行"""
        lines = []
        for line in self.content.strip().split("\n"):
            if ":" in line:
                role_str, text = line.split(":", 1)
                role_str = role_str.strip().lower()
                if role_str in ["客戶", "customer"]:
                    role = SpeakerRole.CUSTOMER
                elif role_str in ["客服", "agent"]:
                    role = SpeakerRole.AGENT
                else:
                    continue
                lines.append(
                    DialogueLine(speaker=role, text=text.strip(), pause_after=1.0)
                )
        self.dialogue_lines = lines
        return lines


@dataclass
class AudioFile:
    """音檔資料"""

    file_path: str
    duration: float = 0.0
    file_size: int = 0
    format: str = "mp3"

    def get_web_path(self) -> str:
        """獲取可供 Web 存取的路徑"""
        # 將本地路徑轉換為 URL 路徑
        # 例如: /path/to/project/storage/audio/file.mp3 -> /storage/audio/file.mp3
        return "/storage/audio/" + Path(self.file_path).name


@dataclass
class TestResult:
    """測試結果資料"""

    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    status: TestStatus = TestStatus.PENDING
    original_script: str = ""
    tts_audio: Optional[AudioFile] = None
    mock_response_audio: Optional[AudioFile] = None
    transcribed_text: str = ""
    llm_analysis: Dict[str, Any] = field(default_factory=dict)
    accuracy_score: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "test_id": self.test_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "original_script": self.original_script,
            "tts_audio": (
                {
                    "file_path": self.tts_audio.file_path,
                    "duration": self.tts_audio.duration,
                    "web_path": self.tts_audio.get_web_path(),  # 新增 Web 路徑
                }
                if self.tts_audio
                else None
            ),
            "mock_response_audio": (
                {
                    "file_path": self.mock_response_audio.file_path,
                    "duration": self.mock_response_audio.duration,
                    "web_path": self.mock_response_audio.get_web_path(),  # 新增 Web 路徑
                }
                if self.mock_response_audio
                else None
            ),
            "transcribed_text": self.transcribed_text,
            "llm_analysis": self.llm_analysis,
            "accuracy_score": self.accuracy_score,
            "error_message": self.error_message,
        }
