# ML Model API Server

FastAPI 기반의 머신러닝 모델 예측 API 서버입니다.

## 프로젝트 구조

```
app/
├── controller/         # API 라우터 정의
│   └── predict_controller.py
├── service/            # 비즈니스 로직
│   └── predict_service.py
├── main.py            # FastAPI 앱 실행
├── model.pkl          # 저장된 ML 모델
```

## 설치 및 실행

### 로컬 환경에서 실행

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 서버 실행:
```bash
python main.py
```

### Docker로 실행

1. Docker 이미지 빌드:
```bash
docker build -t ml-api-server .
```

2. 컨테이너 실행:
```bash
docker run -p 8000:8000 ml-api-server
```

## API 사용 방법

### 예측 API

- 엔드포인트: `POST /api/predict`
- 요청 형식:
```json
{
    "features": [1.0, 2.0, 3.0, ...]
}
```
- 응답 형식:
```json
{
    "prediction": 0.5
}
```

## API 문서

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 