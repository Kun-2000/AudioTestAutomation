"""
客服測試系統資料模型 - 修改版（支援7步驟流程）
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


class TestStep(Enum):
    """測試步驟列舉 - 7個步驟"""

    IDLE = "idle"
    PREPROCESSING = "preprocessing"  # 測試對話腳本
    STARTUP = "startup"  # 系統啟動
    TTS_CONVERSION = "tts_conversion"  # 客服系統
    RECORDING = "recording"  # 錄音系統
    STORAGE = "storage"  # 音檔存放系統
    LLM_ANALYSIS = "llm_analysis"  # LLM分析系統
    COMPLETION = "completion"  # 系統結束


class SpeakerRole(Enum):
    """對話角色列舉"""

    CUSTOMER = "customer"
    AGENT = "agent"


# 步驟進度映射 - 每個步驟完成後的整體進度
STEP_PROGRESS_MAPPING = {
    TestStep.IDLE.value: 0,
    TestStep.PREPROCESSING.value: 14,  # 1/7 ≈ 14%
    TestStep.STARTUP.value: 28,  # 2/7 ≈ 28%
    TestStep.TTS_CONVERSION.value: 43,  # 3/7 ≈ 43%
    TestStep.RECORDING.value: 57,  # 4/7 ≈ 57%
    TestStep.STORAGE.value: 71,  # 5/7 ≈ 71%
    TestStep.LLM_ANALYSIS.value: 86,  # 6/7 ≈ 86%
    TestStep.COMPLETION.value: 100,  # 7/7 = 100%
}

# 步驟顯示名稱映射
STEP_DISPLAY_NAMES = {
    TestStep.PREPROCESSING.value: "測試對話腳本",
    TestStep.STARTUP.value: "系統啟動",
    TestStep.TTS_CONVERSION.value: "客服系統",
    TestStep.RECORDING.value: "錄音系統",
    TestStep.STORAGE.value: "音檔存放系統",
    TestStep.LLM_ANALYSIS.value: "LLM分析系統",
    TestStep.COMPLETION.value: "系統結束",
}


@dataclass
class DialogueLine:
    """對話行資料"""

    speaker: SpeakerRole
    text: str
    pause_after: float = 0.3


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
                lines.append(DialogueLine(speaker=role, text=text.strip()))
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
class StepDetail:
    """步驟詳細資訊"""

    step_name: str
    step_description: str
    sub_stage: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # 預估剩餘秒數
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """測試結果資料 - 支援7步驟流程"""

    # 基本資訊
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    status: TestStatus = TestStatus.PENDING
    original_script: str = ""

    # === 新增：7步驟狀態追蹤 ===
    current_step: str = TestStep.IDLE.value
    step_progress: float = 0.0  # 當前步驟內部進度 (0-100)
    overall_progress: float = 0.0  # 整體測試進度 (0-100)
    completed_steps: List[str] = field(default_factory=list)

    # === 步驟1：測試對話腳本 ===
    parsed_dialogue_count: int = 0
    script_validation_info: Dict[str, Any] = field(default_factory=dict)

    # === 步驟2：系統啟動 ===
    apis_verified: Dict[str, bool] = field(default_factory=dict)
    startup_info: Dict[str, Any] = field(default_factory=dict)

    # === 步驟3：客服系統 ===
    tts_audio: Optional[AudioFile] = None
    tts_generation_info: Dict[str, Any] = field(default_factory=dict)

    # === 步驟4：錄音系統 ===
    recorded_audio: Optional[AudioFile] = None  # 新增：錄音音檔
    recording_info: Dict[str, Any] = field(default_factory=dict)

    # === 步驟5：音檔存放系統 ===
    storage_file_id: Optional[str] = None
    storage_metadata: Dict[str, Any] = field(default_factory=dict)

    # === 步驟6：LLM分析系統 ===
    # STT 階段
    stt_stage: str = "pending"  # pending, processing, completed
    transcribed_text: str = ""
    stt_confidence: float = 0.0
    stt_info: Dict[str, Any] = field(default_factory=dict)

    # LLM 階段
    llm_stage: str = "pending"  # pending, processing, completed
    llm_analysis: Dict[str, Any] = field(default_factory=dict)
    accuracy_score: float = 0.0

    # === 步驟7：系統結束 ===
    final_report: Dict[str, Any] = field(default_factory=dict)
    cleanup_info: Dict[str, Any] = field(default_factory=dict)

    # 錯誤處理
    error_message: Optional[str] = None

    # === 原有的相容性欄位 ===
    mock_response_audio: Optional[AudioFile] = None  # 保持向後相容

    def __post_init__(self):
        """初始化後處理"""
        # 確保 mock_response_audio 與 recorded_audio 同步
        if self.recorded_audio and not self.mock_response_audio:
            self.mock_response_audio = self.recorded_audio

    def update_step_status(
        self,
        step: str,
        progress: float = 0.0,
        _sub_stage: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ):
        """更新步驟狀態"""
        self.current_step = step
        self.step_progress = max(0.0, min(100.0, progress))
        self.overall_progress = self.calculate_overall_progress()

        # 更新步驟詳細資訊
        if additional_info:
            step_info_field = f"{step}_info"
            if hasattr(self, step_info_field):
                getattr(self, step_info_field).update(additional_info)

    def complete_current_step(self):
        """完成當前步驟"""
        if self.current_step != TestStep.IDLE.value:
            if self.current_step not in self.completed_steps:
                self.completed_steps.append(self.current_step)
            self.step_progress = 100.0
            self.overall_progress = self.calculate_overall_progress()

    def calculate_overall_progress(self) -> float:
        """計算整體進度"""
        base_progress = STEP_PROGRESS_MAPPING.get(self.current_step, 0)

        # 如果當前步驟已完成，直接返回基礎進度
        if self.current_step in self.completed_steps:
            return float(base_progress)

        # 計算當前步驟的貢獻
        step_weight = 100 / 7  # 每個步驟佔約 14.3%
        step_contribution = (self.step_progress / 100) * step_weight

        return min(100.0, base_progress + step_contribution)

    def get_step_detail(self) -> StepDetail:
        """獲取當前步驟詳細資訊"""
        display_name = STEP_DISPLAY_NAMES.get(self.current_step, self.current_step)

        # 根據步驟生成描述
        descriptions = {
            TestStep.PREPROCESSING.value: "腳本驗證與解析中",
            TestStep.STARTUP.value: "API連線驗證與環境初始化中",
            TestStep.TTS_CONVERSION.value: "文字轉語音處理中",
            TestStep.RECORDING.value: "模擬通話錄音中",
            TestStep.STORAGE.value: "音檔歸檔與管理中",
            TestStep.LLM_ANALYSIS.value: "語音轉文字與品質分析中",
            TestStep.COMPLETION.value: "報告生成與資源清理中",
        }

        description = descriptions.get(self.current_step, "處理中")

        # 獲取子階段資訊
        sub_stage = None
        if self.current_step == TestStep.LLM_ANALYSIS.value:
            if self.stt_stage == "processing":
                sub_stage = "語音轉文字中"
            elif self.llm_stage == "processing":
                sub_stage = "智能分析中"

        return StepDetail(
            step_name=display_name,
            step_description=description,
            sub_stage=sub_stage,
            estimated_time_remaining=self._estimate_remaining_time(),
            additional_info=self._get_current_step_info(),
        )

    def _estimate_remaining_time(self) -> Optional[int]:
        """估算剩餘時間（秒）"""
        # 簡單的時間估算邏輯
        time_estimates = {
            TestStep.PREPROCESSING.value: 5,
            TestStep.STARTUP.value: 10,
            TestStep.TTS_CONVERSION.value: 30,
            TestStep.RECORDING.value: 5,
            TestStep.STORAGE.value: 3,
            TestStep.LLM_ANALYSIS.value: 45,
            TestStep.COMPLETION.value: 5,
        }

        base_time = time_estimates.get(self.current_step, 10)
        remaining_ratio = (100 - self.step_progress) / 100
        return max(1, int(base_time * remaining_ratio))

    def _get_current_step_info(self) -> Dict[str, Any]:
        """獲取當前步驟的額外資訊"""
        step_info_field = f"{self.current_step}_info"
        if hasattr(self, step_info_field):
            return getattr(self, step_info_field)
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式 - 擴充版"""
        base_dict = {
            "test_id": self.test_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "current_step": self.current_step,
            "step_progress": self.step_progress,
            "overall_progress": self.overall_progress,
            "completed_steps": self.completed_steps,
            "original_script": self.original_script,
            "transcribed_text": self.transcribed_text,
            "llm_analysis": self.llm_analysis,
            "accuracy_score": self.accuracy_score,
            "error_message": self.error_message,
            # 音檔資訊
            "tts_audio": (
                {
                    "file_path": self.tts_audio.file_path,
                    "duration": self.tts_audio.duration,
                    "web_path": self.tts_audio.get_web_path(),
                }
                if self.tts_audio
                else None
            ),
            "recorded_audio": (
                {
                    "file_path": self.recorded_audio.file_path,
                    "duration": self.recorded_audio.duration,
                    "web_path": self.recorded_audio.get_web_path(),
                }
                if self.recorded_audio
                else None
            ),
            # 向後相容
            "mock_response_audio": (
                {
                    "file_path": self.mock_response_audio.file_path,
                    "duration": self.mock_response_audio.duration,
                    "web_path": self.mock_response_audio.get_web_path(),
                }
                if self.mock_response_audio
                else None
            ),
            # 詳細資訊
            "step_detail": self.get_step_detail().__dict__,
            "parsed_dialogue_count": self.parsed_dialogue_count,
            "apis_verified": self.apis_verified,
            "storage_file_id": self.storage_file_id,
            "stt_confidence": self.stt_confidence,
            "final_report": self.final_report,
        }

        return base_dict

    def get_status_response(self) -> Dict[str, Any]:
        """獲取狀態回應格式（用於 API）"""
        step_detail = self.get_step_detail()

        return {
            "test_id": self.test_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "step_progress": self.step_progress,
            "overall_progress": self.overall_progress,
            "step_details": {
                "step_name": step_detail.step_name,
                "step_description": step_detail.step_description,
                "sub_stage": step_detail.sub_stage,
                "estimated_time_remaining": step_detail.estimated_time_remaining,
            },
            "completed_steps": self.completed_steps,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }
