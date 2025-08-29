#!/bin/bash

# 감정 챗봇 Docker 배포 스크립트

echo "🚀 감정 챗봇 Docker 배포 시작"
echo "================================"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    echo "❌ 오류: Dockerfile이 없습니다. 올바른 디렉토리에서 실행해주세요."
    exit 1
fi

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ 오류: .env 파일이 없습니다. 환경 변수를 설정해주세요."
    exit 1
fi

# 필수 파일들 확인
echo "📋 필수 파일 확인 중..."
required_files=(
    "raptor_emotion_chatbot.py"
    "conversational_response_generator.py"
    "emotion_chatbot_api.py"
    "raptor_l1_cluster_embeddings.npz"
    "raptor_l2_cluster_embeddings.npz"
    "raptor_sampled_data.csv"
    "raptor_sampled_embeddings.npy"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 누락된 파일: $file"
        exit 1
    fi
done

echo "✅ 모든 필수 파일이 존재합니다."

# 데이터 디렉토리 생성
mkdir -p data

# Docker 이미지 빌드
echo ""
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

echo "✅ Docker 이미지 빌드 완료"

# 기존 컨테이너 중지 및 제거
echo ""
echo "🔄 기존 컨테이너 정리 중..."
docker-compose down

# 새 컨테이너 시작
echo ""
echo "🚀 컨테이너 시작 중..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 컨테이너 시작 실패"
    exit 1
fi

# 상태 확인
echo ""
echo "📊 배포 상태 확인 중..."
sleep 10

# 헬스체크
echo "🏥 헬스체크 수행 중..."
for i in {1..5}; do
    if curl -s -f http://localhost:5000/api/health > /dev/null; then
        echo "✅ 헬스체크 성공!"
        break
    else
        echo "⏳ 헬스체크 대기 중... ($i/5)"
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        echo "❌ 헬스체크 실패. 로그를 확인해주세요:"
        docker-compose logs emotion-chatbot
        exit 1
    fi
done

# 배포 완료
echo ""
echo "🎉 배포 완료!"
echo "================================"
echo "📍 서비스 접속 정보:"
echo "   - API 서버: http://localhost:5000"
echo "   - 헬스체크: http://localhost:5000/api/health"
echo ""
echo "📊 유용한 명령어들:"
echo "   - 로그 확인: docker-compose logs -f emotion-chatbot"
echo "   - 컨테이너 상태: docker-compose ps"
echo "   - 서비스 중지: docker-compose down"
echo "   - 서비스 재시작: docker-compose restart"
echo ""
echo "✨ 감정 챗봇이 성공적으로 배포되었습니다!"