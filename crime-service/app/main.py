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

from app.api.crime_router import router as crime_api_router

# ✅ 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crime_api")

# ✅ 환경변수 로드
load_dotenv()

# ✅ 요청 모델 정의
class CrimeRequest(BaseModel):
    data: Dict[str, Any]

# ✅ 라이프스팬 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀🚀🚀 Crime Service가 시작됩니다.")
    yield
    print("🛑 Crime Service가 종료됩니다.")

# ✅ FastAPI 설정
app = FastAPI(
    title="Crime Service API",
    description="Crime Service API for jinmini.com",
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
crime_router = APIRouter(prefix="/crime", tags=["Finance API"])

# ✅ 서브 라우터와 엔드포인트를 연결함
app.include_router(crime_api_router, prefix="/crime")


# ✅ 서브 라우터 등록
app.include_router(crime_router)

