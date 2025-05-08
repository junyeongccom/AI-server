from typing import Dict, Any, Tuple, List, Union, Callable
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

    async def _send_json_or_content(self, request_method: Callable, url: str, headers: Dict[str, str], 
                                   json: Any = None, body: Any = None):
        """
        JSON 또는 일반 콘텐츠를 전송하는 내부 헬퍼 메서드입니다.
        
        Args:
            request_method: 요청 메서드 (client.post, client.put 등)
            url: 요청 URL
            headers: 요청 헤더
            json: JSON 데이터 (선택적)
            body: 본문 데이터 (선택적)
            
        Returns:
            요청 응답 객체
        """
        if json is not None:
            return await request_method(url, headers=headers, json=json)
        elif body:
            if isinstance(body, str):
                try:
                    json_data = json_module.loads(body)
                    return await request_method(url, headers=headers, json=json_data)
                except json_module.JSONDecodeError:
                    return await request_method(url, headers=headers, content=body)
            else:
                return await request_method(url, headers=headers, json=body)
        else:
            return await request_method(url, headers=headers)

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
        """
        HTTP 요청을 보내는 메서드입니다.
        
        Args:
            method: HTTP 메서드 ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
            path: 요청 경로
            headers: 요청 헤더 (선택적)
            body: 본문 데이터 (선택적)
            files: 업로드할 파일 (선택적)
            form_data: 폼 데이터 (선택적)
            json: JSON 데이터 (선택적)
            
        Returns:
            요청 응답 객체
        """
        # URL 준비
        url = f"{self.base_url}/{path}" if not path.startswith("http") else path
        logger.info(f"요청 URL: {url}")

        # 요청 헤더 준비
        request_headers = {}
        if headers:
            # headers가 list 타입이면 dict로 변환
            if isinstance(headers, list):
                headers = {k.decode(): v.decode() for k, v in headers}
            
            # 필터링된 헤더 생성
            for k, v in headers.items():
                if k.lower() not in ['host', 'content-length']:
                    request_headers[k] = v

        # 타임아웃 설정
        timeout = httpx.Timeout(30.0)
        
        # HTTP 메서드 맵핑
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # HTTP 메서드 맵핑 딕셔너리
                method_map = {
                    'POST': client.post,
                    'GET': client.get,
                    'PUT': client.put,
                    'DELETE': client.delete,
                    'PATCH': client.patch
                }
                
                # 요청 메서드 선택
                request_method = method_map.get(method.upper())
                if not request_method:
                    error_msg = f"지원하지 않는 HTTP 메서드: {method}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=error_msg
                    )
                
                # POST 메서드의 파일 업로드 특수 처리
                if method.upper() == 'POST' and files:
                    logger.info(f"POST 파일 업로드 요청 전송: {url}")
                    form_data = form_data or None  # 빈 dict 방지
                    response = await client.post(
                        url,
                        headers=request_headers,
                        files=files,
                        data=form_data
                    )
                # 일반 요청 처리 (JSON 또는 콘텐츠)
                else:
                    if method.upper() == 'POST':
                        log_msg = "POST JSON 요청 전송"
                        if json is not None:
                            log_msg += "(직접 json 파라미터 사용)"
                        logger.info(f"{log_msg}: {url}")
                    
                    response = await self._send_json_or_content(
                        request_method=request_method,
                        url=url,
                        headers=request_headers,
                        json=json,
                        body=body
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