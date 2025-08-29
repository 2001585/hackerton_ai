"""
대화형 응답 생성기 - 프롬프트 엔지니어링 기반
CLOVA Studio API를 사용한 동적 응답 생성
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# langchain_naver 사용 (작동 확인된 방식)
try:
    from langchain_naver import ChatClovaX
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[WARNING] langchain_naver가 설치되지 않았습니다. pip install langchain-naver로 설치하세요.")

load_dotenv()

class ConversationalResponseGenerator:
    """프롬프트 엔지니어링 기반 대화형 응답 생성기"""
    
    def __init__(self):
        """CLOVA Studio API 초기화"""
        # LLM_RAG_예제와 동일한 환경변수 사용
        self.api_key = os.getenv("CLOVASTUDIO_API_KEY") or os.getenv("CLOVA_STUDIO_KEY")
        
        # langchain_naver ChatClovaX 초기화
        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatClovaX(
                    model="HCX-003",  # 또는 HCX-007
                    api_key=self.api_key,
                    temperature=0.7,
                    max_tokens=100
                )
                self.use_langchain = True
                print("[INFO] langchain_naver ChatClovaX 초기화 성공")
            except Exception as e:
                print(f"[WARNING] ChatClovaX 초기화 실패: {e}")
                self.use_langchain = False
        else:
            self.use_langchain = False
            if not self.api_key:
                print("[WARNING] CLOVA Studio API 키가 없습니다.")
        
        # 대화 기본 설정
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """개선된 시스템 프롬프트 생성"""
        return """당신은 공감형 감정 상담사입니다. 답변은 2-3문장, 최대 100자 이내로 작성합니다.

주요 역할:
1. 사용자의 감정을 깊이 이해하고 공감하기
2. 짧고 따뜻한 응답으로 위로하기
3. 자연스럽게 추가 이야기를 유도하기
4. 판단하지 않고 들어주기

문장 규칙:
- 각 문장은 완전한 문장으로 끝냅니다 (어절/조사/연결어로 끝내지 말 것)
- 마지막 문장은 '요.' 또는 '다.'와 같은 종결형으로 끝냅니다
- 줄임표(...) 남용 금지, 이모지는 최대 1개만 사용
- 방식: 공감 → 짧은 위로/축하 → 질문으로 대화 이어가기

감정별 대응:
- 기쁨: 함께 기뻐하고 더 자세한 이야기 묻기
- 슬픔: 위로하고 힘든 마음 이해한다고 표현
- 분노: 화난 마음 이해하고 상황 더 물어보기
- 불안: 걱정을 덜어주고 괜찮다고 안심시키기
- 당황: 놀랐을 마음 이해하고 진정시키기
- 상처: 마음 아픈 것 공감하고 따뜻하게 감싸주기

안전 규칙:
- 심리상담·의료적 진단/치료를 제시하지 않습니다
- 위기 신호가 보이면 전문가 상담을 권유합니다

출력 전 자체 점검:
- 답변이 100자 이내인가?
- 마지막 문장이 종결형으로 자연스럽게 끝났는가?
- 미완성 구/절로 끝나지 않았는가?

예시:
사용자: "오늘 시험을 망쳤어요"
응답: "많이 속상하시겠어요. 그래도 최선을 다하셨잖아요. 어떤 시험이었나요?"

사용자: "친구가 생일 파티에 초대해줬어요!"
응답: "정말 좋은 소식이네요! 기분이 좋으시겠어요. 언제 파티인가요?"
"""
    
    def generate_response(self, user_text: str, detected_emotion: str, 
                         conversation_history: List[Dict] = None) -> str:
        """
        대화형 응답 생성
        
        Args:
            user_text: 사용자 입력
            detected_emotion: 검출된 감정
            conversation_history: 이전 대화 기록
            
        Returns:
            생성된 응답 텍스트
        """
        try:
            # 대화 맥락 구성
            messages = self._build_conversation_context(
                user_text, detected_emotion, conversation_history
            )
            
            # CLOVA Studio API 호출
            response = self._call_clova_studio(messages)
            
            if response:
                # 응답 후처리 (길이 제한, 톤 조정)
                return self._post_process_response(response, detected_emotion)
            else:
                # API 실패 시 감정별 기본 응답
                return self._get_fallback_response(user_text, detected_emotion)
                
        except Exception as e:
            print(f"[ERROR] 응답 생성 실패: {e}")
            return self._get_fallback_response(user_text, detected_emotion)
    
    def _build_conversation_context(self, user_text: str, detected_emotion: str,
                                  conversation_history: List[Dict] = None) -> List[Dict]:
        """대화 맥락 구성"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 이전 대화 기록 추가 (최근 3턴만)
        if conversation_history:
            recent_history = conversation_history[-3:]  # 최근 3턴
            for turn in recent_history:
                messages.append({"role": "user", "content": turn.get("user_input", "")})
                messages.append({"role": "assistant", "content": turn.get("bot_response", "")})
        
        # 현재 사용자 입력과 감정 정보 추가
        current_prompt = f"""사용자 메시지: "{user_text}"
감지된 감정: {detected_emotion}

위 메시지에 담긴 {detected_emotion} 감정을 깊이 공감하며, 짧고 따뜻하게 응답해주세요. 
그리고 자연스럽게 추가 이야기를 물어보세요."""
        
        messages.append({"role": "user", "content": current_prompt})
        
        return messages
    
    def _call_clova_studio(self, messages: List[Dict]) -> Optional[str]:
        """CLOVA Studio Chat Completion API 호출 - langchain_naver 사용"""
        if not self.use_langchain:
            print("[WARNING] langchain_naver가 초기화되지 않았습니다. 기본 응답을 사용합니다.")
            return None
        
        try:
            # langchain 메시지 형식으로 변환
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # ChatClovaX 호출
            response = self.llm.invoke(langchain_messages)
            
            # 응답 추출
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"[WARNING] ChatClovaX API 호출 실패: {e}")
        
        return None
    
    def _post_process_response(self, response: str, emotion: str) -> str:
        """응답 후처리"""
        # 길이 제한 (100자 이내)
        if len(response) > 100:
            sentences = response.split('. ')
            if len(sentences) > 1:
                response = sentences[0] + '. ' + sentences[1]
            else:
                response = response[:97] + "..."
        
        # 감정별 톤 조정
        response = response.replace("니다", "네요").replace("습니다", "어요")
        
        # 질문이 없으면 자연스럽게 추가
        if not any(q in response for q in ['?', '까요', '어요?', '세요?']):
            emotion_questions = {
                "기쁨": " 더 자세히 들려주세요!",
                "슬픔": " 힘든 마음을 더 말씀해주세요.",
                "분노": " 어떤 상황이었는지 궁금해요.",
                "불안": " 걱정되는 마음 이해해요. 괜찮을 거예요.",
                "당황": " 놀라셨겠어요. 어떻게 된 일인가요?",
                "상처": " 마음이 많이 아프시겠어요."
            }
            
            if emotion in emotion_questions:
                response += emotion_questions[emotion]
        
        return response
    
    def _get_fallback_response(self, user_text: str, emotion: str) -> str:
        """API 실패 시 감정 기반 기본 응답"""
        # 키워드 추출
        keywords = self._extract_keywords(user_text)
        
        # 감정별 기본 응답 패턴
        emotion_responses = {
            "기쁨": [
                "정말 기뻐보여요! {keyword}는 어때요?",
                "좋은 소식이네요! 더 들려주세요.",
                "함께 기뻐해요! 어떤 기분이세요?"
            ],
            "슬픔": [
                "마음이 아프시겠어요. {keyword} 때문에 힘드시죠?",
                "속상하시겠어요. 제가 들어드릴게요.",
                "힘든 시간이네요. 괜찮아질 거예요."
            ],
            "분노": [
                "정말 화나셨겠어요. {keyword} 상황이 어떻게 됐나요?",
                "짜증나시겠네요. 충분히 이해돼요.",
                "그런 일이 있으셨군요. 어떻게 된 건가요?"
            ],
            "불안": [
                "걱정이 많으시겠어요. {keyword} 때문인가요?",
                "불안하시겠네요. 괜찮을 거예요.",
                "걱정되는 마음 이해해요. 어떤 상황인가요?"
            ],
            "당황": [
                "갑작스러우셨겠어요. {keyword}는 어떻게 하실 건가요?",
                "당황스러우시겠네요. 차근차근 해봐요.",
                "놀라셨겠어요. 어떤 일인가요?"
            ],
            "상처": [
                "마음이 아프시겠어요. {keyword} 때문에 힘드시죠?",
                "상처받으셨군요. 이해해요.",
                "힘드시겠어요. 제가 함께 있어드릴게요."
            ]
        }
        
        import random
        templates = emotion_responses.get(emotion, emotion_responses["기쁨"])
        template = random.choice(templates)
        
        # 키워드 대체
        if keywords and "{keyword}" in template:
            keyword = keywords[0]
            return template.format(keyword=keyword)
        else:
            return template.replace("{keyword} ", "").replace(" {keyword}", "")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """주요 키워드 추출"""
        important_words = [
            "가족", "엄마", "아빠", "친구", "연인", "회사", "일", "직장", "상사", 
            "학교", "공부", "시험", "과제", "성적", "취업", "면접", "돈", "건강",
            "여행", "파티", "생일", "축하", "선물", "음식", "영화", "게임",
            "집", "방", "침대", "거리", "카페", "식당", "병원"
        ]
        
        found_keywords = []
        for word in important_words:
            if word in text:
                found_keywords.append(word)
        
        return found_keywords[:2]  # 최대 2개