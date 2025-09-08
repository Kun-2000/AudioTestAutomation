"""
測試編排器 - 執行完整的7步驟客服測試流程
"""

import logging
import hashlib
from datetime import datetime
from typing import Dict
import httpx

from models.test_models import TestScript, TestResult, TestStatus, TestStep
from services.tts_service import TTSService
from services.stt_service import STTService
from services.llm_service import LLMService
from mock.customer_service import CustomerServiceMock
from mock.audio_storage import AudioStorageMock

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """客服測試編排器 - 支援7步驟流程"""

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
            logger.error("測試編排器初始化失敗: %s", e)
            raise

    async def run_full_test(self, result: TestResult):
        """
        執行完整的7步驟測試流程，直接修改傳入的 TestResult 物件。
        """
        result.status = TestStatus.RUNNING
        result.current_step = TestStep.PREPROCESSING.value

        try:
            logger.info("開始執行7步驟客服測試 (ID: %s)", result.test_id)

            script_content = result.original_script
            if not script_content:
                raise ValueError("測試結果物件中缺少原始腳本")

            # === 執行7個步驟 ===
            await self._step1_preprocessing(script_content, result)
            await self._step2_startup(result)
            await self._step3_tts_conversion(script_content, result)
            await self._step4_recording(result)
            await self._step5_storage(result)
            await self._step6_llm_analysis(result)
            await self._step7_completion(result)

            # 測試完成
            result.status = TestStatus.COMPLETED
            result.current_step = TestStep.COMPLETION.value
            result.overall_progress = 100.0

            logger.info(
                "7步驟測試完成 (ID: %s), 準確率: %.1f%%",
                result.test_id,
                result.accuracy_score,
            )

        except ValueError as e:
            logger.error("測試執行失敗（值錯誤） (ID: %s): %s", result.test_id, e)
            result.status = TestStatus.FAILED
            result.error_message = f"值錯誤: {e}"
        except RuntimeError as e:
            logger.error("測試執行失敗（執行錯誤） (ID: %s): %s", result.test_id, e)
            result.status = TestStatus.FAILED
            result.error_message = f"執行錯誤: {e}"
        except (TypeError, KeyError) as e:
            logger.error("測試執行失敗（類型或鍵錯誤） (ID: %s): %s", result.test_id, e)
            result.status = TestStatus.FAILED
            result.error_message = f"類型或鍵錯誤: {e}"

    async def _step1_preprocessing(self, script_content: str, result: TestResult):
        """步驟1：測試對話腳本 - 腳本驗證與預處理"""
        logger.info("步驟 1/7: 測試對話腳本處理...")

        result.update_step_status(TestStep.PREPROCESSING.value, 0.0)

        try:
            # 腳本格式驗證
            if not script_content.strip():
                raise ValueError("測試腳本不能為空")

            result.update_step_status(TestStep.PREPROCESSING.value, 20.0)

            # 解析對話角色和內容
            test_script = TestScript(content=script_content)
            dialogue_lines = test_script.parse_content()

            if not dialogue_lines:
                raise ValueError("腳本中沒有可識別的對話內容")

            result.update_step_status(TestStep.PREPROCESSING.value, 60.0)

            # 儲存解析結果
            result.parsed_dialogue_count = len(dialogue_lines)
            result.script_validation_info = {
                "total_lines": len(script_content.strip().split("\n")),
                "dialogue_lines": len(dialogue_lines),
                "customer_lines": len(
                    [
                        line
                        for line in dialogue_lines
                        if line.speaker.value == "customer"
                    ]
                ),
                "agent_lines": len(
                    [line for line in dialogue_lines if line.speaker.value == "agent"]
                ),
                "script_hash": hashlib.md5(script_content.encode()).hexdigest()[:8],
                "validated_at": datetime.now().isoformat(),
            }

            result.update_step_status(TestStep.PREPROCESSING.value, 100.0)
            result.complete_current_step()

            logger.info("步驟1完成：解析 %d 行對話", len(dialogue_lines))

        except Exception as e:
            logger.error("步驟1失敗: %s", e)
            raise RuntimeError(f"測試對話腳本處理失敗: {e}") from e

    async def _step2_startup(self, result: TestResult):
        """步驟2：系統啟動 - 初始化測試環境，準備呼叫 API"""
        logger.info("步驟 2/7: 系統啟動...")

        result.update_step_status(TestStep.STARTUP.value, 0.0)

        try:
            # API 連線驗證
            logger.info("驗證 TTS API 連線...")
            tts_status = await self.tts_service.test_connection()
            result.apis_verified["tts"] = tts_status
            result.update_step_status(TestStep.STARTUP.value, 25.0)

            if not tts_status:
                raise RuntimeError("TTS API 連線失敗")

            logger.info("驗證 STT API 連線...")
            stt_status = await self.stt_service.test_connection()
            result.apis_verified["stt"] = stt_status
            result.update_step_status(TestStep.STARTUP.value, 50.0)

            if not stt_status:
                raise RuntimeError("STT API 連線失敗")

            logger.info("驗證 LLM API 連線...")
            llm_status = await self.llm_service.test_connection()
            result.apis_verified["llm"] = llm_status
            result.update_step_status(TestStep.STARTUP.value, 75.0)

            if not llm_status:
                raise RuntimeError("LLM API 連線失敗")

            # 測試環境初始化完成
            result.startup_info = {
                "apis_verified_at": datetime.now().isoformat(),
                "test_environment": "ready",
                "services_status": {
                    "tts_service": "connected",
                    "stt_service": "connected",
                    "llm_service": "connected",
                    "mock_services": "ready",
                },
            }

            result.update_step_status(TestStep.STARTUP.value, 100.0)
            result.complete_current_step()

            logger.info("步驟2完成：系統啟動，所有 API 連線正常")

        except Exception as e:
            logger.error("步驟2失敗: %s", e)
            raise RuntimeError(f"系統啟動失敗: {e}") from e

    async def _step3_tts_conversion(self, script_content: str, result: TestResult):
        """步驟3：客服系統 - TTS轉換與音檔生成"""
        logger.info("步驟 3/7: 客服系統處理...")

        result.update_step_status(TestStep.TTS_CONVERSION.value, 0.0)

        try:
            # 準備 TTS 轉換
            test_script = TestScript(content=script_content)
            result.update_step_status(TestStep.TTS_CONVERSION.value, 10.0)

            # 呼叫 TTS API 生成音檔
            logger.info("開始 TTS 轉換...")
            result.update_step_status(TestStep.TTS_CONVERSION.value, 20.0)

            tts_audio = await self.tts_service.generate_dialogue_audio(test_script)
            result.tts_audio = tts_audio

            # 儲存 TTS 生成資訊
            result.tts_generation_info = {
                "duration": tts_audio.duration,
                "file_size": tts_audio.file_size,
                "format": tts_audio.format,
                "generated_at": datetime.now().isoformat(),
                "dialogue_count": result.parsed_dialogue_count,
            }

            result.update_step_status(TestStep.TTS_CONVERSION.value, 100.0)
            result.complete_current_step()

            logger.info("步驟3完成：TTS 轉換，音檔時長: %.1f 秒", tts_audio.duration)

        except Exception as e:
            logger.error("步驟3失敗: %s", e)
            raise RuntimeError(f"客服系統處理失敗: {e}") from e

    async def _step4_recording(self, result: TestResult):
        """步驟4：錄音系統 - 模擬通話錄音過程"""
        logger.info("步驟 4/7: 錄音系統處理...")

        result.update_step_status(TestStep.RECORDING.value, 0.0)

        try:
            if not result.tts_audio:
                raise RuntimeError("TTS 音檔不存在，無法進行錄音模擬")

            result.update_step_status(TestStep.RECORDING.value, 20.0)

            # 模擬通話錄音（高保真度複製）
            logger.info("開始模擬錄音...")
            recorded_audio = self.cs_mock.simulate_call(result.tts_audio.file_path)
            result.recorded_audio = recorded_audio

            # 為了向後相容，同時設定 mock_response_audio
            result.mock_response_audio = recorded_audio

            # 儲存錄音資訊
            result.recording_info = {
                "source_audio_duration": result.tts_audio.duration,
                "recorded_audio_duration": recorded_audio.duration,
                "file_size": recorded_audio.file_size,
                "recording_quality": "high_fidelity",
                "recorded_at": datetime.now().isoformat(),
            }

            result.update_step_status(TestStep.RECORDING.value, 100.0)
            result.complete_current_step()

            logger.info(
                "步驟4完成：錄音系統，錄音檔時長: %.1f 秒", recorded_audio.duration
            )

        except Exception as e:
            logger.error("步驟4失敗: %s", e)
            raise RuntimeError(f"錄音系統處理失敗: {e}") from e

    async def _step5_storage(self, result: TestResult):
        """步驟5：音檔存放系統 - 音檔歸檔與管理"""
        logger.info("步驟 5/7: 音檔存放系統處理...")

        result.update_step_status(TestStep.STORAGE.value, 0.0)

        try:
            if not result.recorded_audio:
                raise RuntimeError("錄音檔不存在，無法進行存放")

            result.update_step_status(TestStep.STORAGE.value, 20.0)

            # 建立存放 metadata
            metadata = {
                "test_id": result.test_id,
                "type": "recorded_call",
                "duration": result.recorded_audio.duration,
                "created_at": datetime.now().isoformat(),
                "original_script_hash": result.script_validation_info.get(
                    "script_hash", ""
                ),
                "source_info": {
                    "tts_duration": (
                        result.tts_audio.duration if result.tts_audio else 0
                    ),
                    "dialogue_count": result.parsed_dialogue_count,
                },
            }

            result.update_step_status(TestStep.STORAGE.value, 50.0)

            # 存放到音檔系統
            logger.info("儲存錄音檔案...")
            file_id = self.storage_mock.store_audio(
                result.recorded_audio.file_path, metadata
            )
            result.storage_file_id = file_id

            # 儲存存放資訊
            result.storage_metadata = {
                "file_id": file_id,
                "stored_at": datetime.now().isoformat(),
                "storage_path": result.recorded_audio.file_path,
                "metadata": metadata,
            }

            result.update_step_status(TestStep.STORAGE.value, 100.0)
            result.complete_current_step()

            logger.info("步驟5完成：音檔存放，檔案 ID: %s", file_id)

        except Exception as e:
            logger.error("步驟5失敗: %s", e)
            raise RuntimeError(f"音檔存放系統處理失敗: {e}") from e

    async def _step6_llm_analysis(self, result: TestResult):
        """步驟6：LLM分析系統 - STT轉換與比對分析"""
        logger.info("步驟 6/7: LLM分析系統處理...")

        result.update_step_status(TestStep.LLM_ANALYSIS.value, 0.0)

        try:
            if not result.recorded_audio:
                raise RuntimeError("錄音檔不存在，無法進行分析")

            # === 第一階段：STT 轉錄 ===
            logger.info("開始 STT 轉錄...")
            result.stt_stage = "processing"
            result.update_step_status(TestStep.LLM_ANALYSIS.value, 10.0)

            transcribed_text, confidence = await self.stt_service.transcribe_audio(
                result.recorded_audio.file_path
            )

            result.transcribed_text = transcribed_text
            result.stt_confidence = confidence
            result.stt_stage = "completed"
            result.stt_info = {
                "transcribed_at": datetime.now().isoformat(),
                "confidence_score": confidence,
                "text_length": len(transcribed_text),
                "processing_duration": "auto",  # 可以記錄實際處理時間
            }

            result.update_step_status(TestStep.LLM_ANALYSIS.value, 50.0)
            logger.info("STT 轉錄完成")

            # === 第二階段：LLM 分析 ===
            logger.info("開始 LLM 分析...")
            result.llm_stage = "processing"
            result.update_step_status(TestStep.LLM_ANALYSIS.value, 60.0)

            if transcribed_text.strip():
                analysis = await self.llm_service.analyze_conversation(
                    result.original_script, transcribed_text
                )
                result.llm_analysis = analysis
                result.accuracy_score = analysis.get("accuracy_score", 0.0)
            else:
                logger.warning("轉錄文字為空，跳過 LLM 分析")
                result.llm_analysis = {
                    "accuracy_score": 0.0,
                    "summary": "轉錄文字為空，無法進行分析",
                    "key_differences": ["無法獲取轉錄內容"],
                    "suggestions": ["檢查音檔品質", "重新嘗試測試"],
                    "reasoning": "STT 轉錄失敗或音檔無內容",
                }
                result.accuracy_score = 0.0

            result.llm_stage = "completed"
            result.update_step_status(TestStep.LLM_ANALYSIS.value, 100.0)
            result.complete_current_step()

            logger.info("步驟6完成：LLM 分析，準確率: %.1f%%", result.accuracy_score)

        except Exception as e:
            logger.error("步驟6失敗: %s", e)
            raise RuntimeError(f"LLM分析系統處理失敗: {e}") from e

    async def _step7_completion(self, result: TestResult):
        """步驟7：系統結束 - 最終報告生成與資源清理"""
        logger.info("步驟 7/7: 系統結束處理...")

        result.update_step_status(TestStep.COMPLETION.value, 0.0)

        try:
            # 計算測試總時長
            total_duration = (datetime.now() - result.timestamp).total_seconds()

            # 生成最終測試報告
            result.final_report = {
                "test_summary": {
                    "test_id": result.test_id,
                    "total_duration_seconds": total_duration,
                    "accuracy_score": result.accuracy_score,
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                },
                "steps_completed": len(result.completed_steps),
                "file_info": {
                    "tts_audio_path": (
                        result.tts_audio.file_path if result.tts_audio else None
                    ),
                    "recorded_audio_path": (
                        result.recorded_audio.file_path
                        if result.recorded_audio
                        else None
                    ),
                    "storage_file_id": result.storage_file_id,
                },
                "analysis_results": {
                    "original_script_length": len(result.original_script),
                    "transcribed_text_length": len(result.transcribed_text),
                    "dialogue_count": result.parsed_dialogue_count,
                    "stt_confidence": result.stt_confidence,
                    "final_accuracy": result.accuracy_score,
                },
            }

            result.update_step_status(TestStep.COMPLETION.value, 40.0)

            # 清理暫存檔案
            logger.info("清理暫存檔案...")
            cleanup_count = await self._cleanup_temp_files(result)

            result.cleanup_info = {
                "cleaned_files": cleanup_count,
                "cleanup_at": datetime.now().isoformat(),
                "retention_policy": "keep_final_results",
            }

            result.update_step_status(TestStep.COMPLETION.value, 70.0)

            # 保存測試記錄
            await self._save_test_record(result)

            result.update_step_status(TestStep.COMPLETION.value, 100.0)
            result.complete_current_step()

            logger.info("步驟7完成：系統結束，測試總時長: %.1f 秒", total_duration)

        except Exception as e:
            logger.error("步驟7失敗: %s", e)
            raise RuntimeError(f"系統結束處理失敗: {e}") from e

    async def _cleanup_temp_files(self, result: TestResult) -> int:
        """清理暫存檔案"""
        cleanup_count = 0
        try:
            # 模擬使用 result
            _ = result
            cleanup_count = 0
            logger.info("暫存檔案清理完成")

        except FileNotFoundError as e:
            logger.warning("清理暫存檔案時發生檔案未找到錯誤: %s", e)
        except OSError as e:
            logger.warning("清理暫存檔案時發生系統錯誤: %s", e)

        return cleanup_count

    async def _save_test_record(self, result: TestResult):
        """保存測試記錄到持久化存儲"""
        try:
            # 模擬使用 result
            logger.info("測試記錄已保存: %s", result.test_id)

        except OSError as e:
            logger.warning("保存測試記錄時發生系統錯誤: %s", e)
        except ValueError as e:
            logger.warning("保存測試記錄時發生值錯誤: %s", e)

    async def get_service_status(self) -> Dict[str, bool]:
        """檢查所有服務的狀態"""
        status = {}

        try:
            status["tts (yating)"] = await self.tts_service.test_connection()
        except httpx.RequestError as e:
            logger.warning("TTS 服務狀態檢查失敗（請求錯誤）: %s", e)
            status["tts (yating)"] = False
        except httpx.HTTPStatusError as e:
            logger.warning("TTS 服務狀態檢查失敗（HTTP 錯誤）: %s", e)
            status["tts (yating)"] = False

        try:
            status["stt (gpt-4o-transcribe)"] = await self.stt_service.test_connection()
        except httpx.RequestError as e:
            logger.warning("STT 服務狀態檢查失敗（請求錯誤）: %s", e)
            status["stt (gpt-4o-transcribe)"] = False
        except httpx.HTTPStatusError as e:
            logger.warning("STT 服務狀態檢查失敗（HTTP 錯誤）: %s", e)
            status["stt (gpt-4o-transcribe)"] = False

        try:
            status["llm (gpt-4o)"] = await self.llm_service.test_connection()
        except httpx.RequestError as e:
            logger.warning("LLM 服務狀態檢查失敗（請求錯誤）: %s", e)
            status["llm (gpt-4o)"] = False
        except httpx.HTTPStatusError as e:
            logger.warning("LLM 服務狀態檢查失敗（HTTP 錯誤）: %s", e)
            status["llm (gpt-4o)"] = False

        return status

        # Mock 服務總是可用
        # status["mock_cs"] = True
        # status["mock_storage"] = True

        # return status
