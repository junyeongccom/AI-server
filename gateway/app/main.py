from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any, Literal
import os
from dotenv import load_dotenv
import logging
import sys
from contextlib import asynccontextmanager
import json
from pydantic import BaseModel
import traceback

from app.domain.model.service_proxy_factory import ServiceProxyFactory
from app.domain.model.service_type import ServiceType

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
        logger.info(f"📥 GET 요청: 서비스={service.value}, 경로={path}")
        factory = ServiceProxyFactory(service_type=service)
        response = await factory.request(
            method="GET",
            path=path,
            headers=request.headers.raw
        )
        
        if response.status_code == 200:
            try:
                # JSON 응답 처리
                json_content = response.json()
                logger.info(f"✅ JSON 응답 반환: {json_content}")
                return JSONResponse(content=json_content, status_code=response.status_code)
            except Exception as json_error:
                # JSON이 아닌 응답 처리
                logger.warning(f"⚠️ JSON이 아닌 응답: {str(json_error)}")
                return JSONResponse(
                    content={"message": "성공", "raw_response": response.text[:1000]},
                    status_code=200
                )
        else:
            error_msg = f"⚠️ 서비스 오류: HTTP {response.status_code}"
            logger.error(error_msg)
            logger.error(f"📄 응답 내용: {response.text}")
            return JSONResponse(
                content={"detail": error_msg, "response": response.text},
                status_code=response.status_code
            )
    except Exception as e:
        error_msg = f"❌ 게이트웨이 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"detail": error_msg},
            status_code=500
        )

# POST
@gateway_router.post("/{service}/{path:path}", summary="POST 프록시")
async def proxy_post(
    service: ServiceType, 
    path: str, 
    request_body: FinanceRequest,
    request: Request
):
    print(f"🌈Received request for service: {service}, path: {path}")
    factory = ServiceProxyFactory(service_type=service)
    body = request_body.model_dump_json()
    print(f"Request body: {body}")
    response = await factory.request(
        method="POST",
        path=path,
        headers=request.headers.raw,
        body=body
    )
    if response.status_code == 200:
        try:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except json.JSONDecodeError:
            # 응답이 JSON이 아닌 경우
            return JSONResponse(
                content={"detail": "⚠️Invalid JSON response from service"},
                status_code=500
            )
    else:
        # 에러 응답 처리
        return JSONResponse(
            content={"detail": f"Service error: {response.text}"},
            status_code=response.status_code
        )

# PUT
@gateway_router.put("/{service}/{path:path}", summary="PUT 프록시")
async def proxy_put(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="PUT",
        path=path,
        headers=request.headers.raw,
        body=await request.body()
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)

# DELETE
@gateway_router.delete("/{service}/{path:path}", summary="DELETE 프록시")
async def proxy_delete(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="DELETE",
        path=f"{service}/{path}",
        headers=request.headers.raw,
        body=await request.body()
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)

# PATCH
@gateway_router.patch("/{service}/{path:path}", summary="PATCH 프록시")
async def proxy_patch(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="PATCH",
        path=path,
        headers=request.headers.raw,
        body=await request.body()
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)

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