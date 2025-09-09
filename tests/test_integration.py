"""
整合測試檔案 - 測試 TestOrchestrator
"""

import sys
from pathlib import Path
import pytest
from services.test_orchestrator import TestOrchestrator
from models.test_models import AudioFile, TestStatus, TestResult

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_orchestrator_run_full_test_success(mocker):
    """
    測試 TestOrchestrator 完整流程 (成功案例)
    """
    # 1. Mock 所有外部依賴
    mock_tts_audio = AudioFile(file_path="/tmp/tts.mp3", duration=5.0)
    mocker.patch(
        "services.tts_service.TTSService.generate_dialogue_audio",
        return_value=mock_tts_audio,
    )
    mock_cs_audio = AudioFile(file_path="/tmp/cs_response.mp3", duration=5.0)
    mocker.patch(
        "mock.customer_service.CustomerServiceMock.simulate_call",
        return_value=mock_cs_audio,
    )
    mock_transcribed_text = "這是轉錄後的文字"
    mocker.patch(
        "services.stt_service.STTService.transcribe_audio",
        return_value=(mock_transcribed_text, 1.0),
    )
    mock_llm_analysis = {"accuracy_score": 95.0, "summary": "測試成功"}
    mocker.patch(
        "services.llm_service.LLMService.analyze_conversation",
        return_value=mock_llm_analysis,
    )
    mocker.patch(
        "mock.audio_storage.AudioStorageMock.store_audio", return_value="mock-uuid"
    )

    # 2. 執行測試
    orchestrator = TestOrchestrator()
    script_content = "客戶: 你好"
    result = TestResult(original_script=script_content)
    await orchestrator.run_full_test(result)

    # 3. 驗證結果
    assert result.status == TestStatus.COMPLETED
    assert result.original_script == script_content
    assert result.tts_audio == mock_tts_audio
    assert result.mock_response_audio == mock_cs_audio
    assert result.transcribed_text == mock_transcribed_text
    assert result.llm_analysis == mock_llm_analysis
    assert result.accuracy_score == 95.0
    assert result.error_message is None


@pytest.mark.asyncio
async def test_orchestrator_stt_fails(mocker):
    """
    測試 TestOrchestrator 流程 (STT 失敗案例)
    """
    # 1. Mock 依賴
    mocker.patch(
        "services.tts_service.TTSService.generate_dialogue_audio",
        return_value=AudioFile(file_path="/tmp/tts.mp3", duration=5.0),
    )
    mocker.patch(
        "mock.customer_service.CustomerServiceMock.simulate_call",
        return_value=AudioFile(file_path="/tmp/cs_response.mp3", duration=5.0),
    )
    mocker.patch(
        "mock.audio_storage.AudioStorageMock.store_audio", return_value="mock-uuid"
    )
    mocker.patch(
        "services.stt_service.STTService.transcribe_audio",
        side_effect=RuntimeError("STT API Error"),
    )

    # 2. 執行測試
    orchestrator = TestOrchestrator()
    script_content = "客戶: 你好"
    result = TestResult(original_script=script_content)
    await orchestrator.run_full_test(result)

    # 3. 驗證結果
    assert result.status == TestStatus.FAILED
    assert "STT API Error" in result.error_message
    assert result.accuracy_score == 0.0
