import logging
from app.domain.service.mosaic import process_upload_and_mosaic
from app.domain.model.file_schema import UploadResponse


logger = logging.getLogger("tf_main")

async def process_upload_file(file):
    """
    파일 업로드 및 모자이크 처리를 위한 컨트롤러 함수
    서비스 레이어를 호출하여 작업을 위임합니다.
    
    Args:
        file: UploadFile 객체
        
    Returns:
        UploadResponse: 처리 결과
    """
    logger.info(f"파일 '{file.filename}' 업로드 및 모자이크 처리 요청 수신")
    
    # 서비스 레이어 호출
    result = await process_upload_and_mosaic(file)
    
    logger.info(f"파일 '{file.filename}' 처리 완료: {result.message}")
    return result
