# 감정 챗봇 실행 가이드

## 🚀 실행 방법 (3가지)

### 1. GUI 버전 (추천) ⭐
```bash
python gui_chatbot.py
```
- **윈도우 기반 그래픽 인터페이스**
- 클릭으로 쉽게 사용 가능
- 일기 생성 버튼 제공
- 실시간 감정 분석 표시

### 2. 데모 버전 (자동 테스트)
```bash
python demo_chat.py
```
- **미리 정의된 대화로 자동 테스트**
- 5개 감정 시나리오 실행
- 일기 자동 생성 및 저장
- 시스템 검증용

### 3. API 서버 버전
```bash
python emotion_chatbot_api.py
```
- **REST API 서버 실행**
- http://localhost:5000 에서 서비스
- 웹/모바일 앱 연동 가능

## 🎯 추천 실행 순서

### Windows 사용자
1. **GUI 버전**: `python gui_chatbot.py` - 가장 사용하기 쉬움
2. **데모 버전**: `python demo_chat.py` - 시스템 테스트

### 개발자/서버 환경
1. **데모 버전**: `python demo_chat.py` - 기능 확인
2. **API 서버**: `python emotion_chatbot_api.py` - 서비스 배포

## 📊 각 버전 특징

| 버전 | 장점 | 사용 상황 |
|------|------|----------|
| **GUI** | 직관적, 사용 쉬움 | 개인 사용, 데모 |
| **데모** | 자동 테스트, 안정적 | 시스템 검증 |
| **API** | 확장성, 연동 가능 | 서비스 배포 |

## 🔧 문제 해결

### 1. 한글 표시 문제
- Windows에서 이모지/한글이 깨지면 **GUI 버전** 사용

### 2. 입력 문제  
- 콘솔에서 입력이 안 되면 **GUI 버전** 또는 **데모 버전** 사용

### 3. 파일 없음 오류
```bash
# 필수 파일 확인
ls -la *.npz *.npy *.csv
```

### 4. 메모리 부족
- 시스템 메모리 4GB 이상 권장
- 다른 프로그램 종료 후 재시도

## ✅ 성공 확인

### GUI 버전
- 윈도우가 열리고 "챗봇 준비 완료" 메시지 표시

### 데모 버전  
- 5개 대화 자동 실행 후 일기 생성

### API 버전
- "서버 시작 중..." 메시지 후 http://localhost:5000 접속 가능

## 📁 생성되는 파일

- `diary_YYYYMMDD_HHMMSS.json` - 일기 데이터
- `demo_diary_YYYYMMDD_HHMMSS.json` - 데모 일기

## 🎮 GUI 사용법

1. **GUI 실행**: `python gui_chatbot.py`
2. **대화하기**: 하단 입력창에 메시지 입력 후 엔터
3. **일기 생성**: "📖 일기 생성" 버튼 클릭
4. **초기화**: "🔄 초기화" 버튼으로 대화 리셋
5. **종료**: "❌ 종료" 버튼으로 프로그램 종료

## 🔗 API 테스트 (서버 버전)

```bash
# 헬스체크
curl http://localhost:5000/api/health

# 세션 생성
curl -X POST http://localhost:5000/api/session/create

# 대화 테스트
curl -X POST http://localhost:5000/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{"session_id":"your-session-id","text":"오늘 기분이 좋아요"}'
```