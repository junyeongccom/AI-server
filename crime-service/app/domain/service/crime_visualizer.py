import numpy as np
import os
import folium
import logging
from fastapi import HTTPException
import traceback    
from app.domain.service.internal.crime_map_create import CrimeMapCreator
from app.domain.service.internal.crime_indicator_builder import build_merged_dataset_and_indicators
from app.domain.service.internal.crime_map_circle_marker import create_crime_circle_marker_map

logger = logging.getLogger("crime_service")

class CrimeVisualizer:
    def __init__(self):
        pass
    
    def draw_crime_map(self) -> dict:
        """범죄 지도를 생성하고 결과를 반환합니다."""
        try:
            map_creator = CrimeMapCreator()
            map_file_path = map_creator.create_map()
            return {"status": "범죄지도를 완성했습니다.", "file_path": map_file_path}
        except HTTPException as e:
            logger.error(f"지도 생성 실패 (HTTPException): {e.status_code} - {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"지도 생성 중 예상치 못한 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"지도 생성 중 예상치 못한 서버 오류: {type(e).__name__}")
    
            
    def draw_circle_marker_map(self, merged_data_dir='app/up_data', 
                              geo_json_dir='stored_data', 
                              output_dir='app/stored_map') -> dict:
        """
        자치구별 범죄율 대비 CCTV 부족비율을 시각화한 Circle Marker 지도를 생성합니다.
        
        처리 단계:
        1. 병합 데이터 및 지표 생성 (build_merged_dataset_and_indicators 호출)
        2. 병합 데이터에서 부족비율 계산 (CCTV_필요지수/소계)
        3. 부족비율 데이터 CSV 저장
        4. 부족비율에 따른 원형 마커 시각화 지도 생성
        5. HTML 지도 파일 저장
        """
        try:
            logger.info("CCTV 부족비율 Circle Marker 지도 생성 요청 시작")
            
            # 1. 먼저 지표 생성 (build_merged_dataset_and_indicators 직접 호출)
            csv_data_dir = 'app/updated_data'  # CSV 데이터가 있는 경로를 고정값으로 설정
            logger.info(f"1단계: 데이터 병합 및 지표 생성 시작 (CSV 데이터 경로: {csv_data_dir})")
            
            merged_data = build_merged_dataset_and_indicators(
                stored_data_dir=csv_data_dir,  # CSV 파일 경로를 'app/updated_data'로 고정
                output_dir=merged_data_dir     # 병합 데이터 저장 경로
            )
            
            logger.info(f"데이터 소스 경로: {csv_data_dir} (CSV 데이터 파일)")
            logger.info(f"GeoJSON 경로: {geo_json_dir}")
            logger.info(f"결과 저장 경로: {merged_data_dir} (병합 데이터)")
            
            # 지표 생성 결과 확인
            if merged_data is None or merged_data.empty:
                logger.error("지표 생성 결과가 없거나 빈 DataFrame입니다. Circle Marker 지도 생성 중단")
                return {
                    "status": "error",
                    "message": "데이터 병합 및 지표 생성 결과가 비어있습니다."
                }
                
            logger.info(f"지표 생성 완료. 데이터 크기: {merged_data.shape}")
            logger.info("Circle Marker 지도 생성 진행 중...")
            
            # 2. Circle Marker 지도 생성 (crime_map_circle_marker의 함수 호출)
            logger.info("2단계: 부족비율 계산 및 CircleMarker 지도 생성")
            map_file_path = create_crime_circle_marker_map(
                merged_data_dir=merged_data_dir,
                geo_json_dir=geo_json_dir,
                output_dir=output_dir
            )
            
            # 3. 통합 결과 반환
            result = {
                "status": "success",
                "message": "CCTV 부족비율 Circle Marker 지도가 성공적으로 생성되었습니다.",
                "indicator_data_path": os.path.join(merged_data_dir, 'merged_data.csv'),
                "shortfall_data_path": os.path.join(merged_data_dir, 'merged_data_with_shortfall.csv'),
                "file_path": map_file_path
            }
            
            logger.info("전체 작업 완료: 지표 생성 → 부족비율 계산 → 지도 생성")
            logger.info(f"지표 데이터: {result['indicator_data_path']}")
            logger.info(f"부족비율 데이터: {result['shortfall_data_path']}")
            logger.info(f"지도 파일: {result['file_path']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Circle Marker 지도 생성 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Circle Marker 지도 생성 실패: {str(e)}"
            }

    def draw_crime_map2(self) -> object:
        file = self.file
        reader = self.reader
        file.context = self.updated_data
        file.fname = 'police_norm'
        police_norm = reader.csv(file)
        file.context = self.stored_data
        file.fname = 'geo_simple'
        state_geo = reader.json(file)
        file.fname = 'crime_in_seoul'
        crime = reader.csv(file)
        file.context = self.updated_data
        file.fname = 'police_pos'
        police_pos = reader.csv(file)
        station_names = []
        for name in crime['관서명']:
            station_names.append('서울' + str(name[:-1] + '경찰서'))
        station_addrs = []
        station_lats = []
        station_lngs = []
        gmaps = reader.gmaps()
        for name in station_names:
            temp = gmaps.geocode(name, language='ko')
            station_addrs.append(temp[0].get('formatted_address'))
            t_loc = temp[0].get('geometry')
            station_lats.append(t_loc['location']['lat'])
            station_lngs.append(t_loc['location']['lng'])

        police_pos['lat'] = station_lats
        police_pos['lng'] = station_lngs
        col = ['살인 검거', '강도 검거', '강간 검거', '절도 검거', '폭력 검거']
        tmp = police_pos[col] / police_pos[col].max()
        police_pos['검거'] = np.sum(tmp, axis=1)

        folium_map = folium.Map(location=[37.5502, 126.982], zoom_start=12, title='Stamen Toner')

        folium.Choropleth(
            geo_data=state_geo,
            data=tuple(zip(police_norm['구별'],police_norm['범죄'])),
            columns=["State", "Crime Rate"],
            key_on="feature.id",
            fill_color="PuRd",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name="Crime Rate (%)",
            reset=True,
        ).add_to(folium_map)
        for i in police_pos.index:
            folium.CircleMarker([police_pos['lat'][i], police_pos['lng'][i]],
                                radius=police_pos['검거'][i] * 10,
                                fill_color='#0a0a32').add_to(folium_map)

        folium_map.save(os.path.join(self.stored_map, 'crime_map.html'))

        return {"message": '서울시의 범죄 지도가 완성되었습니다.'}
        

