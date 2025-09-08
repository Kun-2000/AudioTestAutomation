"""
LLM 服務模組 - 使用 OpenAI GPT 進行對話品質分析 (非同步版本)
"""

import json
import logging
import re
from typing import Dict, Any
from openai import AsyncOpenAI, APIError

from config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """OpenAI GPT LLM 服務"""

    def __init__(self):
        """初始化 LLM 服務"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API Key 未設定")
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.LLM_MODEL
            logger.info("LLM 服務 (非同步) 初始化成功，使用模型: %s", self.model)
        except Exception as e:
            logger.error("LLM 服務初始化失敗: %s", e)
            raise

    async def analyze_conversation(
        self, original_script: str, transcribed_text: str
    ) -> Dict[str, Any]:
        """分析原始腳本與轉錄文字的對話品質 (非同步版本)"""
        try:
            if not original_script.strip():
                raise ValueError("原始腳本不能為空")

            if not transcribed_text.strip():
                raise ValueError("轉錄文字不能為空")

            normalized_original = self._normalize_text(original_script)
            normalized_transcribed = self._normalize_text(transcribed_text)

            logger.info("開始進行對話品質分析...")

            prompt = self._build_analysis_prompt(
                normalized_original, normalized_transcribed
            )
            response = await self._call_gpt_api(prompt)
            analysis = self._parse_analysis_response(response)

            logger.info("分析完成 - 準確率: %.1f%%", analysis.get("accuracy_score", 0))
            return analysis
        except Exception as e:
            logger.error("對話品質分析失敗: %s", e)
            raise RuntimeError(f"LLM 分析錯誤: {e}") from e

    def _normalize_text(self, text: str) -> str:
        """文字正規化處理"""
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text.strip())
        text = text.replace("，", ",").replace("。", ".")
        text = text.replace("？", "?").replace("！", "!")
        text = text.replace("：", ":").replace("；", ";")
        text = re.sub(
            r"^(客戶|客服|customer|agent)\s*[：:]\s*",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        return text.strip()

    def _build_analysis_prompt(self, original: str, transcribed: str) -> str:
        """建構分析提示詞"""
        return f"""你是專業的客服對話品質分析師。請比較以下原始腳本與實際轉錄文字，分析客服對話的品質。

【重要前提】
輸入的文本都已經移除了「客戶:」和「客服:」等角色標識，請專注於對話內容本身的比對，不要將角色標識的缺失視為一個錯誤或差異。

【原始腳本】
{original}

【轉錄文字】
{transcribed}

請以 JSON 格式回傳分析結果，包含以下欄位：
- "accuracy_score": 準確率分數 (0-100)，代表轉錄文字在語意上與原始腳本的貼近程度。
- "summary": 根據比對結果，生成一句話的簡潔摘要。例如：「轉錄文字與原始腳本非常接近，語義完全一致。」
- "key_differences": 簡潔地列出兩者之間的主要差異點。如果沒有差異，請回傳空列表。
- "suggestions": 根據差異點，提供具體的改進建議。如果沒有差異，請回傳空列表。
- "reasoning": 解釋你為什麼給出這個準確率分數和摘要。

請只回傳 JSON 格式的分析結果："""

    async def _call_gpt_api(self, prompt: str, retry_count: int = 0) -> str:
        """呼叫 GPT API (非同步版本)"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是專業的客服對話品質分析師，擅長分析語音轉錄品質和客服服務品質。請提供準確、客觀的分析結果。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
                top_p=0.9,
                response_format={"type": "json_object"},  # 確保輸出為 JSON
            )
            return response.choices[0].message.content.strip()
        except APIError as e:
            if retry_count < 2:
                logger.warning(
                    "GPT API 呼叫失敗，重試中 (%d/2): %s", retry_count + 1, e
                )
                return await self._call_gpt_api(prompt, retry_count + 1)
            logger.error("GPT API 呼叫失敗: %s", e)
            raise RuntimeError("OpenAI API 錯誤: {e}") from e

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """解析 GPT 回應"""
        try:
            result = json.loads(response_text.strip())
            default_result = {
                "accuracy_score": 0.0,
                "summary": "分析完成",
                "key_differences": [],
                "suggestions": [],
                "reasoning": "",
            }
            for key, default_value in default_result.items():
                result.setdefault(key, default_value)
            result["accuracy_score"] = max(0, min(100, float(result["accuracy_score"])))
            return result
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning("JSON 解析失敗: %s", e)
            logger.warning("原始回應: %s", response_text)
            return {
                "accuracy_score": 0.0,
                "summary": "分析過程發生錯誤",
                "key_differences": [],
                "suggestions": ["檢查輸入資料", "重新嘗試分析"],
                "reasoning": f"無法解析分析結果: {str(e)}",
            }

    async def test_connection(self) -> bool:
        """測試 OpenAI GPT 連接 (非同步版本)"""
        try:
            logger.info("測試 OpenAI GPT (%s) 連接...", self.model)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "回答'測試成功'"}],
                max_tokens=10,
            )
            result = response.choices[0].message.content.strip()
            return bool(result)
        except APIError as e:
            logger.error("OpenAI API 錯誤: %s", e)
            return False
        except ValueError as e:
            logger.error("值錯誤: %s", e)
            return False
        except (ConnectionError, TimeoutError) as e:
            logger.error("連接或超時錯誤: %s", e)
            return False
