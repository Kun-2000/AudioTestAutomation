"""
客服測試系統主程式入口
"""

import logging
import sys
from pathlib import Path
import uvicorn
from config.settings import settings
from api.app import app
from api.routes import router

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.STORAGE_PATH / "app.log"),
    ],
)

logger = logging.getLogger(__name__)

# 註冊路由
app.include_router(router)


def validate_environment():
    """驗證環境設定"""
    try:
        settings.validate_config()
        logger.info("環境設定驗證通過")
        return True
    except ValueError as e:
        logger.error("環境設定錯誤: %s", e)
        return False


def print_startup_info():
    """顯示啟動資訊"""
    print("\n" + "=" * 60)
    print("🚀 客服測試系統")
    print("=" * 60)
    print(f"📊 TTS: Yating TTS ({settings.YATING_TTS_MODEL_CUSTOMER})")
    print(f"🎤 STT: OpenAI ({settings.STT_MODEL})")
    print(f"🤖 LLM: OpenAI ({settings.LLM_MODEL})")
    print(f"💾 存儲路徑: {settings.STORAGE_PATH}")
    print("🌐 Web 介面: http://localhost:8000")
    print("📚 API 文件: http://localhost:8000/docs")
    print("=" * 60 + "\n")


def cleanup_temp_files():
    """清理臨時檔案"""
    try:
        temp_folder = settings.TEMP_PATH
        cleanup_count = 0

        if temp_folder.exists():
            for file_path in temp_folder.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        cleanup_count += 1
                    except OSError:
                        pass

        if cleanup_count > 0:
            logger.info("清理了 %d 個臨時檔案", cleanup_count)

    except FileNotFoundError as e:
        logger.warning("臨時檔案目錄不存在: %s", e)
    except PermissionError as e:
        logger.warning("清理臨時檔案失敗（權限錯誤）: %s", e)
    except OSError as e:
        logger.warning("清理臨時檔案失敗（系統錯誤）: %s", e)


if __name__ == "__main__":
    try:
        # 驗證環境
        if not validate_environment():
            print("\n❌ 環境設定不正確，請檢查 .env 檔案")
            print("必要設定：")
            print("  - OPENAI_API_KEY")
            print("  - YATING_API_KEY")
            sys.exit(1)

        # 清理臨時檔案
        cleanup_temp_files()

        # 顯示啟動資訊
        print_startup_info()

        # 啟動服務
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            access_log=True,
            log_level="info" if not settings.DEBUG else "debug",
        )

    except KeyboardInterrupt:
        logger.info("系統已停止")
        print("\n👋 客服測試系統已停止")

    except ValueError as e:
        logger.error("系統啟動失敗（值錯誤）: %s", e)
        print(f"\n💥 啟動失敗（值錯誤）: {e}")
        print("\n🔧 請檢查：")
        print("  1. Python 環境和依賴套件")
        print("  2. API 金鑰設定")
        print("  3. 網路連線狀態")
        sys.exit(1)

    except OSError as e:
        logger.error("系統啟動失敗（系統錯誤）: %s", e)
        print(f"\n💥 啟動失敗（系統錯誤）: {e}")
        print("\n🔧 請檢查：")
        print("  1. 檔案系統權限")
        print("  2. 網路連線狀態")
        sys.exit(1)

    except RuntimeError as e:
        logger.error("系統啟動失敗（執行錯誤）: %s", e)
        print(f"\n💥 啟動失敗（執行錯誤）: {e}")
        print("\n🔧 請檢查：")
        print("  1. 依賴套件版本")
        print("  2. 系統資源限制")
        sys.exit(1)
