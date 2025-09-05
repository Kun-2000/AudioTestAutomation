"""
API 路由定義
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from services.test_orchestrator import TestOrchestrator
from models.test_models import TestResult, TestStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["客服測試"])

test_orchestrator = None
try:
    test_orchestrator = TestOrchestrator()
except Exception as e:
    logger.error(f"測試編排器初始化失敗: {e}")

# 儲存測試結果的字典
test_results: Dict[str, TestResult] = {}


class TestRequest(BaseModel):
    """測試請求模型"""

    script: str


class TestResponse(BaseModel):
    """測試回應模型"""

    test_id: str
    status: str
    message: str


@router.post("/test/start", response_model=TestResponse)
async def start_test(request: TestRequest, background_tasks: BackgroundTasks):
    """開始執行客服測試"""
    try:
        if not test_orchestrator:
            raise HTTPException(status_code=503, detail="測試系統尚未就緒，請稍後再試")

        if not request.script.strip():
            raise HTTPException(status_code=400, detail="測試腳本不能為空")

        # 創建唯一的 TestResult 物件
        result = TestResult(original_script=request.script)
        test_results[result.test_id] = result

        # 將整個 result 物件傳遞給背景任務
        background_tasks.add_task(run_test_async, result)

        logger.info(f"測試已開始，ID: {result.test_id}")
        return TestResponse(
            test_id=result.test_id, status="running", message="測試已開始執行"
        )
    except Exception as e:
        logger.error(f"開始測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"系統錯誤: {str(e)}")


@router.get("/test/{test_id}/status")
async def get_test_status(test_id: str) -> Dict[str, Any]:
    """查詢測試狀態"""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="找不到指定的測試")
    result = test_results[test_id]
    return {
        "test_id": result.test_id,
        "status": result.status.value,
        "timestamp": result.timestamp.isoformat(),
        "accuracy_score": result.accuracy_score,
        "error_message": result.error_message,
    }


@router.get("/test/{test_id}/result")
async def get_test_result(test_id: str) -> Dict[str, Any]:
    """獲取完整測試結果"""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="找不到指定的測試")
    return test_results[test_id].to_dict()


@router.get("/test/{test_id}/report")
async def get_test_report(test_id: str) -> Dict[str, Any]:
    """獲取測試報告"""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="找不到指定的測試")
    result = test_results[test_id]

    if result.status not in [TestStatus.COMPLETED, TestStatus.FAILED]:
        return {
            "test_id": test_id,
            "status": result.status.value,
            "message": "測試仍在進行中...",
        }

    if result.status == TestStatus.FAILED:
        return {
            "test_id": test_id,
            "status": result.status.value,
            "message": "測試執行失敗",
            "error": result.error_message,
        }

    analysis = result.llm_analysis
    accuracy = result.accuracy_score
    grade = "需要改進"
    if accuracy >= 90:
        grade = "優秀"
    elif accuracy >= 80:
        grade = "良好"
    elif accuracy >= 70:
        grade = "普通"

    return {
        "test_id": test_id,
        "accuracy_score": accuracy,
        "grade": grade,
        "summary": analysis.get("summary", ""),
        "key_differences": analysis.get("key_differences", []),
        "suggestions": analysis.get("suggestions", []),
        "original_script": result.original_script,
        "transcribed_text": result.transcribed_text,
        "timestamp": result.timestamp.isoformat(),
    }


@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """獲取系統狀態"""
    if not test_orchestrator:
        return {"status": "error", "message": "測試系統未就緒", "services": {}}
    service_status = await test_orchestrator.get_service_status()
    all_services_ok = all(service_status.values())
    return {
        "status": "healthy" if all_services_ok else "partial",
        "services": service_status,
        "message": "所有服務正常" if all_services_ok else "部分服務異常",
    }


@router.get("/tests/list")
async def list_tests(limit: int = 10) -> Dict[str, Any]:
    """列出最近的測試記錄"""
    sorted_tests = sorted(
        test_results.values(), key=lambda r: r.timestamp, reverse=True
    )
    test_list = [
        {
            "test_id": result.test_id,
            "status": result.status.value,
            "accuracy_score": result.accuracy_score,
            "timestamp": result.timestamp.isoformat(),
            "script_preview": (
                result.original_script[:50] + "..."
                if len(result.original_script) > 50
                else result.original_script
            ),
        }
        for result in sorted_tests[:limit]
    ]
    return {"tests": test_list, "total": len(test_results)}


async def run_test_async(result: TestResult):
    """在背景執行測試的異步函數"""
    try:
        logger.info(f"開始執行背景測試: {result.test_id}")
        await test_orchestrator.run_full_test(result)
        logger.info(f"背景測試完成: {result.test_id}")
    except Exception as e:
        logger.error(f"背景測試失敗 ({result.test_id}): {e}")
        result.status = TestStatus.FAILED
        result.error_message = str(e)
