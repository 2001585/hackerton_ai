# 🚀 감정 챗봇 Docker 배포 가이드

## 📋 배포 준비사항

### 1. 필요한 파일들 확인
```
감정챗봇_핵심파일/
├── raptor_emotion_chatbot.py          # 메인 챗봇
├── conversational_response_generator.py # AI 응답 생성
├── emotion_chatbot_api.py             # REST API
├── gui_chatbot.py                     # GUI 버전
├── demo_chat.py                       # 데모 버전
├── raptor_*.npz                       # 임베딩 파일들
├── raptor_*.csv                       # 데이터 파일
├── raptor_*.npy                       # 벡터 파일
├── requirements.txt                   # 의존성
├── .env                              # 환경 설정
├── Dockerfile                        # Docker 이미지
├── docker-compose.yml                # 컨테이너 구성
└── deploy.sh                         # 배포 스크립트
```

### 2. 환경변수 설정 (.env)
```bash
# CLOVA Studio API 설정
CLOVASTUDIO_API_KEY=your-api-key-here

# CLOVA Speech API 설정  
CLOVA_CLIENT_ID=your-client-id
CLOVA_CLIENT_SECRET=your-client-secret

# Flask 설정
SECRET_KEY=your-secret-key
FLASK_ENV=production
DEBUG=False
```

## 🐳 Docker 배포 방법

### 방법 1: 자동 배포 스크립트 (권장)
```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

### 방법 2: 수동 배포
```bash
# 1. 이미지 빌드
docker-compose build

# 2. 컨테이너 시작
docker-compose up -d

# 3. 상태 확인
docker-compose ps
```

## 🔍 배포 후 확인

### 헬스체크
```bash
curl http://localhost:5000/api/health
```

### 테스트 요청
```bash
# 세션 생성
curl -X POST http://localhost:5000/api/session/create

# 대화 테스트
curl -X POST http://localhost:5000/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{"session_id":"your-session-id","text":"안녕하세요"}'
```

## 📊 운영 명령어

### 로그 확인
```bash
# 실시간 로그
docker-compose logs -f emotion-chatbot

# 최근 100줄
docker-compose logs --tail=100 emotion-chatbot
```

### 서비스 관리
```bash
# 재시작
docker-compose restart

# 중지
docker-compose down

# 완전 삭제 (이미지까지)
docker-compose down --rmi all
```

### 컨테이너 접속
```bash
docker-compose exec emotion-chatbot bash
```

## 🌐 운영 환경 배포 (Nginx)

운영 환경에서 Nginx 리버스 프록시 사용:

```bash
# Nginx 포함 시작
docker-compose --profile production up -d

# 접속: http://localhost (80포트)
```

## 🔧 트러블슈팅

### 1. 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker-compose logs emotion-chatbot

# 일반적 원인:
# - .env 파일 누락
# - API 키 오류
# - 포트 충돌 (5000번 포트)
```

### 2. API 키 오류
```bash
# .env 파일 확인
cat .env

# 컨테이너 재시작
docker-compose restart
```

### 3. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# docker-compose.yml에 메모리 제한 추가:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## 📈 모니터링

### 리소스 사용량
```bash
docker stats emotion-chatbot
```

### 디스크 사용량
```bash
docker system df
```

## 🔄 업데이트 방법

```bash
# 1. 새 코드 반영
git pull  # 또는 파일 복사

# 2. 이미지 재빌드
docker-compose build --no-cache

# 3. 서비스 재시작
docker-compose up -d
```

---

## 🎯 주요 엔드포인트

- **헬스체크**: `GET /api/health`
- **세션 생성**: `POST /api/session/create`  
- **텍스트 대화**: `POST /api/chat/text`
- **음성 대화**: `POST /api/chat/voice`
- **일기 생성**: `POST /api/diary/generate`
- **대화 히스토리**: `GET /api/session/history`

배포 완료 후 위 엔드포인트들을 통해 감정 챗봇 서비스를 이용할 수 있습니다! 🚀