from fastapi import FastAPI, APIRouter, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List, Union, Tuple
from dotenv import load_dotenv
import logging
import sys
from contextlib import asynccontextmanager
import json
from pydantic import BaseModel


from app.domain.model.service_proxy_factory import ServiceProxyFactory
from app.domain.model.service_type import ServiceType

# ✅ 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway_api")

# ✅ 환경변수 로드
# Load environment variables from .env file
load_dotenv()



# ✅ 요청 모델 정의
class FinanceRequest(BaseModel):
    data: Dict[str, Any]


# ✅ 라이프스팬 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀🚀🚀 FastAPI 앱이 시작됩니다.")
    yield
    print("🛑 FastAPI 앱이 종료됩니다.")

# ✅ FastAPI 설정
app = FastAPI(
    title="Gateway API",
    description="Gateway API for jinmini.com",
    version="0.1.0",
    lifespan=lifespan
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 헤더 변환 함수 추가
def convert_headers(headers: Union[List[Tuple[bytes, bytes]], Dict[str, str]]) -> Dict[str, str]:
    """
    헤더를 Dict[str, str] 형태로 변환하는 유틸리티 함수
    
    Args:
        headers: [(b"key", b"value")] 형태의 List 또는 Dict[str, str]
        
    Returns:
        Dict[str, str]: 변환된 헤더 딕셔너리
    """
    if isinstance(headers, list):
        return {k.decode(): v.decode() for k, v in headers}
    return headers

# ✅ 메인 라우터 생성
gateway_router = APIRouter(prefix="/ai/v1", tags=["Gateway API"])

# ✅ 메인 라우터 실행
# GET
@gateway_router.get("/{service}/{path:path}", summary="GET 프록시")
async def proxy_get(
    service: ServiceType, 
    path: str, 
    request: Request
):
    try:
        logger.info(f"GET 요청: {service.value}/{path}")
        factory = ServiceProxyFactory(service_type=service)
        
        # 헤더를 딕셔너리로 변환
        headers_dict = convert_headers(request.headers.raw)
        
        response = await factory.request(
            method="GET",
            path=path,
            headers=headers_dict
        )
        
        if response.status_code == 200:
            try:
                return JSONResponse(content=response.json(), status_code=response.status_code)
            except Exception:
                return JSONResponse(
                    content={"message": "성공", "raw_response": response.text[:1000]},
                    status_code=200
                )
        else:
            return JSONResponse(
                content={"error": f"서비스 오류: HTTP {response.status_code}", "details": response.text[:500]},
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# 통합 POST 요청 처리 (JSON 또는 파일 업로드)
@gateway_router.post(
    "/{service}/{path:path}", 
    summary="통합 POST 프록시 (JSON 또는 파일 업로드)", 
    description="하나의 엔드포인트에서 JSON 요청과 파일 업로드를 모두 처리합니다."
)
async def proxy_post(
    service: ServiceType, 
    path: str,
    request: Request,
    file: UploadFile = File(None, description="업로드할 파일 (선택 사항)"),
    json_data: Optional[str] = Form(None, description="JSON 형식의 데이터 (선택 사항)")
):
    try:
        logger.info(f"POST 요청: {service.value}/{path}")
        factory = ServiceProxyFactory(service_type=service)
        # ✅ Content-Length, Host 헤더 제외
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ['content-length', 'host']}

        
        # 파일 업로드 처리
        if file and file.filename:
            # 파일 데이터 준비
            file_content = await file.read()
            await file.seek(0)
            files = {"file": (file.filename, file_content, file.content_type)}
            
            # JSON 데이터 준비 (있는 경우)
            form_data = None  # ← None으로 초기화
            if json_data:
                try:
                    form_data = json.loads(json_data)
                except:
                    form_data = {"data": json_data}
            
            # 파일 업로드 요청 전송
            response = await factory.request(
                method="POST",
                path=path,
                headers=headers,
                files=files,
                form_data=form_data  # ← None이면 data를 아예 안 보냄
            )
        else:
            # JSON 요청 처리
            body_dict = None

            # Form에서 JSON 데이터가 전송된 경우
            if json_data:
                try:
                    # 일반적인 경우 JSON 파싱
                    parsed_data = json.loads(json_data)
                    
                    # 챗봇 서비스인 경우 특별한 형식으로 변환
                    if service == ServiceType.CHATBOT:
                        # 이미 message 필드가 있는 경우
                        if isinstance(parsed_data, dict) and "message" in parsed_data:
                            body_dict = parsed_data
                            # user_id가 없으면 추가
                            if "user_id" not in body_dict:
                                body_dict["user_id"] = "123"
                        else:
                            # 문자열이나 다른 형식의 데이터를 message로 변환
                            body_dict = {
                                "message": json_data,
                                "user_id": "123"
                            }
                    else:
                        body_dict = parsed_data
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 처리
                    if service == ServiceType.CHATBOT:
                        body_dict = {
                            "message": json_data,
                            "user_id": "123"
                        }
                    else:
                        body_dict = {"data": json_data}
            else:
                # 요청 본문에서 JSON 데이터 가져오기
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        parsed_data = json.loads(body_bytes.decode())
                        
                        # 챗봇 서비스인 경우 특별한 형식으로 변환
                        if service == ServiceType.CHATBOT:
                            # 이미 message 필드가 있는 경우
                            if isinstance(parsed_data, dict) and "message" in parsed_data:
                                body_dict = parsed_data
                                # user_id가 없으면 추가
                                if "user_id" not in body_dict:
                                    body_dict["user_id"] = "123"
                            else:
                                # message가 없는 경우, 첫 번째 필드를 message로 사용
                                if isinstance(parsed_data, dict) and len(parsed_data) > 0:
                                    first_key = next(iter(parsed_data))
                                    body_dict = {
                                        "message": str(parsed_data[first_key]),
                                        "user_id": "123"
                                    }
                                else:
                                    # 다른 형식이면 전체를 문자열로 변환하여 message로 사용
                                    body_dict = {
                                        "message": body_bytes.decode(),
                                        "user_id": "123"
                                    }
                        else:
                            body_dict = parsed_data
                    except json.JSONDecodeError:
                        if service == ServiceType.CHATBOT:
                            body_dict = {
                                "message": body_bytes.decode(),
                                "user_id": "123"
                            }
                        else:
                            body_dict = {"data": body_bytes.decode()}
                else:
                    if service == ServiceType.CHATBOT:
                        body_dict = {
                            "message": "",
                            "user_id": "123"
                        }
                    else:
                        body_dict = {}

            # JSON 요청 전송 (json= 사용)
            response = await factory.request(
                method="POST",
                path=path,
                headers=headers,
                json=body_dict  # ✅ 이 부분 중요
            )
        
        # 응답 처리
        if response.status_code < 400:
            try:
                return JSONResponse(content=response.json(), status_code=response.status_code)
            except:
                return JSONResponse(
                    content={"message": "성공", "raw_response": response.text[:1000]},
                    status_code=response.status_code
                )
        else:
            return JSONResponse(
                content={"error": f"서비스 오류: HTTP {response.status_code}", "details": response.text[:500]},
                status_code=response.status_code
            )
            
    except Exception as e:
        logger.error(f"게이트웨이 오류: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# PUT
@gateway_router.put("/{service}/{path:path}", summary="PUT 프록시")
async def proxy_put(service: ServiceType, path: str, request: Request):
    try:
        factory = ServiceProxyFactory(service_type=service)
        # 헤더를 딕셔너리로 변환
        headers_dict = convert_headers(request.headers.raw)
        
        # JSON 데이터 추출
        body_bytes = await request.body()
        if body_bytes:
            try:
                body_dict = json.loads(body_bytes.decode())
                response = await factory.request(
                    method="PUT",
                    path=path,
                    headers=headers_dict,
                    json=body_dict
                )
            except json.JSONDecodeError:
                response = await factory.request(
                    method="PUT",
                    path=path,
                    headers=headers_dict,
                    body=body_bytes
                )
        else:
            response = await factory.request(
                method="PUT",
                path=path,
                headers=headers_dict
            )
            
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# DELETE
@gateway_router.delete("/{service}/{path:path}", summary="DELETE 프록시")
async def proxy_delete(service: ServiceType, path: str, request: Request):
    try:
        factory = ServiceProxyFactory(service_type=service)
        # 헤더를 딕셔너리로 변환
        headers_dict = convert_headers(request.headers.raw)
        
        # JSON 데이터 추출
        body_bytes = await request.body()
        if body_bytes:
            try:
                body_dict = json.loads(body_bytes.decode())
                response = await factory.request(
                    method="DELETE",
                    path=path,
                    headers=headers_dict,
                    json=body_dict
                )
            except json.JSONDecodeError:
                response = await factory.request(
                    method="DELETE",
                    path=path,
                    headers=headers_dict,
                    body=body_bytes
                )
        else:
            response = await factory.request(
                method="DELETE",
                path=path,
                headers=headers_dict
            )
            
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# PATCH
@gateway_router.patch("/{service}/{path:path}", summary="PATCH 프록시")
async def proxy_patch(service: ServiceType, path: str, request: Request):
    try:
        factory = ServiceProxyFactory(service_type=service)
        # 헤더를 딕셔너리로 변환
        headers_dict = convert_headers(request.headers.raw)
        
        # JSON 데이터 추출
        body_bytes = await request.body()
        if body_bytes:
            try:
                body_dict = json.loads(body_bytes.decode())
                response = await factory.request(
                    method="PATCH",
                    path=path,
                    headers=headers_dict,
                    json=body_dict
                )
            except json.JSONDecodeError:
                response = await factory.request(
                    method="PATCH",
                    path=path,
                    headers=headers_dict,
                    body=body_bytes
                )
        else:
            response = await factory.request(
                method="PATCH",
                path=path,
                headers=headers_dict
            )
            
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ 메인 라우터 등록
app.include_router(gateway_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    ) 