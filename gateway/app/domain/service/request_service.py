import json
from typing import Optional
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
import logging

from app.domain.model.service_type import ServiceType
from app.domain.model.service_proxy_factory import ServiceProxyFactory
from app.foundation.utils.request_utils import clean_request_path, prepare_headers, prepare_body

logger = logging.getLogger("domain.service.request_service")

async def handle_file_upload_request(service: ServiceType, path: str, request: Request, headers: dict, file: UploadFile, json_data: Optional[str] = None):
    """
    파일 업로드 요청 처리를 위한 함수입니다.
    
    Args:
        service: 서비스 타입
        path: 요청 경로
        request: FastAPI 요청 객체
        headers: 준비된 요청 헤더
        file: 업로드된 파일
        json_data: Form 데이터로 전달된 JSON 문자열 (선택적)
        
    Returns:
        처리된 응답 객체
    """
    # 파일 데이터 준비
    file_content = await file.read()
    await file.seek(0)
    files = {"file": (file.filename, file_content, file.content_type)}
    
    # Form 데이터 처리
    form_data = None
    if json_data:
        try:
            form_data = json.loads(json_data)
        except json.JSONDecodeError:
            form_data = {"data": json_data}
    
    # 서비스 프록시 생성
    factory = ServiceProxyFactory(service_type=service)
    
    # 파일 업로드 요청 전송
    response = await factory.request(
        method="POST",
        path=path,
        headers=headers,
        files=files,
        form_data=form_data
    )
    
    return response

async def handle_request(service: ServiceType, path: str, request: Request, method: str, json_data: Optional[str] = None, file: Optional[UploadFile] = None):
    """
    모든 HTTP 요청 처리를 위한 통합 함수입니다.
    
    Args:
        service: 서비스 타입
        path: 요청 경로
        request: FastAPI 요청 객체
        method: HTTP 메서드 ("GET", "POST", "PUT", "DELETE", "PATCH")
        json_data: Form 데이터로 전달된 JSON 문자열 (선택적)
        file: 업로드된 파일 (선택적)
        
    Returns:
        처리된 응답 객체
    """
    logger.info(f"{method} 요청: {service.value}/{path}")
    
    # 경로 정규화
    clean_path = clean_request_path(path)
    
    # 헤더 처리
    headers = prepare_headers(request, service)
    
    # 파일 업로드 처리 (POST 메서드 + 파일 있음)
    if method == "POST" and file and file.filename:
        return await handle_file_upload_request(service, clean_path, request, headers, file, json_data)
    
    # 서비스 프록시 생성
    factory = ServiceProxyFactory(service_type=service)
    
    # 일반 요청 처리 (GET, POST, PUT, DELETE, PATCH)
    if method != "GET":
        # 요청 본문 준비 (GET 이외의 메서드)
        body_dict = await prepare_body(request, json_data, service)
        
        # 챗봇 서비스 디버깅 로그
        if service == ServiceType.CHATBOT:
            logger.info(f"챗봇 서비스 요청 본문: {json.dumps(body_dict)}")
        
        # 요청 전송
        response = await factory.request(
            method=method,
            path=clean_path,
            headers=headers,
            json=body_dict
        )
    else:
        # GET 요청 (본문 없음)
        response = await factory.request(
            method=method,
            path=clean_path,
            headers=headers
        )
    
    return response

def process_response(response):
    """
    서비스 응답을 처리하여 적절한 JSONResponse를 반환합니다.
    
    Args:
        response: 서비스 응답 객체
        
    Returns:
        처리된 JSONResponse 객체
    """
    # 성공 응답 처리 (상태 코드 < 400)
    if response.status_code < 400:
        try:
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception:
            return JSONResponse(
                content={"message": "성공", "raw_response": response.text[:1000]},
                status_code=response.status_code
            )
    else:
        # 오류 응답 처리
        return JSONResponse(
            content={"error": f"서비스 오류: HTTP {response.status_code}", "details": response.text[:500]},
            status_code=response.status_code
        ) 