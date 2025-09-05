"""
測試編排器 - 執行完整的客服測試流程
"""

import logging
from datetime import datetime
from typing import Dict, Any

from config.settings import settings
from models.test_models import TestScript, TestResult, TestStatus
from services.tts_service import TTSService
from services.stt_service import STTService
from services.llm_service import LLMService
from mock.customer_service import CustomerServiceMock
from mock.audio_storage import AudioStorageMock

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """客服測試編排器"""

    def __init__(self):
        """初始化測試編排器"""
        try:
            logger.info("初始化 TTS 服務: Yating")
            self.tts_service = TTSService()
            logger.info("初始化 STT 服務: gpt-4o-transcribe")
            self.stt_service = STTService()
            logger.info("初始化 LLM 服務: gpt-4o")
            self.llm_service = LLMService()
            self.cs_mock = CustomerServiceMock()
            self.storage_mock = AudioStorageMock()
            logger.info("測試編排器初始化完成")
        except Exception as e:
            logger.error(f"測試編排器初始化失敗: {e}")
            raise

    async def run_full_test(self, result: TestResult):
        """
        執行完整的客服測試流程，直接修改傳入的 TestResult 物件。
        """
        result.status = TestStatus.RUNNING

        try:
            logger.info(f"開始執行客服測試 (ID: {result.test_id})")

            script_content = result.original_script
            if not script_content:
                raise ValueError("測試結果物件中缺少原始腳本")

            # 依序執行步驟，並將結果填充到傳入的 result 物件中
            await self._step1_script_to_speech(script_content, result)
            await self._step2_simulate_call(result)
            await self._step3_store_audio(result)
            await self._step4_speech_to_text(result)
            await self._step5_analyze_conversation(result)
            await self._step6_generate_report(result)

            result.status = TestStatus.COMPLETED
            logger.info(
                f"測試完成 (ID: {result.test_id}), 準確率: {result.accuracy_score:.1f}%"
            )
        except Exception as e:
            logger.error(f"測試執行失敗 (ID: {result.test_id}): {e}")
            result.status = TestStatus.FAILED
            result.error_message = str(e)

    async def _step1_script_to_speech(
        self, script_content: str, result: TestResult
    ) -> None:
        """步驟 1: 將測試腳本轉為語音"""
        logger.info("步驟 1: 執行 TTS 轉換...")
        test_script = TestScript(content=script_content)
        tts_audio = await self.tts_service.generate_dialogue_audio(test_script)
        result.tts_audio = tts_audio
        logger.info(f"TTS 轉換完成，音檔時長: {tts_audio.duration:.1f} 秒")

    async def _step2_simulate_call(self, result: TestResult) -> None:
        """步驟 2: 模擬客服通話"""
        logger.info("步驟 2: 模擬客服通話...")
        if not result.tts_audio:
            raise RuntimeError("TTS 音檔不存在，無法進行模擬通話")
        mock_response = self.cs_mock.simulate_call(result.tts_audio.file_path)
        result.mock_response_audio = mock_response
        logger.info(f"客服通話模擬完成，回應音檔時長: {mock_response.duration:.1f} 秒")

    async def _step3_store_audio(self, result: TestResult) -> None:
        """步驟 3: 儲存音檔到 Mock 存放系統"""
        logger.info("步驟 3: 儲存音檔...")
        if not result.mock_response_audio:
            raise RuntimeError("客服回應音檔不存在，無法儲存")
        metadata = {
            "test_id": result.test_id,
            "type": "customer_service_response",
            "created_at": datetime.now().isoformat(),
        }
        file_id = self.storage_mock.store_audio(
            result.mock_response_audio.file_path, metadata
        )
        logger.info(f"音檔儲存完成，檔案 ID: {file_id}")

    async def _step4_speech_to_text(self, result: TestResult) -> None:
        """步驟 4: 將客服回應音檔轉為文字"""
        logger.info("步驟 4: 執行 STT 轉換...")
        if not result.mock_response_audio:
            raise RuntimeError("客服回應音檔不存在，無法進行 STT")
        transcribed_text, confidence = await self.stt_service.transcribe_audio(
            result.mock_response_audio.file_path
        )
        result.transcribed_text = transcribed_text
        logger.info(f"STT 轉換完成，轉錄長度: {len(transcribed_text)} 字")

    async def _step5_analyze_conversation(self, result: TestResult) -> None:
        """步驟 5: 使用 LLM 分析對話品質"""
        logger.info("步驟 5: 執行對話品質分析...")
        if not result.transcribed_text:
            logger.warning("轉錄文字為空，跳過 LLM 分析")
            result.llm_analysis = {}
            return
        analysis = await self.llm_service.analyze_conversation(
            result.original_script, result.transcribed_text
        )
        result.llm_analysis = analysis
        logger.info(f"對話分析完成，準確率: {analysis.get('accuracy_score', 0):.1f}%")

    async def _step6_generate_report(self, result: TestResult) -> None:
        """步驟 6: 產生最終報告和分數"""
        logger.info("步驟 6: 產生測試報告...")
        if not result.llm_analysis:
            logger.warning("LLM 分析結果不存在，無法產生報告")
            result.accuracy_score = 0.0
            return
        accuracy_score = result.llm_analysis.get("accuracy_score", 0.0)
        result.accuracy_score = float(accuracy_score)
        logger.info(f"測試報告產生完成，最終分數: {result.accuracy_score:.1f}%")

    async def get_service_status(self) -> Dict[str, bool]:
        """檢查所有服務的狀態"""
        status = {}
        try:
            status["tts (yating)"] = await self.tts_service.test_connection()
        except Exception:
            status["tts (yating)"] = False
        try:
            status["stt (gpt-4o-transcribe)"] = await self.stt_service.test_connection()
        except Exception:
            status["stt (gpt-4o-transcribe)"] = False
        try:
            status["llm (gpt-4o)"] = await self.llm_service.test_connection()
        except Exception:
            status["llm (gpt-4o)"] = False
        status["mock_cs"] = True
        status["mock_storage"] = True
        return status
