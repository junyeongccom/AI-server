from app.domain.service.crime_preprocessor import CrimePreprocessor
from app.domain.service.crime_visualizer import CrimeVisualizer
from app.domain.model.crime_schema import CrimeSchema
from app.domain.service.internal.crime_correlation import analyze_correlation, analyze_crime_correlation, get_interpretation_text, load_and_analyze
from app.domain.service.internal.crime_map_create import CrimeMapCreator

class CrimeController:
    def __init__(self):
        self.dataset = CrimeSchema()
        self.preprocessor = CrimePreprocessor()
        self.visualizer = CrimeVisualizer()
        self.map_creator = CrimeMapCreator()

    def preprocess(self, *args):
        self.preprocessor.preprocess(*args)

    def correlation(self): #상관계수 분석
        print("Controller: Calling load_and_analyze for correlation analysis...")
        results = load_and_analyze(self)
        print("Controller: Correlation analysis completed")
        return results
    
    def get_correlation_results(self):
        """상관계수 분석 결과를 반환하는 함수"""
        return self.correlation()

    def draw_crime_map(self):
        try:
            result_map = self.visualizer.draw_crime_map()
            result = {
                "status": "success",
                "result": result_map,
                "message": "Crime map created successfully using visualizer"
            }
            print(f"Controller: Crime map created successfully using visualizer")
        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
            print(f"Controller: Failed to create crime map - {str(e)}")
        return result

    def draw_crime_circle_marker_map(self):
        """
        자치구별 CCTV 부족비율 Circle Marker 지도를 생성하는 함수
        """
        try:
            result_map = self.visualizer.draw_circle_marker_map()
            result = {
                "status": "success",
                "result": result_map,
                "message": "Crime Circle Marker map created successfully using visualizer"
            }
            print(f"Controller: Crime Circle Marker map created successfully using visualizer")
        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
            print(f"Controller: Failed to create Circle Marker map - {str(e)}")
        return result
        
