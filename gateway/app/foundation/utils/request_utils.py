import json
from typing import Optional
from fastapi import Request
from app.domain.model.service_type import ServiceType
import logging

logger = logging.getLogger("foundation.utils.request_utils")

def clean_request_path(path: str) -> str:
    """
    경로 문자열에서 중복된 슬래시(//)를 하나로 정리합니다.
    
    Args:
        path: 정리할 경로 문자열
        
    Returns:
        정규화된 경로 문자열
    """
    while '//' in path:
        path = path.replace('//', '/')
    return path

def prepare_headers(request: Request, service: ServiceType) -> dict:
    """
    요청 헤더를 준비합니다.
    - content-length, host 헤더 제거
    - 챗봇 서비스의 경우 Content-Type을 application/json으로 설정
    
    Args:
        request: FastAPI 요청 객체
        service: 서비스 타입
        
    Returns:
        처리된 헤더 딕셔너리
    """
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['content-length', 'host']}
    
    if service == ServiceType.CHATBOT:
        # 기존 Content-Type 헤더를 제거하고 새로 설정
        headers = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
        headers["Content-Type"] = "application/json"
        logger.info("챗봇 서비스용 Content-Type 헤더 설정: application/json")
    
    return headers

async def prepare_body(request: Request, json_data: Optional[str], service: ServiceType) -> dict:
    """
    요청 본문을 준비합니다.
    - JSON 파싱 처리
    - 챗봇 서비스의 경우 {"message": ..., "user_id": "123"} 형식으로 변환
    
    Args:
        request: FastAPI 요청 객체
        json_data: Form 데이터로 전달된 JSON 문자열 (선택적)
        service: 서비스 타입
        
    Returns:
        처리된 요청 본문 딕셔너리
    """
    is_chatbot = service == ServiceType.CHATBOT
    body_dict = {}
    
    # JSON 데이터 파싱
    if json_data:
        try:
            parsed = json.loads(json_data)
            logger.debug(f"Form 데이터에서 JSON 파싱 성공: {type(parsed)}")
        except json.JSONDecodeError:
            parsed = json_data
            logger.debug(f"Form 데이터 JSON 파싱 실패, 원본 문자열 사용: {type(parsed)}")
    else:
        # 요청 본문에서 데이터 가져오기
        body_bytes = await request.body()
        if body_bytes:
            body_text = body_bytes.decode('utf-8', errors='replace')
            try:
                parsed = json.loads(body_text)
                logger.debug(f"요청 본문에서 JSON 파싱 성공: {type(parsed)}")
            except json.JSONDecodeError:
                parsed = body_text
                logger.debug(f"요청 본문 JSON 파싱 실패, 원본 문자열 사용: {type(parsed)}")
        else:
            parsed = {}
            logger.debug("요청 본문 없음, 빈 객체 사용")
    
    # 챗봇 서비스 처리
    if is_chatbot:
        if isinstance(parsed, dict) and "message" in parsed:
            # 이미 올바른 형식이면 user_id 추가 (없는 경우)
            if "user_id" not in parsed:
                parsed["user_id"] = "123"
            return parsed
        else:
            # 다른 형식이면 message 필드로 변환
            message = str(parsed)
            if isinstance(parsed, dict) and len(parsed) > 0:
                # 첫 번째 필드 값을 message로 사용
                first_key = next(iter(parsed))
                message = str(parsed[first_key])
            
            return {
                "message": message,
                "user_id": "123"
            }
    
    # 일반 서비스 처리
    if isinstance(parsed, dict):
        return parsed
    else:
        return {"data": str(parsed)} 