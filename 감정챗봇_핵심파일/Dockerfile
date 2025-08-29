# 감정 대화 챗봇 Docker 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일들 복사
COPY . .

# 포트 노출
EXPOSE 5000

# 환경변수 설정
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# 컨테이너 시작 명령
CMD ["python", "emotion_chatbot_api.py"]