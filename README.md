# 自動化測試錄音功能系統 (AudioTestAutomation)

本專案為一套基於 Web 的自動化錄音功能測試系統。系統旨在提供一個端到端的自動化測試流程，透過文字轉語音 (TTS)、語音轉文字 (STT) 及大型語言模型 (LLM) 對模擬的客服對話進行深度分析，並生成量化的準確率報告。

## 目錄

- [1. 專案目標](#1-專案目標)
- [2. 應用場景](#2-應用場景)
- [3. 核心功能](#3-核心功能)
- [4. 系統部署與啟動](#4-系統部署與啟動)
- [5. 系統架構](#5-系統架構)
- [6. 模組結構詳解](#6-模組結構詳解)

## 1. 專案目標

傳統上驗證客服或電話系統的錄音品質，往往需要大量的人工聽取與比對，過程耗時且缺乏客觀標準。本專案旨在解決此問題，達成以下目標：

- **端到端自動化**：從對話腳本生成到最終的品質分析，建立一個無需人工干預的完整測試流程。
- **語意層面分析**：利用大型語言模型 (LLM) 評估轉錄內容與原始腳本的語意相似度，超越傳統的字面比對。
- **量化評估報告**：提供包含準確率分數、分析摘要、主要差異點及改進建議的量化與質化報告。
- **靈活配置**：系統設計具有彈性，可透過環境變數輕鬆切換 STT 和 LLM 模型，以進行效能比較。

## 2. 應用場景

本系統的核心應用場景是**客服系統的自動化品質監控**，旨在解決傳統人工抽樣聽取錄音所面臨的效率低、成本高及標準不一的問題。

在現代客服中心，電話或線上通話的錄音是確保服務品質、解決客訴及符合法規的關鍵環節。本系統可被整合至日常維運流程中，達成以下目的：

- **自動化回歸測試**：當客服系統的底層架構、錄音模組或轉碼元件進行更新時，可自動執行一系列標準化的測試腳本，確保核心的錄音功能未因改動而產生品質衰退 (Regression)。
- **客觀的量化指標**：取代傳統主觀的人工判斷，系統透過 STT 轉錄與 LLM 語意比對，提供一個穩定且客觀的準確率分數，作為衡量錄音品質的關鍵績效指標 (KPI)。
- **提升測試覆蓋率**：相較於人工抽樣只能覆蓋極少數的通話，自動化測試能夠以更高頻率、更廣泛地對系統進行驗證，及早發現因高併發、特定語句或異常流程所導致的錄音問題。

## 3. 核心功能

- **視覺化 Web 操作介面**：提供一個互動式網頁，使用者可直接貼上對話腳本、啟動測試並即時查看結果。
- **七步驟自動化測試流程**：內建一個包含腳本解析、環境檢查、TTS 生成、模擬錄音、音檔儲存、AI 分析到報告生成的完整測試管線。
- **可配置的 AI 模型**：可透過 `.env` 設定檔輕鬆切換 STT 與 LLM 模型，無需修改任何程式碼。
- **整合多種 AI 服務**：
  - **TTS**: Yating (雅婷)
  - **STT**: OpenAI (`whisper-1`, `gpt-4o-transcribe`)
  - **LLM**: OpenAI (`gpt-4o`, `gpt-4o-mini`)
- **非同步後端處理**：後端採用 FastAPI，測試流程在背景任務中執行，確保使用者介面在測試進行中依然保持流暢。
- **完整的自動化測試**：專案包含單元測試與整合測試 (`pytest`)，確保程式碼的穩定與可靠。

## 4. 系統部署與啟動

### 前置需求

- Python 3.8 或更高版本
- `git` 版本控制工具

### 部署步驟

#### 步驟 1: 取得原始碼

```bash
git clone https://github.com/Kun-2000/AudioTestAutomation.git
cd AudioTestAutomation
```

#### 步驟 2: 建立並啟用 Python 虛擬環境

為確保依賴套件隔離，建議使用虛擬環境。

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

#### 步驟 3: 安裝依賴套件

專案所需之套件皆定義於 `requirements.txt`。

```bash
pip install -r requirements.txt
```

#### 步驟 4: 設定環境變數

複製 `.env.example` 檔案為 `.env`，並填入您的 API 金鑰。

```bash
cp .env.example .env
```

接著編輯 `.env` 檔案：

```env
# .env

# [必要] 填入您的 OpenAI API 金鑰
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# [必要] 填入您的 Yating TTS API 金鑰
YATING_API_KEY="your-yating-api-key"

# [可選] 覆蓋預設模型或其他設定
STT_MODEL=whisper-1
LLM_MODEL=gpt-4o-mini
```

#### 步驟 5: 啟動應用程式

```bash
python main.py
```

應用程式成功啟動後，即可透過瀏覽器訪問 `http://127.0.0.1:8000`。

## 5. 系統架構

本系統採用前後端分離的設計模式，後端遵循服務導向架構 (Service-Oriented Architecture)，確保模組之間的高內聚與低耦合。

### 運作流程 (Workflow)

1. **前端使用者介面 (Frontend UI - `index.html`)**：使用者在網頁上輸入對話腳本並啟動測試。前端透過 Fetch API 向後端發送非同步請求。

2. **API 路由層 (API Routes - `api/routes.py`)**：FastAPI 應用接收到請求，驗證輸入後，將測試任務交由背景處理，並立即回傳一個測試 ID 給前端。

3. **核心編排器 (Orchestrator - `services/test_orchestrator.py`)**：`TestOrchestrator` 類別作為核心協調者，依序調用 TTS、STT、LLM 等服務，執行完整的七步驟測試管線。

4. **狀態輪詢與結果渲染**：前端定期向後端 API 輪詢測試狀態。測試完成後，前端獲取完整的 JSON 報告，並動態地將準確率、分析摘要、音檔等結果渲染到頁面上。

## 6. 模組結構詳解

```
AudioTestAutomation/
├── api/                  # API 路由與 FastAPI 應用主體
│   ├── app.py            # FastAPI 應用實例與設定
│   └── routes.py         # 定義所有 API 端點
├── config/               # 設定檔
│   └── settings.py       # 從 .env 讀取並管理所有設定
├── mock/                 # 模擬服務，用於模擬錄音與儲存
│   ├── audio_storage.py
│   └── customer_service.py
├── models/               # Pydantic/Dataclass 資料模型
│   └── test_models.py    # 定義 TestResult, TestStep 等核心資料結構
├── services/             # 核心商業邏輯層
│   ├── llm_service.py    # 封裝 LLM 分析服務
│   ├── stt_service.py    # 封裝 STT 轉錄服務
│   ├── test_orchestrator.py # 核心編排器，串接七步驟流程
│   └── tts_service.py    # 封裝 TTS 生成服務
├── storage/              # (自動生成) 存放音檔、日誌等
├── tests/                # 自動化測試腳本
│   ├── test_basic.py     # 單元測試
│   └── test_integration.py # 整合測試
├── utils/                # 共用工具函式
│   └── audio_utils.py    # 音檔處理相關函式
├── web/                  # 前端網頁
│   └── templates/
│       └── index.html    # 系統主頁面
├── .env.example          # 環境變數設定範本
├── main.py               # 專案啟動入口
└── requirements.txt      # Python 依賴套件清單
```
