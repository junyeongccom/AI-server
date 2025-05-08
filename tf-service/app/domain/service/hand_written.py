import os
import logging
import numpy as np
from PIL import Image
from fastapi import UploadFile
from app.domain.repository.handwritten_repository import save_uploaded_file, load_mnist_model
from app.domain.model.file_schema import HandwrittenPredictionResponse

logger = logging.getLogger("tf_main")

async def process_handwritten_image(file: UploadFile) -> HandwrittenPredictionResponse:
    """
    손글씨 이미지를 처리하고 분류하는 서비스
    
    Args:
        file: 업로드된 손글씨 이미지 파일
    
    Returns:
        HandwrittenPredictionResponse: 예측 결과
    """
    # MNIST 디렉토리 및 파일 경로 설정
    mnist_dir = "/mnist"
    file_path = os.path.join(mnist_dir, file.filename)
    
    # 파일 저장 (Repository 호출)
    await save_uploaded_file(file, file_path)
    
    # 이미지 전처리
    img_array = preprocess_image(file_path)
    
    # 모델 경로 설정
    model_path = os.path.join(os.getcwd(), "app", "models", "my_mnist_model.h5")
    alt_model_path = "/app/models/my_mnist_model.h5"
    
    try:
        # 모델 로드 시도 (Repository 호출)
        model = load_mnist_model(model_path)
    except FileNotFoundError:
        # 대체 경로 시도
        logger.info(f"대체 모델 경로로 시도: {alt_model_path}")
        model = load_mnist_model(alt_model_path)
    
    # 모델 예측 수행
    predictions = model.predict(img_array)
    predicted_digit = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_digit])
    
    logger.info(f"손글씨 숫자 예측 결과: {predicted_digit} (확률: {confidence:.4f})")
    
    # 응답 모델 생성 및 반환
    return HandwrittenPredictionResponse(
        predicted_digit=int(predicted_digit),
        confidence=confidence,
        file_path=file_path
    )

def preprocess_image(file_path: str) -> np.ndarray:
    """
    이미지를 MNIST 모델 입력에 적합한 형태로 전처리
    
    Args:
        file_path: 이미지 파일 경로
    
    Returns:
        np.ndarray: 전처리된 이미지 배열
    """
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
    
    return img_array
