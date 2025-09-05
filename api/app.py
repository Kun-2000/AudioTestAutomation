"""
FastAPI 應用程式主檔案
"""

import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles  # 引入 StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path

from config.settings import settings
from api.routes import router  # 引入路由

# 設定日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 創建 FastAPI 應用程式
app = FastAPI(
    title="客服測試系統",
    description="使用 TTS、STT、LLM 的客服對話品質測試系統",
    version="1.0.0",
    debug=settings.DEBUG,
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 新增部分：掛載靜態檔案目錄 ---
# 這會讓 storage 資料夾下的所有檔案，可以透過 /storage/... 的網址被存取
storage_path = Path(__file__).parent.parent / "storage"
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")

# 設定模板引擎
templates = Jinja2Templates(directory="web/templates")

# 註冊 API 路由
app.include_router(router)


# 首頁路由
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首頁"""
    return templates.TemplateResponse("index.html", {"request": request})


# 健康檢查
@app.get("/health")
async def health_check():
    """系統健康檢查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {"api": True, "storage": True},
    }
