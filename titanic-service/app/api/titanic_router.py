from fastapi import APIRouter, Request
import logging
from app.domain.controller.titanic_controller import TitanicController

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 로거 설정
logger = logging.getLogger("titanic_router")
logger.setLevel(logging.INFO)
router = APIRouter()

# GET
@router.get("/passengers", summary="모든 타이타닉 승객 목록 조회")
async def get_all_passengers():
    """
    등록된 모든 타이타닉 승객의 목록을 조회합니다.
    """
    print("📋 모든 타이타닉 승객 목록 조회")
    logger.info("📋 모든 타이타닉 승객 목록 조회")
    
    # 샘플 데이터
    passengers = [
        {"id": 1, "name": "John Smith", "age": 30, "survived": True},
        {"id": 2, "name": "Jane Doe", "age": 25, "survived": False},
        {"id": 3, "name": "Robert Brown", "age": 45, "survived": True}
    ]
    return {"passengers": passengers}

# POST
@router.post("/passengers", summary="승객 정보로 생존 여부 예측")
async def predict_survival(
    
    
):
    print(f"🕞🕞🕞🕞🕞🕞predict_survival 호출 - 승객: ")
    logger.info(f"🕞🕞🕞🕞🕞🕞predict_survival 호출 - 승객: ")
    controller = TitanicController()
    return await controller.predict_survival()

# PUT
@router.put("/passengers", summary="승객 정보 전체 수정")
async def update_passenger(request: Request):
    print("📝 승객 정보 전체 수정")
    logger.info("📝 승객 정보 전체 수정")
    
    # 샘플 응답
    return {
        "message": "승객 정보가 성공적으로 수정되었습니다.",
        "updated_data": {
            "name": "Updated John Smith",
            "age": 35,
            "survived": True
        }
    }

# DELETE
@router.delete("/passengers", summary="승객 정보 삭제")
async def delete_passenger():
    """
    승객 정보를 삭제합니다.
    """
    print("🗑️ 승객 정보 삭제")
    logger.info("🗑️ 승객 정보 삭제")
    
    # 샘플 응답
    return {
        "message": "승객 정보가 성공적으로 삭제되었습니다."
    }

# PATCH
@router.patch("/passengers", summary="승객 정보 부분 수정")
async def patch_passenger(request: Request):
    """
    승객 정보를 부분적으로 수정합니다.
    """
    print("✏️ 승객 정보 부분 수정")
    logger.info("✏️ 승객 정보 부분 수정")
    
    # 샘플 응답
    return {
        "message": "승객 정보가 부분적으로 수정되었습니다.",
        "updated_fields": {
            "name": "Patched John Smith"
        }
    }
