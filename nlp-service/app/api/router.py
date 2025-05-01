from fastapi import APIRouter, HTTPException, Request
import logging
import traceback
from app.domain.controller.wordcloud_controller import WordCloudController

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nlp_api")

# 라우터 생성
router = APIRouter(
    prefix="",
    tags=["워드클라우드"]
)

@router.get(
    "/generate-wordcloud", 
    summary="워드클라우드 생성", 
    description="삼성 보고서 데이터를 분석하여 워드클라우드를 생성합니다."
)
async def generate_wordcloud(request: Request):
    """
    삼성 보고서 텍스트를 분석하여 워드클라우드를 생성합니다.
    
    프로세스:
    1. 텍스트 파일 읽기 (kr-Report_2018.txt)
    2. 한글만 추출
    3. 토큰화
    4. 명사 추출
    5. 불용어 제거
    6. 빈도 계산
    7. 워드클라우드 생성
    
    Returns:
        dict: 워드클라우드 생성 결과와 저장 경로를 포함한 JSON 응답
    """
    logger.info(f"📥 요청 수신: {request.method} {request.url.path}")
    logger.info(f"📍 클라이언트: {request.client.host}:{request.client.port}")
    logger.info(f"🔍 헤더: {dict(request.headers)}")
    
    try:
        logger.info("🔄 WordCloudController 생성 및 워드클라우드 생성 요청")
        controller = WordCloudController()
        result = await controller.generate_wordcloud()
        
        logger.info(f"📤 응답 반환: {result}")
        return result
    except Exception as e:
        error_msg = f"❌ 워드클라우드 생성 중 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(f"🔥 예외 발생: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "워드클라우드 생성 실패",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        ) 