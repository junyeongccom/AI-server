from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
import logging

app = APIRouter()
logger = logging.getLogger("tf_main")

# 업로드 디렉토리 절대 경로로 설정
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"파일 업로드 디렉토리: {UPLOAD_DIR}")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    logger.info(f"파일 업로드 시작: {file.filename}, 저장 위치: {file_location}")
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"파일 업로드 성공: {file.filename}")
        
        # 파일 존재 여부 확인 및 로그 기록
        if os.path.exists(file_location):
            file_size = os.path.getsize(file_location)
            logger.info(f"파일 저장 확인: {file_location}, 크기: {file_size} bytes")
        else:
            logger.error(f"파일이 저장되지 않음: {file_location}")
            
        return JSONResponse(content={"filename": file.filename, "message": "파일 업로드 성공!", "path": file_location})
    except Exception as e:
        logger.error(f"파일 업로드 실패: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)