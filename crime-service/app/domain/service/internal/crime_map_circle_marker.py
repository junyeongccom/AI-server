import os
import pandas as pd
import numpy as np
import folium
import json
import logging
from fastapi import HTTPException
import traceback

logger = logging.getLogger(__name__)

def create_crime_circle_marker_map(merged_data_dir='app/up_data', 
                                  geo_json_dir='stored_data', 
                                  output_dir='app/stored_map'):
    """
    범죄 데이터와 CCTV 설치 데이터를 기반으로 부족비율을 계산하고
    CircleMarker를 활용한 시각화 지도를 생성하는 함수
    
    Args:
        merged_data_dir: 병합된 데이터가 저장된 디렉토리 경로
        geo_json_dir: GeoJSON 파일이 저장된 디렉토리 경로
        output_dir: 출력 파일이 저장될 디렉토리 경로
        
    Returns:
        저장된 지도 파일 경로
    """
    try:
        logger.info("===== 범죄-CCTV 부족비율 지도 생성 시작 =====")
        
        # 디렉토리 생성 (없는 경우)
        os.makedirs(merged_data_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"병합 데이터 디렉토리 확인: {merged_data_dir}")
        logger.info(f"지도 출력 디렉토리 확인: {output_dir}")
        logger.info(f"GeoJSON 디렉토리 설정값: {geo_json_dir}")
        
        # 현재 작업 디렉토리 로깅
        current_dir = os.getcwd()
        logger.info(f"현재 작업 디렉토리: {current_dir}")
        
        # 1. 병합된 데이터 로드
        merged_data_file = os.path.join(merged_data_dir, 'merged_data.csv')
        
        try:
            merged_df = pd.read_csv(merged_data_file)
            logger.info(f"병합 데이터 로드 완료: {merged_df.shape}")
            
            # 필수 컬럼 확인
            required_columns = ['자치구', '소계', 'CCTV_필요지수', '범죄']
            missing_columns = [col for col in required_columns if col not in merged_df.columns]
            
            if missing_columns:
                missing_cols_str = ', '.join(missing_columns)
                logger.error(f"필수 컬럼이 누락되었습니다: {missing_cols_str}")
                raise ValueError(f"필수 컬럼 누락: {missing_cols_str}")
                
            # 데이터 타입 변환 (안전성 확보)
            merged_df['소계'] = merged_df['소계'].astype(float)
            merged_df['CCTV_필요지수'] = merged_df['CCTV_필요지수'].astype(float)
            merged_df['범죄'] = merged_df['범죄'].astype(float)
            logger.info("데이터 타입 변환 완료")
            
        except Exception as e:
            logger.error(f"병합 데이터 로드 실패: {str(e)}")
            raise
            
        # 2. 부족비율 계산
        logger.info("부족비율 계산 중...")
        
        try:
            # CCTV 대수 0인 경우 1로 치환하여 나눗셈 오류 방지
            merged_df['부족비율'] = merged_df['CCTV_필요지수'] / merged_df['소계'].replace(0, 1)
            
            # 부족비율이 너무 크면 경고 로그 출력 (예: 100 초과)
            extreme_ratio_count = (merged_df['부족비율'] > 100).sum()
            if extreme_ratio_count > 0:
                logger.warning(f"극단적인 부족비율(100 초과)이 {extreme_ratio_count}개 발견되었습니다. CCTV 대수가 매우 적거나 0일 가능성이 있습니다.")
                
            logger.info("부족비율 계산 완료")
            
            # 샘플 데이터 로그 출력
            logger.info(f"부족비율 샘플 데이터:\n{merged_df[['자치구', '소계', 'CCTV_필요지수', '부족비율']].head(3)}")
            
            # 부족비율이 포함된 데이터 저장
            shortfall_file = os.path.join(merged_data_dir, 'merged_data_with_shortfall.csv')
            merged_df.to_csv(shortfall_file, index=False, encoding='utf-8')
            logger.info(f"부족비율 데이터 저장 완료: {shortfall_file}")
            
        except Exception as e:
            logger.error(f"부족비율 계산 중 오류 발생: {str(e)}")
            raise
        
        # 3. GeoJSON 데이터 로드
        # 여러 가능한 경로를 시도하여 GeoJSON 파일을 찾음
        geo_json_file_paths = [
            os.path.join(geo_json_dir, 'geo_simple.json'),  # 기존 경로
            os.path.join('app', geo_json_dir, 'geo_simple.json'),  # app/ 하위 경로
            os.path.join('app', 'stored_data', 'geo_simple.json'),  # 고정 경로
            os.path.join('app', 'updated_data', 'geo_simple.json'),  # updated_data 경로
            os.path.join('/app', 'stored_data', 'geo_simple.json'),  # 절대 경로
            os.path.join(current_dir, geo_json_dir, 'geo_simple.json'),  # 현재 디렉토리 기준
            os.path.join(current_dir, 'stored_data', 'geo_simple.json'),  # 현재 디렉토리의 stored_data
            os.path.join(current_dir, 'app', 'stored_data', 'geo_simple.json')  # 현재 디렉토리의 app/stored_data
        ]
        
        # 각 경로가 존재하는지 로깅
        for path in geo_json_file_paths:
            exists = os.path.exists(path)
            logger.info(f"GeoJSON 경로 확인: {path} - {'존재함' if exists else '존재하지 않음'}")
        
        # 첫 번째로 존재하는 경로 선택
        geo_json_file = None
        for path in geo_json_file_paths:
            if os.path.exists(path):
                geo_json_file = path
                logger.info(f"사용할 GeoJSON 파일 경로: {geo_json_file}")
                break
        
        if geo_json_file is None:
            # 파일이 없는 경우 대체 방법: 임베디드 GeoJSON 사용
            logger.warning("GeoJSON 파일을 찾을 수 없습니다. 임베디드 GeoJSON 데이터를 사용합니다.")
            # app/updated_data 디렉터리에서 geo_simple.json 파일을 찾아보기
            updated_data_geo = os.path.join('app', 'updated_data', 'geo_simple.json')
            if os.path.exists(updated_data_geo):
                geo_json_file = updated_data_geo
                logger.info(f"대체 GeoJSON 경로 사용: {geo_json_file}")
            else:
                error_msg = "GeoJSON 파일을 찾을 수 없습니다. Docker 볼륨 설정을 확인해주세요."
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
        
        try:
            with open(geo_json_file, 'r', encoding='utf-8') as f:
                state_geo = json.load(f)
            logger.info(f"GeoJSON 데이터 로드 완료: {geo_json_file}")
        except Exception as e:
            logger.error(f"GeoJSON 데이터 로드 실패: {str(e)}")
            raise
            
        # 4. 자치구별 중심 좌표 추출
        logger.info("자치구별 중심 좌표 추출 중...")
        district_centers = {}
        
        try:
            for feature in state_geo['features']:
                district_name = feature['id']
                coords = feature['geometry']['coordinates']
                
                # 폴리곤(Polygon) 타입
                if feature['geometry']['type'] == 'Polygon':
                    # 첫 번째 좌표 사용 (간단한 방식)
                    first_coord = coords[0][0]
                    # GeoJSON은 [경도, 위도] 순서, Folium은 [위도, 경도] 순서
                    district_centers[district_name] = (first_coord[1], first_coord[0])
                    
                # 멀티폴리곤(MultiPolygon) 타입
                elif feature['geometry']['type'] == 'MultiPolygon':
                    # 첫 번째 폴리곤의 첫 번째 좌표 사용
                    first_coord = coords[0][0][0]
                    district_centers[district_name] = (first_coord[1], first_coord[0])
                    
            logger.info(f"자치구별 중심 좌표 추출 완료: {len(district_centers)} 개 자치구")
            
        except Exception as e:
            logger.error(f"자치구별 중심 좌표 추출 중 오류 발생: {str(e)}")
            raise
            
        # 5. Circle Marker 지도 생성
        logger.info("Circle Marker 지도 생성 중...")
        
        try:
            # 기본 지도 생성 (서울 중심)
            folium_map = folium.Map(location=[37.5502, 126.982], 
                                    zoom_start=11, 
                                    tiles='OpenStreetMap')
            
            # 각 자치구별 Circle Marker 추가
            for idx, row in merged_df.iterrows():
                district = row['자치구']
                crime_index = row['범죄']
                cctv_count = row['소계']
                shortfall_ratio = row['부족비율']
                
                # 자치구가 좌표 데이터에 있는지 확인
                if district in district_centers:
                    # Circle Marker 크기 설정 (부족비율에 비례)
                    # 스케일링: 부족비율이 지나치게 큰 경우 제한
                    radius = min(shortfall_ratio * 8, 50)  # 최대 radius는 50으로 제한
                    radius = max(radius, 5)  # 최소 radius는 5로 설정
                    
                    # 색상 설정: 부족비율 > 1 (빨강), 아니면 파랑
                    color = 'red' if shortfall_ratio > 1 else 'blue'
                    
                    # 툴팁 생성
                    tooltip = f"""
                    <div style="font-family: 'Malgun Gothic'; font-size: 12px;">
                    <b>{district}</b><br>
                    범죄 지수: {crime_index:.2f}<br>
                    CCTV 설치 대수: {int(cctv_count)}대<br>
                    부족 비율: {shortfall_ratio:.2f}
                    </div>
                    """
                    
                    # Circle Marker 추가
                    folium.CircleMarker(
                        location=district_centers[district],
                        radius=radius,
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.6,
                        tooltip=folium.Tooltip(tooltip)
                    ).add_to(folium_map)
                    
                    # 자치구명 표시
                    folium.Marker(
                        location=district_centers[district],
                        icon=folium.DivIcon(
                            icon_size=(0, 0),
                            html=f'<div style="font-size: 10px; font-weight: bold;">{district}</div>'
                        )
                    ).add_to(folium_map)
                else:
                    logger.warning(f"자치구 '{district}'의 좌표 정보가 GeoJSON에 없습니다. 스킵합니다.")
            
            # 범례 추가
            legend_html = '''
            <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                        padding: 10px; border: 1px solid grey; border-radius: 5px; font-family: 'Malgun Gothic';">
                <p><b>CCTV 부족비율 지도</b></p>
                <p><i class="fa fa-circle" style="color:red"></i> 부족비율 > 1 (CCTV 부족)</p>
                <p><i class="fa fa-circle" style="color:blue"></i> 부족비율 ≤ 1 (CCTV 충분)</p>
                <p>* 원의 크기는 부족비율에 비례</p>
            </div>
            '''
            folium_map.get_root().html.add_child(folium.Element(legend_html))
            
            logger.info("Circle Marker 지도 생성 완료")
            
            # 6. 지도 저장
            # 상대 경로에서 절대 경로로 변환
            output_map_file = os.path.join(output_dir, 'crime_circle_marker_map.html')
            output_map_file_abs = os.path.abspath(output_map_file)
            
            # 저장 시도 경로 로깅
            logger.info(f"상대 경로: {output_map_file}")
            logger.info(f"저장 시도 절대 경로: {output_map_file_abs}")
            
            # 디렉터리 존재 확인 및 권한 확인
            output_dir_abs = os.path.dirname(output_map_file_abs)
            if not os.path.exists(output_dir_abs):
                logger.warning(f"출력 디렉토리가 존재하지 않습니다: {output_dir_abs}")
                os.makedirs(output_dir_abs, exist_ok=True)
                logger.info(f"출력 디렉토리 생성 완료: {output_dir_abs}")
            
            # 디렉토리에 쓰기 권한이 있는지 확인
            if not os.access(output_dir_abs, os.W_OK):
                logger.error(f"출력 디렉토리에 쓰기 권한이 없습니다: {output_dir_abs}")
                raise PermissionError(f"디렉토리 쓰기 권한 없음: {output_dir_abs}")
            
            # 파일 저장 시도 - try/except로 감싸기
            try:
                folium_map.save(output_map_file_abs)
                logger.info(f"지도 저장 완료: {output_map_file_abs}")
                
                # 파일이 실제로 생성되었는지 확인
                if os.path.exists(output_map_file_abs):
                    file_size = os.path.getsize(output_map_file_abs)
                    logger.info(f"지도 파일 확인: {output_map_file_abs} (크기: {file_size} 바이트)")
                else:
                    logger.error(f"지도 파일이 생성되었지만 확인할 수 없습니다: {output_map_file_abs}")
            except Exception as e:
                logger.error(f"지도 저장 실패: {str(e)}")
                logger.error(traceback.format_exc())
                raise
            
            return output_map_file_abs
            
        except Exception as e:
            logger.error(f"지도 생성 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
    except Exception as e:
        logger.error(f"범죄-CCTV 부족비율 지도 생성 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"지도 생성 중 오류: {str(e)}")

# 직접 실행 테스트용 (실제로는 사용되지 않음)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        map_file = create_crime_circle_marker_map()
        print(f"지도 생성 성공: {map_file}")
    except Exception as e:
        print(f"오류 발생: {str(e)}") 