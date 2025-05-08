from fastapi import FastAPI, APIRouter, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import logging
import sys
from contextlib import asynccontextmanager
import json
from pydantic import BaseModel
from app.domain.model.service_proxy_factory import ServiceProxyFactory
from app.domain.model.service_type import ServiceType
from app.domain.service.request_service import handle_request, process_response

# ✅ 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway_api")

# ✅ 환경변수 로드
# Load environment variables from .env file
load_dotenv()



# ✅ 요청 모델 정의
class FinanceRequest(BaseModel):
    data: Dict[str, Any]


# ✅ 라이프스팬 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀🚀🚀 FastAPI 앱이 시작됩니다.")
    yield
    print("🛑 FastAPI 앱이 종료됩니다.")

# ✅ FastAPI 설정
app = FastAPI(
    title="Gateway API",
    description="Gateway API for jinmini.com",
    version="0.1.0",
    lifespan=lifespan
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 메인 라우터 생성
gateway_router = APIRouter(prefix="/ai/v1", tags=["Gateway API"])

# ✅ 메인 라우터 실행
# GET
@gateway_router.get("/{service}/{path:path}", summary="GET 프록시")
async def proxy_get(
    service: ServiceType, 
    path: str, 
    request: Request
):
    try:
        response = await handle_request(service, path, request, "GET")
        return process_response(response)
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# 통합 POST 요청 처리 (JSON 또는 파일 업로드)
@gateway_router.post(
    "/{service}/{path:path}", 
    summary="통합 POST 프록시 (JSON 또는 파일 업로드)", 
    description="하나의 엔드포인트에서 JSON 요청과 파일 업로드를 모두 처리합니다."
)
async def proxy_post(
    service: ServiceType, 
    path: str,
    request: Request,
    file: UploadFile = File(None, description="업로드할 파일 (선택 사항)"),
    json_data: Optional[str] = Form(None, description="JSON 형식의 데이터 (선택 사항)")
):
    try:
        response = await handle_request(service, path, request, "POST", json_data, file)
        return process_response(response)
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# PUT
@gateway_router.put("/{service}/{path:path}", summary="PUT 프록시")
async def proxy_put(service: ServiceType, path: str, request: Request):
    try:
        response = await handle_request(service, path, request, "PUT")
        return process_response(response)
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# DELETE
@gateway_router.delete("/{service}/{path:path}", summary="DELETE 프록시")
async def proxy_delete(service: ServiceType, path: str, request: Request):
    try:
        response = await handle_request(service, path, request, "DELETE")
        return process_response(response)
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# PATCH
@gateway_router.patch("/{service}/{path:path}", summary="PATCH 프록시")
async def proxy_patch(service: ServiceType, path: str, request: Request):
    try:
        response = await handle_request(service, path, request, "PATCH")
        return process_response(response)
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# ✅ 메인 라우터 등록
app.include_router(gateway_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    ) 