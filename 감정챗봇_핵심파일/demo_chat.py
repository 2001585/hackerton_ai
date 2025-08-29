# -*- coding: utf-8 -*-
"""
데모용 간단한 챗봇 - 미리 정의된 대화로 테스트
"""

import json
from datetime import datetime
from raptor_emotion_chatbot import EmotionChatbot

def demo_conversation():
    """미리 정의된 대화로 데모 실행"""
    
    print("=" * 60)
    print("🤖 감정 대화 챗봇 데모")
    print("=" * 60)
    print("미리 정의된 대화로 시스템을 테스트합니다.\n")
    
    # 챗봇 초기화
    try:
        print("🔄 챗봇 시스템 로딩 중...")
        chatbot = EmotionChatbot()
        print("✅ 준비 완료!\n")
    except Exception as e:
        print(f"❌ 챗봇 로드 실패: {e}")
        return
    
    # 미리 정의된 대화 시나리오
    demo_messages = [
        "오늘 정말 기분이 좋아! 친구들과 놀러가기로 했거든",
        "그런데 갑자기 비가 와서 계획이 취소됐어... 너무 아쉬워",
        "엄마가 또 공부하라고 잔소리하셔서 짜증나",
        "내일 시험인데 준비가 안 되어서 불안해 죽겠어",
        "친구가 내 비밀을 다른 사람에게 말해서 배신감 들어"
    ]
    
    print("📝 대화 시작:")
    print("-" * 40)
    
    # 각 메시지 처리
    for i, message in enumerate(demo_messages, 1):
        print(f"\n[턴 {i}]")
        print(f"😊 사용자: {message}")
        
        try:
            # 챗봇 응답 생성
            response = chatbot.process_input(message, input_type="text")
            
            if response["status"] == "success":
                # 감정 이모지 매핑
                emotion_emojis = {
                    "기쁨": "😊", "슬픔": "😢", "분노": "😠",
                    "불안": "😰", "당황": "😵", "상처": "💔"
                }
                
                emotion = response["detected_emotion"]
                confidence = response["emotion_confidence"]
                bot_response = response["bot_response"]
                emoji = emotion_emojis.get(emotion, "🤖")
                
                print(f"{emoji} 챗봇: {bot_response}")
                print(f"💭 감정: {emotion} ({confidence}%)")
                
            else:
                print(f"❌ 오류: {response.get('message', '알 수 없는 오류')}")
                
        except Exception as e:
            print(f"❌ 처리 오류: {e}")
    
    print("\n" + "=" * 60)
    print("📊 대화 통계")
    print("=" * 60)
    
    # 감정 통계
    if chatbot.conversation_history:
        from collections import Counter
        emotions = [turn.detected_emotion for turn in chatbot.conversation_history]
        emotion_counts = Counter(emotions)
        
        print(f"총 대화 턴: {len(chatbot.conversation_history)}턴")
        print("감정 분포:")
        for emotion, count in emotion_counts.most_common():
            percentage = (count / len(emotions)) * 100
            print(f"  {emotion}: {count}회 ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("📖 일기 생성")
    print("=" * 60)
    
    try:
        print("🔄 일기 생성 중...")
        diary = chatbot.generate_diary_summary()
        
        if diary["status"] == "success":
            diary_content = diary["diary"]
            emotion_analysis = diary["emotion_analysis"]
            
            print(f"\n📝 일기 요약:")
            print(diary_content['<<일기 요약>>'])
            
            print(f"\n🔍 원인:")
            print(diary_content['<<원인>>'])
            
            print(f"\n💡 조언:")
            print(diary_content['<<조언>>'])
            
            print(f"\n📋 투두리스트:")
            todos = diary_content['<<투두리스트>>']
            print(f"  📅 오늘: {todos['<<오늘>>']}")
            print(f"  📅 내일: {todos['<<내일>>']}")
            print(f"  📅 모레: {todos['<<모레>>']}")
            print(f"  📅 D+3: {todos['<<D-3>>']}")
            
            print(f"\n📊 감정 분석:")
            print(f"  🎯 대표 감정: {emotion_analysis['dominant_emotion']}")
            print("  📈 감정 분포 (TOP 3):")
            for emotion_data in emotion_analysis['top_3_emotions']:
                emotion = emotion_data['emotion']
                percentage = emotion_data['percentage']
                print(f"    - {emotion}: {percentage}%")
            
            # 파일 저장
            filename = f"demo_diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(diary, f, ensure_ascii=False, indent=2)
            print(f"\n💾 일기가 {filename}에 저장되었습니다.")
            
        else:
            print("❌ 일기 생성 실패")
            
    except Exception as e:
        print(f"❌ 일기 생성 오류: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 데모 완료!")
    print("=" * 60)

if __name__ == "__main__":
    demo_conversation()