import os
import logging
import traceback
from app.domain.service.samsung_report import SamsungReport

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("wordcloud_controller")

class WordCloudController:
    """워드클라우드 컨트롤러"""
    
    async def generate_wordcloud(self):
        """
        워드클라우드 생성 메서드
        
        Returns:
            dict: 워드클라우드 생성 결과와 경로 정보
        """
        logger.info("🎯 워드클라우드 컨트롤러: 생성 요청 시작")
        try:
            # SamsungReport 클래스 인스턴스 생성
            logger.info("🔄 SamsungReport 인스턴스 생성")
            report_analyzer = SamsungReport()
            
            # 전체 프로세스 실행 (워드클라우드 생성까지)
            logger.info("🚀 워드클라우드 생성 프로세스 시작")
            result = report_analyzer.process_all()
            
            # 결과 확인
            if result:
                logger.info("✅ 워드클라우드 생성 성공")
                
                # 컨테이너 내부 경로 사용
                container_path = result["container_path"] if isinstance(result, dict) else result
                
                # 상대 경로로 변환 (절대 경로에서)
                if os.path.isabs(container_path):
                    rel_path = os.path.relpath(container_path)
                else:
                    rel_path = container_path
                    
                logger.info(f"📊 결과 반환: 출력 경로={rel_path}")
                return {
                    "message": "워드클라우드 생성 완료",
                    "output_path": rel_path,
                    "local_path": result.get("local_path") if isinstance(result, dict) else None
                }
            else:
                logger.error("❌ 워드클라우드 생성 실패: 결과가 없습니다")
                return {
                    "message": "워드클라우드 생성 실패",
                    "error": "프로세스 실행 중 오류가 발생했습니다."
                }
        except Exception as e:
            error_msg = f"❌ 워드클라우드 생성 중 예외 발생: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "message": "워드클라우드 생성 실패",
                "error": str(e),
                "traceback": traceback.format_exc()
            } 