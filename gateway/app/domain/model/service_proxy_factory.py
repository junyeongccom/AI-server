from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status
import httpx
import logging
import traceback
import os
import json
from app.domain.model.service_type import SERVICE_URLS, ServiceType

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service_proxy")

class ServiceProxyFactory:
    def __init__(self, service_type: ServiceType):
        """서비스 프록시 팩토리 초기화

        Args:
            service_type (ServiceType): 서비스 타입 (TITANIC, CRIME, NLP, TF 등)
        """
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
        headers: Dict[str, str] = None,
        body: Any = None,
        files: Dict[str, Tuple[str, bytes, str]] = None,
        form_data: Dict[str, str] = None
    ):
        """HTTP 요청을 대상 서비스로 전달

        Args:
            method (str): HTTP 메서드 (GET, POST, PUT, DELETE, PATCH)
            path (str): 요청 경로
            headers (Dict[str, str], optional): HTTP 헤더. 기본값은 None.
            body (Any, optional): 요청 바디. 기본값은 None.
            files (Dict[str, Tuple[str, bytes, str]], optional): 업로드할 파일. 기본값은 None.
            form_data (Dict[str, str], optional): 폼 데이터. 기본값은 None.

        Returns:
            httpx.Response: 대상 서비스의 응답
        """
        url = f"{self.base_url}/{path}" if not path.startswith("http") else path
        logger.info(f"요청 URL: {url}")
        
        # 요청 헤더 설정
        request_headers = {}
        if headers:
            for k, v in headers:
                # 호스트 헤더 제외 (URL에 맞게 자동으로 설정됨)
                if k.decode('utf-8').lower() != 'host':
                    request_headers[k.decode('utf-8')] = v.decode('utf-8')
        
        # JSON 페이로드 또는 폼 데이터로 요청 전송
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == 'GET':
                    logger.info(f"GET 요청 전송: {url}")
                    response = await client.get(url, headers=request_headers)
                
                elif method.upper() == 'POST':
                    if files:
                        # 파일 업로드 요청인 경우
                        logger.info(f"POST 파일 업로드 요청 전송: {url}")
                        response = await client.post(
                            url, 
                            headers=request_headers,
                            files=files,
                            data=form_data
                        )
                    else:
                        # JSON 요청인 경우
                        logger.info(f"POST JSON 요청 전송: {url}")
                        # 바디가 문자열인지 확인하여 JSON 처리
                        json_data = None
                        if body:
                            if isinstance(body, str):
                                try:
                                    json_data = json.loads(body)
                                except json.JSONDecodeError:
                                    # JSON 파싱 실패 시 데이터로 전송
                                    response = await client.post(url, headers=request_headers, content=body)
                                    return response
                            else:
                                json_data = body
                            
                            response = await client.post(url, headers=request_headers, json=json_data)
                        else:
                            response = await client.post(url, headers=request_headers)
                
                elif method.upper() == 'PUT':
                    logger.info(f"PUT 요청 전송: {url}")
                    response = await client.put(url, headers=request_headers, content=body)
                
                elif method.upper() == 'DELETE':
                    logger.info(f"DELETE 요청 전송: {url}")
                    response = await client.delete(url, headers=request_headers, content=body)
                
                elif method.upper() == 'PATCH':
                    logger.info(f"PATCH 요청 전송: {url}")
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
