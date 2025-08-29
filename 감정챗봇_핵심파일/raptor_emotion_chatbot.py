"""
RAPTOR RAG 기반 감정 대화 챗봇 시스템
- 음성(STT) 및 텍스트 입력 지원
- 실시간 감정 인식 및 공감 응답
- 대화 종료 후 일기 요약 및 분석
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# =====================================
# 데이터 클래스 정의
# =====================================

@dataclass
class ConversationTurn:
    """대화 턴 데이터 구조"""
    turn_number: int
    user_input: str
    detected_emotion: str
    emotion_confidence: float
    bot_response: str
    timestamp: str
    input_type: str  # 'text' or 'voice'

@dataclass
class EmotionAnalysis:
    """감정 분석 결과"""
    dominant_emotion: str
    emotion_distribution: Dict[str, float]  # {"기쁨": 0.6, "슬픔": 0.3, "분노": 0.1}
    top_3_emotions: List[Tuple[str, float]]  # [("기쁨", 60), ("슬픔", 30), ("분노", 10)]

@dataclass
class DiaryEntry:
    """일기 요약 구조"""
    summary: str
    cause: str
    advice: str
    todo_today: str
    todo_tomorrow: str
    todo_day_after: str
    todo_d3: str
    emotion_analysis: EmotionAnalysis
    conversation_history: List[ConversationTurn]

# =====================================
# RAPTOR 계층적 검색 시스템
# =====================================

class RAPTOREmotionSearch:
    """RAPTOR 계층적 감정 검색 시스템"""
    
    def __init__(self):
        """RAPTOR 시스템 초기화"""
        print("[INFO] RAPTOR 감정 검색 시스템 초기화 중...")
        
        # SentenceTransformer 모델 로드
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        try:
            # L1: 감정별 대표 벡터 로드
            with np.load('raptor_l1_cluster_embeddings.npz') as data:
                self.l1_embeddings = {key: data[key] for key in data.keys()}
            
            # L2: 감정-상황별 대표 벡터 로드
            with np.load('raptor_l2_cluster_embeddings.npz') as data:
                self.l2_embeddings = {key: data[key] for key in data.keys()}
            
            # L3: 개별 텍스트 벡터 로드
            self.l3_embeddings = np.load('raptor_sampled_embeddings.npy')
            self.l3_data = pd.read_csv('raptor_sampled_data.csv', encoding='utf-8-sig')
            
            print(f"[OK] RAPTOR 시스템 로드 완료")
            print(f"  L1 클러스터: {len(self.l1_embeddings)}개")
            print(f"  L2 클러스터: {len(self.l2_embeddings)}개")
            print(f"  L3 텍스트: {len(self.l3_embeddings)}개")
            
        except Exception as e:
            print(f"[ERROR] RAPTOR 데이터 로드 실패: {e}")
            raise
    
    def detect_emotion(self, text: str) -> Tuple[str, float]:
        """
        텍스트에서 감정 검출 (RAPTOR 계층적 검색)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (감정, 신뢰도) 튜플
        """
        # 쿼리 임베딩 생성
        query_embedding = self.model.encode([text])[0]
        
        # L1 감정 클러스터 검색
        l1_similarities = {}
        for emotion_cluster, embedding in self.l1_embeddings.items():
            similarity = np.dot(embedding, query_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(query_embedding)
            )
            emotion = emotion_cluster.replace('emotion_', '')
            l1_similarities[emotion] = similarity
        
        # 가장 유사한 감정 선택
        best_emotion = max(l1_similarities, key=l1_similarities.get)
        confidence = l1_similarities[best_emotion]
        
        # L2, L3 검색은 필요시 추가 (현재는 빠른 응답을 위해 L1만 사용)
        
        return best_emotion, float(confidence)
    
    def find_similar_responses(self, text: str, emotion: str, top_k: int = 3) -> List[str]:
        """
        유사한 감정 상황의 응답 찾기
        
        Args:
            text: 입력 텍스트
            emotion: 검출된 감정
            top_k: 반환할 유사 텍스트 수
            
        Returns:
            유사한 상황의 텍스트 리스트
        """
        query_embedding = self.model.encode([text])[0]
        
        # 해당 감정의 텍스트만 필터링
        emotion_mask = self.l3_data['emotion_major'] == emotion
        filtered_indices = self.l3_data[emotion_mask].index.tolist()
        
        if not filtered_indices:
            filtered_indices = list(range(len(self.l3_data)))
        
        # 유사도 계산
        filtered_embeddings = self.l3_embeddings[filtered_indices]
        similarities = np.dot(filtered_embeddings, query_embedding) / (
            np.linalg.norm(filtered_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Top-K 선택
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        similar_texts = []
        for idx in top_indices:
            original_idx = filtered_indices[idx]
            similar_texts.append(self.l3_data.iloc[original_idx]['text'])
        
        return similar_texts

# =====================================
# STT (음성 인식) 시스템
# =====================================

class ClovaSTT:
    """CLOVA Speech Recognition 시스템"""
    
    def __init__(self):
        """STT 시스템 초기화"""
        self.client_id = os.getenv("CLOVA_CLIENT_ID", "i44O37OUtVx0tzYCAw0z")
        self.client_secret = os.getenv("CLOVA_CLIENT_SECRET")
        self.api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"
        
    def recognize_speech(self, audio_file_path: str, lang: str = "Kor") -> str:
        """
        음성 파일을 텍스트로 변환
        
        Args:
            audio_file_path: 음성 파일 경로
            lang: 언어 설정 (기본값: Kor)
            
        Returns:
            인식된 텍스트
        """
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
            "Content-Type": "application/octet-stream"
        }
        
        params = {"lang": lang}
        
        try:
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            response = requests.post(
                self.api_url,
                headers=headers,
                params=params,
                data=audio_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                print(f"[ERROR] STT 실패: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"[ERROR] STT 처리 오류: {e}")
            return ""

# =====================================
# 응답 생성 시스템
# =====================================

# 대화형 응답 생성기 import
from conversational_response_generator import ConversationalResponseGenerator

class EmpatheticResponseGenerator:
    """공감 응답 생성기 - 대화형 AI 기반"""
    
    def __init__(self):
        """대화형 응답 생성기 초기화"""
        try:
            # CLOVA Studio 기반 대화형 생성기 시도
            self.conversational_generator = ConversationalResponseGenerator()
            self.use_ai_generation = True
            print("[INFO] 대화형 AI 응답 생성기 활성화")
        except Exception as e:
            print(f"[WARNING] 대화형 AI 로드 실패: {e}")
            self.use_ai_generation = False
    
    # 기존 템플릿 (AI 실패 시 백업용)
    RESPONSE_TEMPLATES = {
        "기쁨": [
            "정말 기뻐보여요! 더 자세히 들려주세요!",
            "와 좋겠어요! 어떤 기분이세요?",
            "함께 기뻐해요! 무슨 일인가요?"
        ],
        "슬픔": [
            "마음이 아프시겠어요. 괜찮을 거예요. 어떤 일이 있었나요?",
            "힘드시겠네요. 더 말씀해주세요.",
            "속상하시겠어요. 제가 들어드릴게요."
        ],
        "분노": [
            "정말 화나셨겠어요. 어떤 상황인가요?",
            "짜증나시겠네요. 충분히 이해돼요. 무슨 일이죠?",
            "화난 마음 이해해요. 더 말씀해주세요."
        ],
        "불안": [
            "걱정이 많으시겠어요. 괜찮을 거예요. 뭐 때문인가요?",
            "불안하시겠네요. 어떤 걱정이 있으세요?",
            "긴장되시는군요. 천천히 말씀해주세요."
        ],
        "당황": [
            "갑작스러우셨겠어요. 어떻게 된 일인가요?",
            "당황스러우시겠네요. 무슨 일이 있었나요?",
            "놀라셨겠어요. 어떤 상황이었어요?"
        ],
        "상처": [
            "마음이 아프시겠어요. 힘든 일이 있으셨나요?",
            "상처받으셨군요. 어떤 일인지 말씀해주세요.",
            "힘드시겠어요. 제가 함께 있어드릴게요."
        ]
    }
    
    def generate_empathetic_response(self, text: str, emotion: str, 
                                   similar_contexts: List[str] = None,
                                   conversation_history: List = None) -> str:
        """
        공감 응답 생성 - AI 기반 또는 템플릿 기반
        
        Args:
            text: 사용자 입력
            emotion: 검출된 감정
            similar_contexts: 유사한 맥락 (선택적)
            conversation_history: 대화 기록 (선택적)
            
        Returns:
            공감 응답 텍스트
        """
        # 1순위: 대화형 AI 생성 시도
        if self.use_ai_generation:
            try:
                ai_response = self.conversational_generator.generate_response(
                    text, emotion, conversation_history
                )
                if ai_response and len(ai_response.strip()) > 5:
                    return ai_response
                else:
                    print("[WARNING] AI 응답이 너무 짧습니다. 템플릿을 사용합니다.")
            except Exception as e:
                print(f"[WARNING] AI 응답 생성 실패: {e}")
        
        # 2순위: 개선된 템플릿 기반 응답 (AI 실패 시)
        return self._generate_template_response(text, emotion, similar_contexts)
    
    def _generate_template_response(self, text: str, emotion: str, similar_contexts: List[str] = None) -> str:
        """템플릿 기반 응답 생성 (개선된 버전)"""
        # 기본 템플릿 선택
        if emotion in self.RESPONSE_TEMPLATES:
            import random
            base_response = random.choice(self.RESPONSE_TEMPLATES[emotion])
        else:
            base_response = "그런 기분이시군요. 더 말씀해주세요."
        
        # 키워드 기반 맞춤화 (기존 로직 유지)
        keywords = self._extract_keywords(text)
        
        if keywords:
            if "엄마" in keywords or "부모" in keywords:
                base_response = base_response.replace("더 말씀해주세요.", "가족 관계는 어떠세요?")
            elif "친구" in keywords:
                base_response = base_response.replace("더 말씀해주세요.", "친구와는 어떤 일이 있었나요?")
            elif "회사" in keywords or "일" in keywords:
                base_response = base_response.replace("더 말씀해주세요.", "직장에서 무슨 일이 있었나요?")
            elif "학교" in keywords or "공부" in keywords:
                base_response = base_response.replace("더 말씀해주세요.", "학업 스트레스가 심한가요?")
        
        return base_response
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 주요 키워드 추출"""
        important_words = ["엄마", "아빠", "부모", "친구", "회사", "일", "학교", "공부", "시험", "과제"]
        found_keywords = []
        
        for word in important_words:
            if word in text:
                found_keywords.append(word)
        
        return found_keywords

# =====================================
# 일기 요약 생성 시스템
# =====================================

class DiaryGenerator:
    """일기 요약 생성기"""
    
    def generate_diary_entry(self, conversation_history: List[ConversationTurn]) -> DiaryEntry:
        """
        대화 히스토리를 기반으로 일기 생성
        
        Args:
            conversation_history: 대화 턴 리스트
            
        Returns:
            구조화된 일기 엔트리
        """
        # 감정 통계 분석
        emotion_counts = Counter([turn.detected_emotion for turn in conversation_history])
        total_turns = len(conversation_history)
        
        # 감정 분포 계산
        emotion_distribution = {
            emotion: (count / total_turns) for emotion, count in emotion_counts.items()
        }
        
        # Top 3 감정
        top_3_emotions = [
            (emotion, round(ratio * 100, 1)) 
            for emotion, ratio in sorted(emotion_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        
        # 대표 감정
        dominant_emotion = top_3_emotions[0][0] if top_3_emotions else "기쁨"
        
        # 감정 분석 객체 생성
        emotion_analysis = EmotionAnalysis(
            dominant_emotion=dominant_emotion,
            emotion_distribution=emotion_distribution,
            top_3_emotions=top_3_emotions
        )
        
        # 대화 내용 요약
        user_texts = [turn.user_input for turn in conversation_history]
        summary = self._generate_summary(user_texts, dominant_emotion)
        
        # 원인 분석
        cause = self._analyze_cause(user_texts, emotion_counts)
        
        # 조언 생성
        advice = self._generate_advice(dominant_emotion, emotion_counts)
        
        # 투두리스트 생성
        todos = self._generate_todos(dominant_emotion, user_texts)
        
        return DiaryEntry(
            summary=summary,
            cause=cause,
            advice=advice,
            todo_today=todos["today"],
            todo_tomorrow=todos["tomorrow"],
            todo_day_after=todos["day_after"],
            todo_d3=todos["d3"],
            emotion_analysis=emotion_analysis,
            conversation_history=conversation_history
        )
    
    def _generate_summary(self, user_texts: List[str], dominant_emotion: str) -> str:
        """대화 내용 요약"""
        # 간단한 요약 생성 (실제로는 더 복잡한 로직 필요)
        summary = f"오늘은 주로 {dominant_emotion}의 감정을 느끼는 하루였습니다. "
        
        if len(user_texts) > 0:
            # 첫 번째와 마지막 대화 참조
            summary += f"'{user_texts[0][:30]}...'로 시작해서 "
            if len(user_texts) > 1:
                summary += f"'{user_texts[-1][:30]}...'로 마무리되었습니다."
        
        return summary
    
    def _analyze_cause(self, user_texts: List[str], emotion_counts: Counter) -> str:
        """감정의 원인 분석"""
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "기쁨"
        
        cause_analysis = f"{dominant_emotion} 감정의 주요 원인은 "
        
        # 키워드 기반 원인 추론
        all_text = " ".join(user_texts)
        
        if "가족" in all_text or "엄마" in all_text or "아빠" in all_text:
            cause_analysis += "가족 관계에서 비롯된 것으로 보입니다."
        elif "친구" in all_text:
            cause_analysis += "친구 관계에서 발생한 것으로 보입니다."
        elif "일" in all_text or "회사" in all_text:
            cause_analysis += "업무 스트레스와 관련이 있어 보입니다."
        else:
            cause_analysis += "일상적인 상황들이 복합적으로 작용한 것 같습니다."
        
        return cause_analysis
    
    def _generate_advice(self, dominant_emotion: str, emotion_counts: Counter) -> str:
        """감정별 맞춤 조언 생성"""
        advice_map = {
            "기쁨": "좋은 감정을 유지하며 감사 일기를 써보세요.",
            "슬픔": "충분한 휴식을 취하고 좋아하는 활동을 해보세요.",
            "분노": "심호흡을 하고 운동으로 스트레스를 해소해보세요.",
            "불안": "명상이나 요가로 마음을 안정시켜보세요.",
            "당황": "차분히 상황을 정리하고 우선순위를 정해보세요.",
            "상처": "자신을 위로하고 친한 사람과 대화를 나눠보세요."
        }
        
        return advice_map.get(dominant_emotion, "오늘 하루도 수고하셨어요. 충분한 휴식을 취하세요.")
    
    def _generate_todos(self, dominant_emotion: str, user_texts: List[str]) -> Dict[str, str]:
        """감정 개선을 위한 투두리스트 생성"""
        todos = {
            "기쁨": {
                "today": "오늘 있었던 좋은 일 3가지 적어보기",
                "tomorrow": "감사한 사람에게 연락하기",
                "day_after": "좋아하는 취미 활동 30분",
                "d3": "주변 사람들과 긍정적인 경험 공유하기"
            },
            "슬픔": {
                "today": "좋아하는 음악 들으며 산책하기",
                "tomorrow": "친한 친구와 대화 나누기",
                "day_after": "새로운 취미 활동 시도해보기",
                "d3": "자기 관리 시간 갖기 (마사지, 목욕 등)"
            },
            "분노": {
                "today": "10분 명상 또는 심호흡 운동",
                "tomorrow": "운동으로 스트레스 해소하기",
                "day_after": "화났던 상황 객관적으로 일기 쓰기",
                "d3": "스트레스 관리 방법 하나 배우기"
            },
            "불안": {
                "today": "걱정 노트에 불안한 내용 적고 정리하기",
                "tomorrow": "요가나 스트레칭 20분",
                "day_after": "불안 완화 호흡법 연습",
                "d3": "전문가 상담 예약 고려하기"
            },
            "당황": {
                "today": "오늘 일정 다시 정리하고 우선순위 정하기",
                "tomorrow": "비슷한 상황 대비 계획 세우기",
                "day_after": "스트레스 관리 기술 하나 배우기",
                "d3": "유사 상황 시뮬레이션 해보기"
            },
            "상처": {
                "today": "자기 위로의 시간 갖기 (좋아하는 것 하기)",
                "tomorrow": "신뢰하는 사람과 감정 공유하기",
                "day_after": "회복을 위한 셀프케어 활동",
                "d3": "긍정적인 자기 대화 연습하기"
            }
        }
        
        return todos.get(dominant_emotion, {
            "today": "오늘 하루 돌아보며 일기 쓰기",
            "tomorrow": "좋아하는 활동 한 가지 하기",
            "day_after": "새로운 것 하나 시도해보기",
            "d3": "자기 관리 시간 갖기"
        })

# =====================================
# 메인 챗봇 시스템
# =====================================

class EmotionChatbot:
    """감정 대화 챗봇 메인 시스템"""
    
    def __init__(self):
        """챗봇 시스템 초기화"""
        print("[INFO] 감정 대화 챗봇 초기화 중...")
        
        # 컴포넌트 초기화
        self.raptor_search = RAPTOREmotionSearch()
        self.stt_system = ClovaSTT()
        self.response_generator = EmpatheticResponseGenerator()
        self.diary_generator = DiaryGenerator()
        
        # 대화 히스토리
        self.conversation_history: List[ConversationTurn] = []
        self.turn_counter = 0
        
        print("[OK] 챗봇 시스템 준비 완료")
    
    def process_input(self, input_data: Union[str, bytes], input_type: str = "text") -> Dict:
        """
        사용자 입력 처리 (텍스트 또는 음성)
        
        Args:
            input_data: 텍스트 문자열 또는 음성 바이트 데이터
            input_type: "text" 또는 "voice"
            
        Returns:
            응답 딕셔너리
        """
        # 1. 입력 처리
        if input_type == "voice":
            # 음성을 텍스트로 변환
            # 실제 구현시에는 임시 파일로 저장 후 처리
            user_text = self.stt_system.recognize_speech(input_data)
            if not user_text:
                return {
                    "status": "error",
                    "message": "음성 인식 실패"
                }
        else:
            user_text = input_data
        
        # 2. 감정 검출
        detected_emotion, confidence = self.raptor_search.detect_emotion(user_text)
        
        # 3. 유사 컨텍스트 검색
        similar_contexts = self.raptor_search.find_similar_responses(user_text, detected_emotion)
        
        # 4. 공감 응답 생성 (대화 기록 포함)
        # 이전 대화들을 딕셔너리 형태로 변환
        conversation_dict = []
        for turn in self.conversation_history[-3:]:  # 최근 3턴만
            conversation_dict.append({
                "user_input": turn.user_input,
                "bot_response": turn.bot_response
            })
        
        bot_response = self.response_generator.generate_empathetic_response(
            user_text, detected_emotion, similar_contexts, conversation_dict
        )
        
        # 5. 대화 턴 저장
        self.turn_counter += 1
        turn = ConversationTurn(
            turn_number=self.turn_counter,
            user_input=user_text,
            detected_emotion=detected_emotion,
            emotion_confidence=confidence,
            bot_response=bot_response,
            timestamp=datetime.now().isoformat(),
            input_type=input_type
        )
        self.conversation_history.append(turn)
        
        # 6. 응답 반환
        return {
            "status": "success",
            "turn_number": self.turn_counter,
            "user_input": user_text,
            "detected_emotion": detected_emotion,
            "emotion_confidence": round(confidence * 100, 1),
            "bot_response": bot_response,
            "timestamp": turn.timestamp
        }
    
    def generate_diary_summary(self) -> Dict:
        """
        대화 종료 후 일기 요약 생성
        
        Returns:
            구조화된 일기 데이터
        """
        if not self.conversation_history:
            return {
                "status": "error",
                "message": "대화 기록이 없습니다"
            }
        
        # 일기 생성
        diary_entry = self.diary_generator.generate_diary_entry(self.conversation_history)
        
        # 파싱 가능한 형식으로 변환
        formatted_output = {
            "status": "success",
            "diary": {
                "<<일기 요약>>": diary_entry.summary,
                "<<원인>>": diary_entry.cause,
                "<<조언>>": diary_entry.advice,
                "<<투두리스트>>": {
                    "<<오늘>>": diary_entry.todo_today,
                    "<<내일>>": diary_entry.todo_tomorrow,
                    "<<모레>>": diary_entry.todo_day_after,
                    "<<D-3>>": diary_entry.todo_d3
                }
            },
            "emotion_analysis": {
                "dominant_emotion": diary_entry.emotion_analysis.dominant_emotion,
                "top_3_emotions": [
                    {
                        "emotion": emotion,
                        "percentage": percentage
                    }
                    for emotion, percentage in diary_entry.emotion_analysis.top_3_emotions
                ],
                "full_distribution": diary_entry.emotion_analysis.emotion_distribution
            },
            "conversation_stats": {
                "total_turns": len(self.conversation_history),
                "start_time": self.conversation_history[0].timestamp,
                "end_time": self.conversation_history[-1].timestamp
            }
        }
        
        return formatted_output
    
    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
        self.turn_counter = 0
        print("[INFO] 대화 히스토리가 초기화되었습니다")

# =====================================
# API 엔드포인트 테스트
# =====================================

def test_chatbot():
    """챗봇 시스템 테스트"""
    print("\n=== 감정 대화 챗봇 테스트 ===\n")
    
    # 챗봇 초기화
    chatbot = EmotionChatbot()
    
    # 테스트 대화
    test_conversations = [
        "아 진짜 엄마가 나 학원가라는데 너무 빡치네",
        "그래도 친구들이 응원해줘서 조금 나아졌어",
        "내일 시험인데 너무 불안해",
        "그래도 열심히 했으니까 잘 볼 수 있을 거야",
        "오늘 정말 힘든 하루였어"
    ]
    
    print("--- 실시간 대화 처리 ---\n")
    for text in test_conversations:
        print(f"사용자: {text}")
        response = chatbot.process_input(text, input_type="text")
        print(f"봇: {response['bot_response']}")
        print(f"[감정: {response['detected_emotion']} ({response['emotion_confidence']}%)]")
        print()
    
    print("\n--- 일기 요약 생성 ---\n")
    diary = chatbot.generate_diary_summary()
    
    # 일기 출력
    print(json.dumps(diary, ensure_ascii=False, indent=2))
    
    # 파일로 저장
    output_file = f"diary_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(diary, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SUCCESS] 일기가 {output_file}에 저장되었습니다")

if __name__ == "__main__":
    test_chatbot()