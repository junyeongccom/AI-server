from fastapi import APIRouter
import logging
from app.domain.controller.crime_controller import CrimeController

# 로거 설정
logger = logging.getLogger("crime_router")
logger.setLevel(logging.INFO)
router = APIRouter()

# GET
@router.get("/preprocess", summary="범죄상세")
async def preprocess():
    controller = CrimeController()
    controller.preprocess('cctv_in_seoul.csv', 'crime_in_seoul.csv', 'pop_in_seoul.xls')
    return {"message": '서울시의 범죄 데이터가 전처리 되었습니다.'}

@router.get("/map", summary="범죄지도 그리기")
async def draw_crime_map():
    controller = CrimeController()
    controller.draw_crime_map()
    return {"message": '서울시의 범죄 지도가 완성되었습니다.'}

@router.get("/map/circle-marker", summary="CCTV 부족비율 Circle Marker 지도 그리기")
async def draw_crime_circle_marker_map():
    logger.info("CCTV 부족비율 Circle Marker 지도 생성 요청")
    controller = CrimeController()
    result = controller.draw_crime_circle_marker_map()
    logger.info("CCTV 부족비율 Circle Marker 지도 생성 완료")
    return {"message": '서울시의 CCTV 부족비율 Circle Marker 지도가 완성되었습니다.'}