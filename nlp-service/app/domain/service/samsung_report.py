from konlpy.tag import Okt
import re
from nltk import FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from icecream import ic
import os
import shutil
import traceback
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("samsung_report")

class SamsungReport:
    def __init__(self):
        # 인스턴스 변수 초기화
        self.report_path = 'original/kr-Report_2018.txt'
        self.stopwords_path = 'original/stopwords.txt'
        self.font_path = 'original/D2Coding.ttf'
        self.output_path = 'output/wordcloud.png'
        
        # 로컬(호스트) 출력 경로 설정
        self.local_output_path = '/mnt/host_output/wordcloud.png'
        
        # 데이터 저장용 변수
        self.text = ""
        self.hangeul_text = ""
        self.tokens = []
        self.nouns = []
        self.stopwords = []
        self.filtered_words = []
        self.freq_distribution = None
        
        # NLP 관련 객체
        self.okt = Okt()
        
        # 파일 경로 로깅 (절대 경로로 변환하여 출력)
        self.abs_report_path = os.path.abspath(self.report_path)
        self.abs_stopwords_path = os.path.abspath(self.stopwords_path)
        self.abs_font_path = os.path.abspath(self.font_path)
        self.abs_output_path = os.path.abspath(self.output_path)
        
        logger.info(f"📂 초기화 경로: 현재 작업 디렉토리: {os.getcwd()}")
        logger.info(f"📂 보고서 파일 경로: {self.abs_report_path} (존재: {os.path.exists(self.abs_report_path)})")
        logger.info(f"📂 불용어 파일 경로: {self.abs_stopwords_path} (존재: {os.path.exists(self.abs_stopwords_path)})")
        logger.info(f"📂 폰트 파일 경로: {self.abs_font_path} (존재: {os.path.exists(self.abs_font_path)})")
        logger.info(f"📂 출력 파일 경로: {self.abs_output_path}")
        
        # 디렉토리 생성 (컨테이너 내부)
        os.makedirs('output', exist_ok=True)
        
        # 로컬 출력 디렉토리 생성 시도 (호스트 마운트 경로가 있을 경우)
        local_dir = os.path.dirname(self.local_output_path)
        if local_dir:
            try:
                os.makedirs(local_dir, exist_ok=True)
                logger.info(f"📂 로컬 출력 디렉토리 생성/확인 완료: {local_dir}")
            except Exception as e:
                logger.error(f"⚠️ 로컬 출력 디렉토리 생성 실패: {e}")
                logger.error(traceback.format_exc())

    def read_report(self):
        """삼성 보고서 파일을 읽어옵니다."""
        try:
            logger.info(f"📖 보고서 읽기 시작: {self.abs_report_path}")
            with open(self.report_path, 'r', encoding='utf-8') as f:
                self.text = f.read()
            logger.info(f"✅ 보고서 읽기 완료: {len(self.text)} 글자")
            return self.text
        except Exception as e:
            error_msg = f"⚠️ 보고서 파일 읽기 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"보고서 파일 읽기 실패: {e}")

    def extract_hangeul(self):
        """한글만 추출합니다."""
        try:
            logger.info("🔍 한글 추출 시작")
            # 한글과 공백만 남기고 모두 제거하는 정규표현식
            self.hangeul_text = re.sub(r'[^가-힣\s]', '', self.text)
            # 중복 공백 제거
            self.hangeul_text = re.sub(r'\s+', ' ', self.hangeul_text).strip()
            logger.info(f"✅ 한글 추출 완료: {len(self.hangeul_text)} 글자")
            return self.hangeul_text
        except Exception as e:
            error_msg = f"⚠️ 한글 추출 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"한글 추출 실패: {e}")

    def change_token(self):
        """텍스트를 토큰화합니다."""
        try:
            logger.info("🔍 토큰화 시작")
            # 띄어쓰기 기준으로 단어 토큰화
            self.tokens = self.hangeul_text.split()
            logger.info(f"✅ 토큰화 완료: {len(self.tokens)} 토큰")
            return self.tokens
        except Exception as e:
            error_msg = f"⚠️ 토큰화 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"토큰화 실패: {e}")

    def extract_noun(self):
        """명사를 추출합니다."""
        try:
            self.nouns = []
            logger.info("🔍 명사 추출 시작")
            
            # 진행상황 표시를 위한 변수
            total = len(self.tokens)
            progress_step = max(1, total // 10)  # 10% 단위로 진행상황 보고
            
            for i, token in enumerate(self.tokens):
                if i % progress_step == 0:
                    logger.info(f"⏳ 명사 추출 진행중... {i/total*100:.1f}% 완료")
                
                # KoNLPy Okt를 이용해 명사 추출
                nouns_in_token = self.okt.nouns(token)
                
                # 2글자 이상 명사만 추가 (의미없는 1글자 명사 제거)
                for noun in nouns_in_token:
                    if len(noun) >= 2:
                        self.nouns.append(noun)
            
            logger.info(f"✅ 명사 추출 완료: {len(self.nouns)} 개")
            return self.nouns
        except Exception as e:
            error_msg = f"⚠️ 명사 추출 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"명사 추출 실패: {e}")

    def read_stopword(self):
        """불용어 리스트를 읽어옵니다."""
        try:
            logger.info(f"📖 불용어 파일 읽기 시작: {self.abs_stopwords_path}")
            with open(self.stopwords_path, 'r', encoding='utf-8') as f:
                self.stopwords = [line.strip() for line in f]
            logger.info(f"✅ 불용어 리스트 읽기 완료: {len(self.stopwords)} 개")
            return self.stopwords
        except Exception as e:
            error_msg = f"⚠️ 불용어 파일 읽기 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # 기본 불용어 셋으로 대체하고 계속 진행
            logger.info("🔄 기본 불용어 셋으로 대체합니다")
            self.stopwords = ['이', '그', '저', '것', '수', '등', '들', '및', '에서', '그리고']
            return self.stopwords

    def remove_stopword(self):
        """불용어를 제거합니다."""
        try:
            logger.info("🔍 불용어 제거 시작")
            if not self.stopwords:
                self.read_stopword()
                
            self.filtered_words = [word for word in self.nouns if word not in self.stopwords]
            logger.info(f"✅ 불용어 제거 완료: {len(self.filtered_words)} 개 단어 남음 (제거 전: {len(self.nouns)})")
            return self.filtered_words
        except Exception as e:
            error_msg = f"⚠️ 불용어 제거 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"불용어 제거 실패: {e}")

    def find_frequency(self):
        """단어 빈도수를 분석합니다."""
        try:
            logger.info("🔍 단어 빈도 분석 시작")
            # NLTK의 FreqDist를 이용해 빈도 계산
            self.freq_distribution = FreqDist(self.filtered_words)
            
            # 가장 빈도가 높은 20개 단어 출력
            most_common = self.freq_distribution.most_common(20)
            logger.info(f"✅ 빈도 분석 완료: 총 {len(self.freq_distribution)} 개 고유 단어")
            logger.info(f"📊 상위 단어: {most_common[:5]}")
            
            return self.freq_distribution
        except Exception as e:
            error_msg = f"⚠️ 빈도 분석 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"빈도 분석 실패: {e}")

    def draw_wordcloud(self):
        """워드클라우드를 생성하고 저장합니다. 컨테이너 내부와 로컬에 모두 저장합니다."""
        try:
            # 빈도 분석이 되어있지 않으면 실행
            if not self.freq_distribution:
                self.find_frequency()
                
            logger.info(f"🎨 워드클라우드 생성 시작 (폰트: {self.abs_font_path})")
            
            # 워드클라우드 객체 생성
            wordcloud = WordCloud(
                font_path=self.font_path,  # 한글 폰트 경로
                background_color='white',  # 배경색
                width=800,                # 가로 크기
                height=600,               # 세로 크기
                max_words=200,            # 최대 표시 단어 수
                max_font_size=100,        # 최대 폰트 크기
                random_state=42           # 랜덤 시드 고정
            ).generate_from_frequencies(dict(self.freq_distribution))
            
            # 워드클라우드 그림 저장 (절대 경로로 변환)
            container_output_path = os.path.abspath(self.output_path)
            
            # 워드클라우드 이미지 생성
            plt.figure(figsize=(10, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')  # 축 표시 제거
            plt.tight_layout(pad=0)
            
            # 1. 컨테이너 내부에 저장
            try:
                logger.info(f"💾 컨테이너 내부 저장 시도: {container_output_path}")
                plt.savefig(container_output_path, dpi=300, bbox_inches='tight')
                logger.info(f"✅ 컨테이너 내부 워드클라우드 저장 완료: {container_output_path}")
            except Exception as e:
                error_msg = f"⚠️ 컨테이너 내부 워드클라우드 저장 실패: {e}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                raise Exception(f"내부 저장 실패: {e}")
            
            # 2. 로컬(호스트)에 저장
            try:
                # 방법 1: 직접 저장 (권한 있을 경우)
                logger.info(f"💾 호스트 경로 저장 시도: {self.local_output_path}")
                plt.savefig(self.local_output_path, dpi=300, bbox_inches='tight')
                logger.info(f"✅ 로컬 경로에 워드클라우드 직접 저장 완료: {self.local_output_path}")
            except Exception as e:
                logger.warning(f"⚠️ 로컬 경로 직접 저장 실패: {e}")
                
                # 방법 2: 컨테이너 내부 파일을 로컬로 복사 (방법 1 실패 시)
                try:
                    logger.info(f"🔄 내부 파일을 호스트로 복사 시도: {container_output_path} -> {self.local_output_path}")
                    shutil.copy2(container_output_path, self.local_output_path)
                    logger.info(f"✅ 컨테이너 내부 파일을 로컬로 복사 완료: {self.local_output_path}")
                except Exception as copy_error:
                    logger.warning(f"⚠️ 로컬 경로 복사 실패 (볼륨 마운트 확인 필요): {copy_error}")
                    # 오류는 기록하지만 예외를 발생시키지는 않음 (옵션 기능이므로)
            
            # 그래프 닫기
            plt.close()
            
            # 최종 결과 반환
            return {
                "container_path": container_output_path,
                "local_path": self.local_output_path
            }
        except Exception as e:
            error_msg = f"⚠️ 워드클라우드 생성 오류: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"워드클라우드 생성 실패: {e}")

    def process_all(self):
        """모든 처리 과정을 순차적으로 실행합니다."""
        try:
            logger.info("🚀 삼성 보고서 분석 시작")
            
            # 각 단계를 명확히 분리하여 로깅
            logger.info("📙 STEP 1: 보고서 읽기")
            self.read_report()
            
            logger.info("🔤 STEP 2: 한글 추출")
            self.extract_hangeul()
            
            logger.info("🔢 STEP 3: 토큰화")
            self.change_token()
            
            logger.info("📝 STEP 4: 명사 추출")
            self.extract_noun()
            
            logger.info("🗑️ STEP 5: 불용어 읽기")
            self.read_stopword()
            
            logger.info("✂️ STEP 6: 불용어 제거")
            self.remove_stopword()
            
            logger.info("📊 STEP 7: 빈도 분석")
            self.find_frequency()
            
            logger.info("🎨 STEP 8: 워드클라우드 생성")
            result = self.draw_wordcloud()
            
            logger.info("✅ 삼성 보고서 분석 완료")
            return result
        except Exception as e:
            error_msg = f"❌ 처리 중 오류 발생: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise Exception(f"보고서 처리 실패: {str(e)}")

# 테스트용 코드
if __name__ == "__main__":
    analyzer = SamsungReport()
    analyzer.process_all()        