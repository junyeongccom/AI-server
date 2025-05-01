from typing import Optional
from fastapi import HTTPException
import httpx
import logging
import traceback
from app.domain.model.service_type import SERVICE_URLS, ServiceType

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service_proxy")

class ServiceProxyFactory:
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        self.base_url = SERVICE_URLS[service_type]
        logger.info(f"👩🏻 ServiceProxyFactory 생성: 서비스={service_type.value}, URL={self.base_url}")

    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[list[tuple[bytes, bytes]]] = None,
        body: Optional[bytes] = None
    ) -> httpx.Response:
        # NLP 서비스의 요청 URL 구성
        if self.service_type == ServiceType.NLP:
            # 이미 prefix가 포함되어 있다면 제거 (중복 방지)
            if path.startswith("nlp/"):
                path = path[4:]  # "nlp/" 부분 제거
                
            url = f"{self.base_url}/nlp/{path}"
            logger.info(f"🔄 NLP 서비스 URL 구성: {url} (원본 경로: {path})")
        else:
            url = f"{self.base_url}/{self.service_type.value}/{path}"
            
        logger.info(f"🎯 요청 URL: {url}, 메서드: {method}")
        
        # 헤더 설정 (필요 시 외부 헤더 병합 가능)
        headers_dict = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"📡 HTTP 요청 실행: {method} {url}")
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers_dict,
                    content=body
                )
                logger.info(f"📥 응답 수신: 상태 코드={response.status_code}")
                
                # 응답 본문 출력 (디버깅용)
                if response.status_code == 200:
                    logger.info(f"✅ 요청 성공: {method} {url}")
                    try:
                        # JSON 응답인지 확인
                        json_response = response.json()
                        logger.info(f"📊 JSON 응답: {json_response}")
                    except Exception as json_err:
                        logger.warning(f"⚠️ JSON이 아닌 응답: {response.text[:100]}...")
                else:
                    logger.error(f"❌ 요청 실패: 상태 코드={response.status_code}")
                    logger.error(f"📄 응답 내용: {response.text}")
                
                return response
            except Exception as e:
                error_msg = f"❌ 요청 실패: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=str(e))
