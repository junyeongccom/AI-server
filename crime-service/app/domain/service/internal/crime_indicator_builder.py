import os
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def build_merged_dataset_and_indicators(stored_data_dir='stored_data', output_dir='app/up_data'):
    """
    세 개의 데이터셋을 병합하고 범죄 관련 지표를 생성하는 함수
    1. police_norm_in_seoul.csv: 범죄율 및 검거율
    2. cctv_in_seoul.csv: CCTV 설치 대수
    3. pop_in_seoul.csv: 인구, 외국인, 고령자 비율
    
    반환값: 병합 및 지표가 추가된 DataFrame
    """
    try:
        logger.info("===== 데이터 병합 및 범죄 지표 생성 시작 =====")
        
        # 출력 디렉토리 생성 (없는 경우)
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"출력 디렉토리 확인: {output_dir}")
        
        # 1. 데이터 로드
        logger.info("데이터 로드 중...")
        
        # 경찰서 정규화 데이터 (범죄율)
        police_norm_file = os.path.join(stored_data_dir, 'police_norm_in_seoul.csv')
        try:
            police_norm = pd.read_csv(police_norm_file)
            logger.info(f"경찰서 정규화 데이터 로드 완료: {police_norm.shape}")
            
            # 자치구 컬럼 확인
            if '자치구' not in police_norm.columns and 'Unnamed: 0' in police_norm.columns:
                police_norm = police_norm.rename(columns={'Unnamed: 0': '자치구'})
                logger.info("컬럼 이름 변경: 'Unnamed: 0' -> '자치구'")
            
            # 범죄 컬럼 확인
            if '범죄' not in police_norm.columns and '범죄율' in police_norm.columns:
                police_norm = police_norm.rename(columns={'범죄율': '범죄'})
                logger.info("컬럼 이름 변경: '범죄율' -> '범죄'")
                
            # 범죄 컬럼 숫자형 변환
            police_norm['범죄'] = police_norm['범죄'].astype(float)
            logger.info("'범죄' 컬럼 숫자형(float)으로 변환 완료")

            # 자치구 컬럼 타입 확인 및 로깅
            logger.info(f"경찰서 정규화 데이터 '자치구' 컬럼 타입: {police_norm['자치구'].dtype}")
                
        except Exception as e:
            logger.error(f"경찰서 정규화 데이터 로드 실패: {str(e)}")
            raise
            
        # CCTV 데이터
        cctv_file = os.path.join(stored_data_dir, 'cctv_in_seoul.csv')
        try:
            cctv_data = pd.read_csv(cctv_file)
            logger.info(f"CCTV 데이터 로드 완료: {cctv_data.shape}")
            
            # 자치구 컬럼 확인
            if '자치구' not in cctv_data.columns:
                cctv_data = cctv_data.rename(columns={cctv_data.columns[0]: '자치구'})
                logger.info(f"컬럼 이름 변경: '{cctv_data.columns[0]}' -> '자치구'")
                
            # 소계 컬럼 확인 - 필수 컬럼으로 처리
            if '소계' not in cctv_data.columns:
                logger.error("'소계' 컬럼을 찾을 수 없습니다. CCTV 데이터를 확인해주세요.")
                raise ValueError("'소계' 컬럼 없음: CCTV 데이터가 올바른지 확인 필요")
            
            # 소계 컬럼 숫자형 변환
            cctv_data['소계'] = cctv_data['소계'].astype(float)
            logger.info("'소계' 컬럼 숫자형(float)으로 변환 완료")

            # 자치구 컬럼 타입 확인 및 로깅
            logger.info(f"CCTV 데이터 '자치구' 컬럼 타입: {cctv_data['자치구'].dtype}")
                
        except Exception as e:
            logger.error(f"CCTV 데이터 로드 실패: {str(e)}")
            raise
            
        # 인구 데이터
        pop_file = os.path.join(stored_data_dir, 'pop_in_seoul.csv')
        try:
            pop_data = pd.read_csv(pop_file)
            logger.info(f"인구 데이터 로드 완료: {pop_data.shape}")
            
            # 자치구 컬럼 확인
            if '자치구' not in pop_data.columns:
                pop_data = pop_data.rename(columns={pop_data.columns[0]: '자치구'})
                logger.info(f"컬럼 이름 변경: '{pop_data.columns[0]}' -> '자치구'")
                
            # 인구수, 한국인, 외국인, 고령자 컬럼 이름 정리
            if '인구수' not in pop_data.columns:
                pop_data = pop_data.rename(columns={pop_data.columns[1]: '인구수'})
                
            if '한국인' not in pop_data.columns:
                pop_data = pop_data.rename(columns={pop_data.columns[2]: '한국인'})
                
            if '외국인' not in pop_data.columns:
                pop_data = pop_data.rename(columns={pop_data.columns[3]: '외국인'})
                
            if '고령자' not in pop_data.columns:
                pop_data = pop_data.rename(columns={pop_data.columns[4]: '고령자'})
                
            logger.info("인구 데이터 컬럼 확인 완료")
            
            # 주요 컬럼 숫자형 변환
            for col in ['인구수', '한국인', '외국인', '고령자']:
                pop_data[col] = pop_data[col].astype(float)
            logger.info("인구 관련 컬럼 숫자형(float)으로 변환 완료")
            
            # 비율 컬럼 추가 (없는 경우)
            if '외국인비율' not in pop_data.columns:
                pop_data['외국인비율'] = (pop_data['외국인'] / pop_data['인구수']) * 100
                logger.info("'외국인비율' 컬럼 생성 완료")
                
            if '고령자비율' not in pop_data.columns:
                pop_data['고령자비율'] = (pop_data['고령자'] / pop_data['인구수']) * 100
                logger.info("'고령자비율' 컬럼 생성 완료")

            # 자치구 컬럼 타입 확인 및 로깅
            logger.info(f"인구 데이터 '자치구' 컬럼 타입: {pop_data['자치구'].dtype}")
                
        except Exception as e:
            logger.error(f"인구 데이터 로드 실패: {str(e)}")
            raise
            
        # 2. 데이터 병합
        logger.info("데이터 병합 중...")
        
        # CCTV 데이터와 인구 데이터 병합 전 자치구 컬럼 타입 통일
        try:
            # 병합 전 자치구 컬럼을 문자열로 변환
            cctv_data['자치구'] = cctv_data['자치구'].astype(str)
            pop_data['자치구'] = pop_data['자치구'].astype(str)
            
            logger.info(f"병합 전 CCTV 데이터 '자치구' 컬럼 타입(변환 후): {cctv_data['자치구'].dtype}")
            logger.info(f"병합 전 인구 데이터 '자치구' 컬럼 타입(변환 후): {pop_data['자치구'].dtype}")
            
            # 병합 방식: outer join 사용
            # - outer join은 모든 자치구를 포함하고 누락 데이터는 NaN으로 처리
            # - 실제 데이터에 불일치가 있을 경우도 대비하기 위해 선택
            # - 추후 결측치는 0으로 대체하여 계산 진행
            merged_df = pd.merge(cctv_data, pop_data, on='자치구', how='outer')
            logger.info(f"CCTV + 인구 데이터 병합 완료: {merged_df.shape}")
            logger.info(f"첫 병합 후 '자치구' 컬럼 타입: {merged_df['자치구'].dtype}")
            
        except Exception as e:
            logger.error(f"CCTV + 인구 데이터 병합 실패: {str(e)}")
            raise
            
        # 경찰서 정규화 데이터 병합
        try:
            # 병합 전 자치구 컬럼을 문자열로 변환
            merged_df['자치구'] = merged_df['자치구'].astype(str)
            police_norm['자치구'] = police_norm['자치구'].astype(str)
            
            logger.info(f"병합 전 경찰서 정규화 데이터 '자치구' 컬럼 타입(변환 후): {police_norm['자치구'].dtype}")
            logger.info(f"병합 전 중간 병합 데이터 '자치구' 컬럼 타입(변환 후): {merged_df['자치구'].dtype}")
            
            # 샘플 값 로깅하여 확인
            logger.info(f"경찰서 정규화 데이터 '자치구' 샘플: {police_norm['자치구'].head(3).tolist()}")
            logger.info(f"중간 병합 데이터 '자치구' 샘플: {merged_df['자치구'].head(3).tolist()}")
            
            # 일관성을 위해 여기서도 outer join 유지
            merged_df = pd.merge(merged_df, police_norm, on='자치구', how='outer')
            logger.info(f"최종 데이터 병합 완료: {merged_df.shape}")
            logger.info(f"최종 병합 후 '자치구' 컬럼 타입: {merged_df['자치구'].dtype}")
        except Exception as e:
            logger.error(f"최종 데이터 병합 실패: {str(e)}")
            raise
            
        # 결측치 처리
        merged_df = merged_df.fillna(0)
        logger.info("결측치 0으로 대체 완료")
        
        # 로그에 병합된 데이터의 컬럼 표시
        logger.info(f"병합된 데이터 컬럼: {merged_df.columns.tolist()}")
        
        # 3. 지표 생성
        logger.info("범죄 지표 생성 중...")
            
        # 지표 계산
        try:
            # 인구당 CCTV
            merged_df['인구당_CCTV'] = merged_df['소계'] / merged_df['인구수'].replace(0, 1)  # 0으로 나누기 방지
            
            # 범죄_인구_가중치
            merged_df['범죄_인구_가중치'] = merged_df['범죄'] * (merged_df['인구수'] / 1000)
            
            # 취약지수
            merged_df['취약지수'] = merged_df['범죄'] * (1 + merged_df['외국인비율']/100 + merged_df['고령자비율']/100)
            
            # CCTV_필요지수
            merged_df['CCTV_필요지수'] = merged_df['범죄'] * (merged_df['인구수'] / 1000) * (1 + merged_df['외국인비율']/100 + merged_df['고령자비율']/100)
            
            logger.info("범죄 지표 생성 완료")
        except Exception as e:
            logger.error(f"범죄 지표 생성 실패: {str(e)}")
            raise
            
        # 지표 샘플 데이터 출력
        logger.info("생성된 지표 샘플:")
        indicator_cols = ['인구당_CCTV', '범죄_인구_가중치', '취약지수', 'CCTV_필요지수']
        logger.info(f"지표 컬럼: {indicator_cols}")
        logger.info(f"지표 샘플 데이터:\n{merged_df[['자치구'] + indicator_cols].head(3)}")
        
        # 4. 데이터 저장
        output_file = os.path.join(output_dir, 'merged_data.csv')
        try:
            merged_df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"병합 및 지표 데이터 저장 완료: {output_file}")
        except Exception as e:
            logger.error(f"데이터 저장 실패: {str(e)}")
            raise
            
        logger.info("===== 데이터 병합 및 범죄 지표 생성 완료 =====")
        return merged_df
        
    except Exception as e:
        logger.error(f"데이터 병합 및 지표 생성 중 오류 발생: {str(e)}")
        raise

# 직접 실행 테스트용 (실제로는 사용되지 않음)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        merged_data = build_merged_dataset_and_indicators()
        print("데이터 병합 및 지표 생성 성공!")
    except Exception as e:
        print(f"오류 발생: {str(e)}") 