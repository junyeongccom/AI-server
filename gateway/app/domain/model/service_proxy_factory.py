from typing import Dict, Any, Tuple, List, Union
from fastapi import HTTPException, status
import httpx
import logging
import json as json_module
from app.domain.model.service_type import SERVICE_URLS, ServiceType

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service_proxy")

class ServiceProxyFactory:
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        self.base_url = SERVICE_URLS.get(service_type)

        if not self.base_url:
            error_msg = f"서비스 URL을 찾을 수 없습니다: {service_type}"
            logger.error(error_msg)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

        logger.info(f"서비스 프록시 생성: {service_type} → {self.base_url}")

    async def request(
        self,
        method: str,
        path: str,
        headers: Union[List[Tuple[bytes, bytes]], Dict[str, str]] = None,
        body: Any = None,
        files: Dict[str, Tuple[str, bytes, str]] = None,
        form_data: Dict[str, str] = None,
        json: Any = None
    ):
        url = f"{self.base_url}/{path}" if not path.startswith("http") else path
        logger.info(f"요청 URL: {url}")

        request_headers = {}
        if headers:
            # headers가 list 타입이면 dict로 변환
            if isinstance(headers, list):
                headers = {k.decode(): v.decode() for k, v in headers}
            
            # 필터링된 헤더 생성
            for k, v in headers.items():
                if k.lower() not in ['host', 'content-length']:
                    request_headers[k] = v

        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == 'POST':
                    if files:
                        logger.info(f"POST 파일 업로드 요청 전송: {url}")
                        form_data = form_data or None  # ✅ 빈 dict 방지
                        response = await client.post(
                            url,
                            headers=request_headers,
                            files=files,
                            data=form_data
                        )
                    elif json is not None:
                        logger.info(f"POST JSON 요청 전송(직접 json 파라미터 사용): {url}")
                        response = await client.post(
                            url,
                            headers=request_headers,
                            json=json
                        )
                    else:
                        logger.info(f"POST JSON 요청 전송: {url}")
                        json_data = None
                        if body:
                            if isinstance(body, str):
                                try:
                                    json_data = json_module.loads(body)
                                except json_module.JSONDecodeError:
                                    response = await client.post(url, headers=request_headers, content=body)
                                    return response
                            else:
                                json_data = body

                            response = await client.post(url, headers=request_headers, json=json_data)
                        else:
                            response = await client.post(url, headers=request_headers)

                elif method.upper() == 'GET':
                    response = await client.get(url, headers=request_headers)

                elif method.upper() == 'PUT':
                    if json is not None:
                        response = await client.put(url, headers=request_headers, json=json)
                    else:
                        response = await client.put(url, headers=request_headers, content=body)

                elif method.upper() == 'DELETE':
                    if json is not None:
                        response = await client.delete(url, headers=request_headers, json=json)
                    else:
                        response = await client.delete(url, headers=request_headers, content=body)

                elif method.upper() == 'PATCH':
                    if json is not None:
                        response = await client.patch(url, headers=request_headers, json=json)
                    else:
                        response = await client.patch(url, headers=request_headers, content=body)

                else:
                    error_msg = f"지원하지 않는 HTTP 메서드: {method}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=error_msg
                    )

                logger.info(f"응답 상태 코드: {response.status_code}")
                return response

            except httpx.RequestError as e:
                error_msg = f"요청 중 오류 발생: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )