import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
import logging
import traceback

router = APIRouter()
logger = logging.getLogger("tf_main")

# 업로드 디렉토리 절대 경로로 설정
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"파일 업로드 디렉토리: {UPLOAD_DIR}")

# 캐스케이드 파일 경로 설정
CASCADE_PATH = os.path.join(os.getcwd(), "app", "data", "haarcascade_frontalface_alt.xml")
if not os.path.exists(CASCADE_PATH):
    # 대체 경로 시도
    CASCADE_PATH = os.path.join(os.getcwd(), "data", "haarcascade_frontalface_alt.xml")
    
if os.path.exists(CASCADE_PATH):
    logger.info(f"얼굴 인식 캐스케이드 파일 발견: {CASCADE_PATH}")
else:
    logger.warning(f"얼굴 인식 캐스케이드 파일이 없습니다. 얼굴 모자이크 기능이 작동하지 않을 수 있습니다.")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    logger.info(f"파일 업로드 시작: {file.filename}, 저장 위치: {file_location}")
    
    try:
        # 원본 파일 저장
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"파일 업로드 성공: {file.filename}")
        
        # 파일 존재 여부 확인 및 로그 기록
        if os.path.exists(file_location):
            file_size = os.path.getsize(file_location)
            logger.info(f"파일 저장 확인: {file_location}, 크기: {file_size} bytes")
        else:
            logger.error(f"파일이 저장되지 않음: {file_location}")
            return JSONResponse(content={"error": "파일 저장 실패"}, status_code=500)
        
        # 얼굴 인식 캐스케이드 파일 있는 경우 모자이크 처리
        if os.path.exists(CASCADE_PATH):
            logger.info("얼굴 모자이크 처리 시작")
            
            try:
                # 파일 이름과 확장자 분리
                filename, extension = os.path.splitext(file.filename)
                mosaic_file_location = os.path.join(UPLOAD_DIR, f"{filename}_mosaic{extension}")
                
                # 얼굴 감지 및 모자이크 처리
                result = mosaic_faces(file_location, mosaic_file_location)
                
                if result["success"]:
                    return JSONResponse(content={
                        "filename": file.filename,
                        "message": "파일 업로드 및 얼굴 모자이크 처리 성공",
                        "original_path": file_location,
                        "mosaic_path": mosaic_file_location,
                        "faces_detected": result["faces_detected"]
                    })
                else:
                    return JSONResponse(content={
                        "filename": file.filename,
                        "message": f"파일 업로드 성공, 모자이크 처리 실패: {result['error']}",
                        "path": file_location
                    })
            except Exception as e:
                logger.error(f"얼굴 모자이크 처리 오류: {str(e)}")
                logger.error(traceback.format_exc())
                return JSONResponse(content={
                    "filename": file.filename,
                    "message": "파일 업로드 성공, 모자이크 처리 중 오류 발생",
                    "error": str(e),
                    "path": file_location
                })
        else:
            # 캐스케이드 파일이 없는 경우
            logger.warning("얼굴 인식 캐스케이드 파일이 없어 얼굴 모자이크 처리를 건너뜁니다.")
                
            return JSONResponse(content={
                "filename": file.filename, 
                "message": "파일 업로드 성공! (얼굴 모자이크 기능 비활성화됨)", 
                "path": file_location
            })
            
    except Exception as e:
        logger.error(f"파일 업로드 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

def mosaic_faces(input_path, output_path, mosaic_size=15):
    """
    이미지에서 얼굴을 감지하고 모자이크 처리
    
    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 이미지 경로
        mosaic_size: 모자이크 블록 크기
        
    Returns:
        dict: 처리 결과 정보
    """
    try:
        # 이미지 파일 확인
        if not os.path.exists(input_path):
            return {"success": False, "error": f"입력 이미지 파일이 없습니다: {input_path}", "faces_detected": 0}
            
        # 얼굴 인식 모델 로드
        face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
        
        # 이미지 읽기
        img = cv2.imread(input_path)
        if img is None:
            return {"success": False, "error": f"이미지를 읽을 수 없습니다: {input_path}", "faces_detected": 0}
            
        # 얼굴 인식
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        
        # 감지된 얼굴 수
        faces_detected = len(faces)
        logger.info(f"감지된 얼굴 수: {faces_detected}")
        
        if faces_detected == 0:
            # 얼굴이 감지되지 않은 경우 원본 이미지 복사
            cv2.imwrite(output_path, img)
            return {"success": True, "error": "감지된 얼굴이 없습니다", "faces_detected": 0}
        
        # 이미지 복사본 생성
        result_img = img.copy()
        
        # 각 얼굴에 모자이크 적용
        for (x, y, w, h) in faces:
            # 얼굴 영역 잘라내기
            face_img = img[y:y+h, x:x+w]
            
            # 모자이크 처리
            face_img = cv2.resize(face_img, (mosaic_size, mosaic_size), interpolation=cv2.INTER_LINEAR)
            face_img = cv2.resize(face_img, (w, h), interpolation=cv2.INTER_NEAREST)
            
            # 모자이크된 얼굴 적용
            result_img[y:y+h, x:x+w] = face_img
            
            # 얼굴 주변에 사각형 그리기
            # cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        # 결과 이미지 저장
        cv2.imwrite(output_path, result_img)
        
        return {
            "success": True,
            "error": "",
            "faces_detected": faces_detected
        }
        
    except Exception as e:
        logger.error(f"모자이크 처리 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "faces_detected": 0}