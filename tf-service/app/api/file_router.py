import cv2
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
import logging

router = APIRouter()
logger = logging.getLogger("tf_main")

# 업로드 디렉토리 절대 경로로 설정
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"파일 업로드 디렉토리: {UPLOAD_DIR}")

@router.get("/mosaic")
async def mosaic_file():
    girl = './data/girl.jpg'
    cascade = './data/haarcascade_frontalface_alt.xml'
    cascade = cv2.CascadeClassifier(cascade)
    img = cv2.imread(girl)
    face = cascade.detectMultiScale(img, minSize=(150,150))
    if len(face) == 0:
        print('얼굴인식 실패')
        quit()
    for(x,y,w,h) in face:
        print(f'얼굴의 좌표 = {x}, {y}, {w}, {h}')
        red = (0,0,255)
        cv2.rectangle(img, (x, y), (x+w, y+h), red, thickness=20)
    cv2.imwrite('./saved_data/girl-face.png',img)
    cv2.imshow('./saved_data/girl-face',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

@router.post("/upload")
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