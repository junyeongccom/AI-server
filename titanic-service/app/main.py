from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any
import os
from dotenv import load_dotenv
import logging
import sys
from contextlib import asynccontextmanager
import json
from pydantic import BaseModel

from app.api.titanic_router import router as titanic_api_router

# ✅ 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("titanic_api")

# ✅ 환경변수 로드
load_dotenv()

# ✅ 요청 모델 정의
class TitanicRequest(BaseModel):
    data: Dict[str, Any]

# ✅ 라이프스팬 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀🚀🚀 Titanic Service가 시작됩니다.")
    yield
    print("🛑 Titanic Service가 종료됩니다.")

# ✅ FastAPI 설정
app = FastAPI(
    title="Titanic Service API",
    description="Titanic Service API for jinmini.com",
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

# ✅ 서브 라우터 생성
titanic_router = APIRouter(prefix="/titanic", tags=["Titanic Service"])

# ✅ 서브 라우터와 엔드포인트를 연결함
app.include_router(titanic_api_router, prefix="/titanic")

# ✅ 서브 라우터 등록
app.include_router(titanic_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9001,
        reload=True
    )
