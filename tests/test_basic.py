"""
基本單元測試檔案
"""

import pytest
import asyncio
from unittest.mock import patch
from pathlib import Path
import sys

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.test_models import TestScript, SpeakerRole
from utils.audio_utils import create_silence, combine_audio_segments
from config.settings import settings


class TestModels:
    """測試資料模型"""

    def test_test_script_parse_content(self):
        """測試腳本解析功能"""
        script_content = "客戶: 您好\n客服: 您好"
        script = TestScript(content=script_content)
        lines = script.parse_content()
        assert len(lines) == 2
        assert lines[0].speaker == SpeakerRole.CUSTOMER
        assert lines[0].text == "您好"


class TestAudioUtils:
    """測試音檔工具"""

    def test_create_silence(self):
        """測試靜音生成"""
        silence_data = create_silence(0.1)
        assert isinstance(silence_data, bytes)
        assert len(silence_data) > 0


# --- 修正後的 Mock 服務測試 ---
class TestMockServices:
    """測試 Mock 服務"""

    def test_customer_service_mock(self, tmp_path):
        """測試客服系統 Mock (修正版)"""
        # 1. 準備一個假的來源音檔
        source_file = tmp_path / "source.mp3"
        source_content = b"dummy_audio_content"
        source_file.write_bytes(source_content)

        from mock.customer_service import CustomerServiceMock

        cs_mock = CustomerServiceMock()

        # 2. 執行模擬通話
        result_audio_file = cs_mock.simulate_call(str(source_file))

        # 3. 驗證結果
        result_path = Path(result_audio_file.file_path)
        assert result_path.exists()
        assert result_path.name != source_file.name  # 檔名應該是新的
        assert result_path.read_bytes() == source_content  # 內容應該完全相同

    def test_audio_storage_mock(self, tmp_path):
        """測試音檔存放 Mock"""
        # 1. 準備假檔案
        source_file = tmp_path / "test.mp3"
        source_file.touch()

        from mock.audio_storage import AudioStorageMock

        storage_mock = AudioStorageMock()
        file_id = storage_mock.store_audio(str(source_file), {"test": "data"})

        # 2. 驗證儲存和讀取
        assert file_id in storage_mock.audio_metadata
        retrieved_file = storage_mock.retrieve_audio(file_id)
        assert retrieved_file is not None
        assert Path(retrieved_file.file_path).exists()

        # 3. 驗證統計資訊
        stats = storage_mock.get_storage_stats()
        assert stats["total_files"] == 1


class TestConfiguration:
    """測試配置"""

    def test_storage_paths_exist(self):
        """測試存儲路徑被正確創建"""
        assert settings.STORAGE_PATH.exists()
        assert settings.AUDIO_PATH.exists()
        assert settings.TEMP_PATH.exists()
