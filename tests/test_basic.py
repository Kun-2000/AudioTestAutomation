"""
基本單元測試檔案
"""

from pathlib import Path
import sys
import shutil
import pytest
from models.test_models import TestScript, SpeakerRole
from utils.audio_utils import create_silence
from config.settings import settings
from mock.customer_service import CustomerServiceMock
from mock.audio_storage import AudioStorageMock

# 添加專案根目錄到 Python 搜尋路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 定義測試音檔路徑
SAMPLE_AUDIO_PATH = project_root / "tests" / "test.mp3"


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


class TestMockServices:
    """測試 Mock 服務"""

    def test_customer_service_mock(self):
        """測試客服系統 Mock"""
        # 如果測試音檔不存在，則跳過此測試
        if not SAMPLE_AUDIO_PATH.exists():
            pytest.skip(f"測試音檔 {SAMPLE_AUDIO_PATH} 不存在，跳過此測試。")

        cs_mock = CustomerServiceMock()
        result_audio_file = cs_mock.simulate_call(str(SAMPLE_AUDIO_PATH))

        # 驗證檔案已複製且內容相同
        result_path = Path(result_audio_file.file_path)
        assert result_path.exists()
        assert result_path.name != SAMPLE_AUDIO_PATH.name
        assert result_path.read_bytes() == SAMPLE_AUDIO_PATH.read_bytes()

    def test_audio_storage_mock(self, tmp_path):
        """測試音檔存放 Mock"""
        if not SAMPLE_AUDIO_PATH.exists():
            pytest.skip(f"測試音檔 {SAMPLE_AUDIO_PATH} 不存在，跳過此測試。")

        # 複製音檔到 pytest 的臨時目錄中進行測試
        source_file = tmp_path / "test.mp3"
        shutil.copy2(SAMPLE_AUDIO_PATH, source_file)

        storage_mock = AudioStorageMock()
        file_id = storage_mock.store_audio(str(source_file), {"test": "data"})

        # 驗證儲存、讀取及統計功能
        assert file_id in storage_mock.audio_metadata
        retrieved_file = storage_mock.retrieve_audio(file_id)
        assert retrieved_file is not None
        assert Path(retrieved_file.file_path).exists()
        assert storage_mock.get_storage_stats()["total_files"] == 1


class TestConfiguration:
    """測試配置"""

    def test_storage_paths_exist(self):
        """測試存儲路徑是否被正確創建"""
        assert settings.STORAGE_PATH.exists()
        assert settings.AUDIO_PATH.exists()
        assert settings.TEMP_PATH.exists()
