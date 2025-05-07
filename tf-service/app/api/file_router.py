from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import logging
import os
import matplotlib.pyplot as plt
from tensorflow import keras
import numpy as np
import shutil
from PIL import Image
from app.domain.controller.file_controller import process_upload_file
from app.domain.model.file_schema import UploadResponse

router = APIRouter()
logger = logging.getLogger("tf_main")

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    이미지 파일을 업로드하고, 얼굴 인식 후 모자이크 처리
    
    - **file**: 업로드할 이미지 파일
    
    **Returns**:
    - **filename**: 업로드된 파일명
    - **message**: 처리 결과 메시지
    - **original_path**: 원본 이미지 저장 경로
    - **mosaic_path**: 모자이크 처리된 이미지 저장 경로 (처리된 경우)
    - **faces_detected**: 감지된 얼굴 수
    """
    result = await process_upload_file(file)
    
    # 정상 처리된 경우 200 OK 응답
    if "실패" not in result.message and "오류" not in result.message:
        return result
    
    # 오류 발생 시 500 Internal Server Error 응답
    if "파일 저장 실패" in result.message:
        return JSONResponse(content=result.dict(), status_code=500)
    
    # 파일 업로드는 성공했지만 모자이크 처리 실패 시 200 OK (부분 성공)
    return result

@router.get("/mnist-sample")
async def get_mnist_sample():
    """
    MNIST 데이터셋에서 100번째 이미지를 반환합니다.
    이미지는 mnist 디렉토리에 mnist_sample.png 파일로 저장되고, 레이블은 JSON으로 반환됩니다.
    
    **Returns**:
    - **label**: 이미지의 레이블 (숫자 0-9)
    - **image_path**: 저장된 이미지 파일 경로
    """
    try:
        # MNIST 데이터셋 로드
        mnist = keras.datasets.mnist
        (train_images, train_labels), (_, _) = mnist.load_data()
        
        # 100번째 이미지 선택
        mnist_idx = 100
        image = train_images[mnist_idx]
        label = int(train_labels[mnist_idx])
        
        # 이미지 파일 저장 경로 설정
        mnist_dir = "/mnist"
        os.makedirs(mnist_dir, exist_ok=True)
        image_path = os.path.join(mnist_dir, "mnist_sample.png")
        
        # Matplotlib을 사용하여 이미지 저장
        plt.figure(figsize=(5, 5))
        plt.imshow(image, cmap='gray')
        plt.axis('off')  # 축 제거
        plt.savefig(image_path, bbox_inches='tight', pad_inches=0)
        plt.close()
        
        logger.info(f"MNIST 샘플 이미지(인덱스: {mnist_idx}, 레이블: {label})가 {image_path}에 저장되었습니다.")
        
        # 응답 반환
        return {
            "label": label,
            "image_path": image_path
        }
    
    except Exception as e:
        logger.error(f"MNIST 샘플 이미지 생성 오류: {str(e)}")
        return JSONResponse(
            content={"error": f"MNIST 샘플 이미지 생성 중 오류 발생: {str(e)}"},
            status_code=500
        )

@router.post("/upload-handwritten")
async def upload_handwritten(file: UploadFile = File(...)):
    """
    손글씨 숫자 이미지를 업로드하고 분류합니다.
    
    - **file**: 업로드할 손글씨 숫자 이미지
    
    **Returns**:
    - **predicted_digit**: 예측된 숫자 (0-9)
    - **confidence**: 예측 확률 (0-1)
    """
    try:
        # mnist 디렉토리 생성
        mnist_dir = "/mnist"
        os.makedirs(mnist_dir, exist_ok=True)
        
        # 파일 저장
        file_path = os.path.join(mnist_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"손글씨 이미지 업로드 완료: {file_path}")
        
        # 이미지 전처리
        # 1. 이미지 로드 및 그레이스케일 변환
        img = Image.open(file_path).convert('L')
        
        # 2. 28x28 크기로 리사이즈
        img = img.resize((28, 28), Image.LANCZOS)
        
        # 3. 이미지를 NumPy 배열로 변환 (0-255)
        img_array = np.array(img)
        
        # 4. 255로 나누어 정규화 (0-1)
        img_array = img_array / 255.0
        
        # 5. 모델 입력 형태로 변환 (1, 28, 28)
        img_array = img_array.reshape(1, 28, 28)
        
        # MNIST 모델 로드
        model_path = os.path.join(os.getcwd(), "app", "models", "my_mnist_model.h5")
        
        # 모델 경로가 존재하지 않을 경우 대체 경로 시도
        if not os.path.exists(model_path):
            model_path = "/app/models/my_mnist_model.h5"
            if not os.path.exists(model_path):
                logger.warning(f"모델 파일을 찾을 수 없습니다: {model_path}")
                return JSONResponse(
                    content={"error": "MNIST 모델 파일을 찾을 수 없습니다."},
                    status_code=500
                )
        
        # 모델 로드
        model = keras.models.load_model(model_path)
        logger.info(f"MNIST 모델 로드 완료: {model_path}")
        
        # 예측
        predictions = model.predict(img_array)
        predicted_digit = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_digit])
        
        logger.info(f"손글씨 숫자 예측 결과: {predicted_digit} (확률: {confidence:.4f})")
        
        # 결과 반환
        return {
            "predicted_digit": int(predicted_digit),
            "confidence": confidence,
            "file_path": file_path
        }
    
    except Exception as e:
        logger.error(f"손글씨 분류 중 오류 발생: {str(e)}")
        return JSONResponse(
            content={"error": f"손글씨 분류 중 오류 발생: {str(e)}"},
            status_code=500
        )