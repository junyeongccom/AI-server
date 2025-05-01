"""
삼성 리포트 테스트를 위한 API 모듈입니다.
"""
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
import os
from app.domain.service.samsung_report import SamsungReport

# FastAPI 인스턴스 생성
app = FastAPI(
    title="NLP Test API",
    description="삼성 리포트 테스트를 위한 API",
    version="0.1.0",
)

# 라우터 생성
router = APIRouter(tags=["테스트"])

@router.get("/test", summary="테스트 엔드포인트", description="테스트용 메시지를 반환합니다.")
async def test_endpoint():
    """
    테스트 엔드포인트입니다.
    
    Returns:
        dict: 테스트 메시지를 포함한 JSON 응답
    """
    return {"message": "테스트 파일입니다"}

@router.get("/generate-wordcloud", 
          summary="워드클라우드 생성", 
          description="삼성 보고서 데이터를 분석하여 워드클라우드를 생성합니다.")
async def generate_wordcloud():
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
    try:
        # SamsungReport 클래스 인스턴스 생성
        report_analyzer = SamsungReport()
        
        # 전체 프로세스 실행 (워드클라우드 생성까지)
        result = report_analyzer.process_all()
        
        # 결과 확인
        if result:
            # 컨테이너 내부 경로 사용
            container_path = result["container_path"] if isinstance(result, dict) else result
            
            # 상대 경로로 변환 (절대 경로에서)
            if os.path.isabs(container_path):
                rel_path = os.path.relpath(container_path)
            else:
                rel_path = container_path
                
            return {
                "message": "워드클라우드 생성 완료",
                "output_path": rel_path,
                "local_path": result.get("local_path") if isinstance(result, dict) else None
            }
        else:
            return {
                "message": "워드클라우드 생성 실패",
                "error": "프로세스 실행 중 오류가 발생했습니다."
            }
    except Exception as e:
        return {
            "message": "워드클라우드 생성 실패",
            "error": str(e)
        }

# 라우터 등록
app.include_router(router)

# OpenAPI 스키마 커스터마이징
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ----- 테스트 코드 (pytest + async) -----
# 테스트 코드는 pytest 실행 시에만 임포트되도록 조건부 임포트 처리
# Docker 환경에서 실행 시 pytest 관련 코드는 무시됨
try:
    import pytest
    from httpx import AsyncClient
    
    # 테스트 코드는 실제 실행환경(Docker 등)에서는 실행되지 않도록 처리
    if __name__ != "__main__" and "pytest" in globals():
        @pytest.fixture
        async def async_client():
            """비동기 테스트 클라이언트를 반환하는 pytest fixture입니다."""
            async with AsyncClient(app=app, base_url="http://test") as client:
                yield client

        @pytest.mark.asyncio
        async def test_read_test_endpoint(async_client):
            """
            /test 엔드포인트를 비동기적으로 테스트합니다.
            
            Args:
                async_client: 비동기 테스트 클라이언트 fixture
            """
            response = await async_client.get("/test")
            assert response.status_code == 200
            assert response.json() == {"message": "테스트 파일입니다"}

        @pytest.mark.asyncio
        async def test_openapi_schema():
            """
            OpenAPI 스키마가 올바르게 생성되는지 테스트합니다.
            """
            schema = app.openapi()
            assert schema["info"]["title"] == "NLP Test API"
            assert schema["info"]["version"] == "0.1.0"
            
            # /test 엔드포인트가 스키마에 포함되어 있는지 확인
            paths = schema.get("paths", {})
            assert "/test" in paths
            assert "get" in paths["/test"]
except ImportError:
    # pytest나 httpx가 설치되지 않은 환경(예: Docker)에서는 테스트 코드를 로드하지 않음
    pass
