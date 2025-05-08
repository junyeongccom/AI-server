import os
import shutil
import logging
from fastapi import UploadFile
from tensorflow import keras

logger = logging.getLogger("tf_main")

async def save_uploaded_file(file: UploadFile, file_path: str) -> str:
    """
    업로드된 파일을 지정된 경로에 저장합니다.
    
    Args:
        file: 업로드된 파일 객체
        file_path: 저장할 파일 경로
    
    Returns:
        저장된 파일 경로
    """
    # 디렉토리 경로 확인 및 생성
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    
    # 파일 저장
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"파일 저장 성공: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        raise RuntimeError(f"파일 저장 중 오류 발생: {str(e)}")

def load_mnist_model(model_path: str):
    """
    지정된 경로에서 MNIST 모델을 로드합니다.
    
    Args:
        model_path: 모델 파일 경로
    
    Returns:
        로드된 Keras 모델
    """
    try:
        # 모델 경로 확인
        if not os.path.exists(model_path):
            logger.error(f"모델 파일을 찾을 수 없습니다: {model_path}")
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
        
        # 모델 로드
        model = keras.models.load_model(model_path)
        logger.info(f"MNIST 모델 로드 완료: {model_path}")
        return model
    except Exception as e:
        logger.error(f"모델 로드 중 오류 발생: {str(e)}")
        raise RuntimeError(f"모델 로드 중 오류 발생: {str(e)}") 