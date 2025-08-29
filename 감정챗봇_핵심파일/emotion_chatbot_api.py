"""
감정 대화 챗봇 REST API 서버
Flask 기반 백엔드 API 엔드포인트
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import tempfile

# 챗봇 시스템 import
from raptor_emotion_chatbot import EmotionChatbot

# Flask 앱 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# CORS 설정 (프론트엔드 연동용)
CORS(app, supports_credentials=True)

# 세션별 챗봇 인스턴스 저장
chatbot_sessions = {}

# 허용된 음성 파일 확장자
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a'}

def allowed_audio_file(filename):
    """음성 파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def get_or_create_chatbot(session_id: str) -> EmotionChatbot:
    """세션별 챗봇 인스턴스 반환 또는 생성"""
    if session_id not in chatbot_sessions:
        chatbot_sessions[session_id] = EmotionChatbot()
    return chatbot_sessions[session_id]

def cleanup_old_sessions():
    """24시간 이상된 세션 정리"""
    # 실제 운영시 구현 필요
    pass

# =====================================
# API 엔드포인트
# =====================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    헬스체크 엔드포인트
    
    Returns:
        - 200: 서버 정상 작동
    """
    return jsonify({
        "status": "healthy",
        "service": "Emotion Chatbot API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """
    새 대화 세션 생성
    
    Body (optional):
        {
            "user_id": "string",  # 사용자 식별자 (선택적)
            "metadata": {}        # 추가 메타데이터 (선택적)
        }
    
    Returns:
        {
            "session_id": "string",
            "created_at": "datetime",
            "expires_at": "datetime"
        }
    """
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    # 챗봇 인스턴스 생성
    chatbot = get_or_create_chatbot(session_id)
    
    # 요청 데이터 처리
    data = request.get_json() or {}
    
    response = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "user_id": data.get("user_id"),
        "metadata": data.get("metadata", {})
    }
    
    return jsonify(response), 201

@app.route('/api/chat/text', methods=['POST'])
def chat_text():
    """
    텍스트 입력 처리 엔드포인트
    
    Headers:
        - Content-Type: application/json
        
    Body:
        {
            "text": "string",        # 사용자 입력 텍스트 (필수)
            "session_id": "string"   # 세션 ID (필수)
        }
    
    Returns:
        {
            "status": "success",
            "turn_number": int,
            "user_input": "string",
            "detected_emotion": "string",
            "emotion_confidence": float,
            "bot_response": "string",
            "timestamp": "datetime"
        }
    """
    try:
        data = request.get_json()
        
        # 필수 파라미터 검증
        if not data or 'text' not in data or 'session_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameters: text and session_id"
            }), 400
        
        text = data['text']
        session_id = data['session_id']
        
        # 챗봇 인스턴스 가져오기
        chatbot = get_or_create_chatbot(session_id)
        
        # 텍스트 처리
        response = chatbot.process_input(text, input_type="text")
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/chat/voice', methods=['POST'])
def chat_voice():
    """
    음성 입력 처리 엔드포인트
    
    Headers:
        - Content-Type: multipart/form-data
        
    Form Data:
        - audio: 음성 파일 (필수)
        - session_id: 세션 ID (필수)
    
    Returns:
        {
            "status": "success",
            "turn_number": int,
            "user_input": "string",      # STT 변환된 텍스트
            "detected_emotion": "string",
            "emotion_confidence": float,
            "bot_response": "string",
            "timestamp": "datetime"
        }
    """
    try:
        # 세션 ID 확인
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({
                "status": "error",
                "message": "Missing session_id"
            }), 400
        
        # 음성 파일 확인
        if 'audio' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No audio file provided"
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
        
        if not allowed_audio_file(audio_file.filename):
            return jsonify({
                "status": "error",
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
            }), 400
        
        # 임시 파일로 저장
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        audio_file.save(temp_path)
        
        try:
            # 챗봇 인스턴스 가져오기
            chatbot = get_or_create_chatbot(session_id)
            
            # 음성 처리 (파일 경로 전달)
            response = chatbot.process_input(temp_path, input_type="voice")
            
            return jsonify(response), 200
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/diary/generate', methods=['POST'])
def generate_diary():
    """
    대화 종료 후 일기 요약 생성
    
    Body:
        {
            "session_id": "string"   # 세션 ID (필수)
        }
    
    Returns:
        {
            "status": "success",
            "diary": {
                "<<일기 요약>>": "string",
                "<<원인>>": "string",
                "<<조언>>": "string",
                "<<투두리스트>>": {
                    "<<오늘>>": "string",
                    "<<내일>>": "string",
                    "<<모레>>": "string",
                    "<<D-3>>": "string"
                }
            },
            "emotion_analysis": {
                "dominant_emotion": "string",
                "top_3_emotions": [
                    {
                        "emotion": "string",
                        "percentage": float
                    }
                ],
                "full_distribution": {}
            },
            "conversation_stats": {
                "total_turns": int,
                "start_time": "datetime",
                "end_time": "datetime"
            }
        }
    """
    try:
        data = request.get_json()
        
        # 세션 ID 확인
        if not data or 'session_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing session_id"
            }), 400
        
        session_id = data['session_id']
        
        # 챗봇 인스턴스 확인
        if session_id not in chatbot_sessions:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        chatbot = chatbot_sessions[session_id]
        
        # 일기 생성
        diary_response = chatbot.generate_diary_summary()
        
        return jsonify(diary_response), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/session/reset', methods=['POST'])
def reset_session():
    """
    대화 세션 초기화
    
    Body:
        {
            "session_id": "string"   # 세션 ID (필수)
        }
    
    Returns:
        {
            "status": "success",
            "message": "Session reset successfully",
            "session_id": "string"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing session_id"
            }), 400
        
        session_id = data['session_id']
        
        if session_id in chatbot_sessions:
            chatbot_sessions[session_id].reset_conversation()
            
            return jsonify({
                "status": "success",
                "message": "Session reset successfully",
                "session_id": session_id
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/session/history', methods=['GET'])
def get_conversation_history():
    """
    대화 히스토리 조회
    
    Query Parameters:
        - session_id: 세션 ID (필수)
    
    Returns:
        {
            "status": "success",
            "session_id": "string",
            "conversation_history": [
                {
                    "turn_number": int,
                    "user_input": "string",
                    "detected_emotion": "string",
                    "emotion_confidence": float,
                    "bot_response": "string",
                    "timestamp": "datetime",
                    "input_type": "string"
                }
            ],
            "total_turns": int
        }
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                "status": "error",
                "message": "Missing session_id parameter"
            }), 400
        
        if session_id not in chatbot_sessions:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        chatbot = chatbot_sessions[session_id]
        
        # 대화 히스토리를 딕셔너리로 변환
        history = []
        for turn in chatbot.conversation_history:
            history.append({
                "turn_number": turn.turn_number,
                "user_input": turn.user_input,
                "detected_emotion": turn.detected_emotion,
                "emotion_confidence": round(turn.emotion_confidence * 100, 1),
                "bot_response": turn.bot_response,
                "timestamp": turn.timestamp,
                "input_type": turn.input_type
            })
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "conversation_history": history,
            "total_turns": len(history)
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/emotions/list', methods=['GET'])
def list_emotions():
    """
    지원되는 감정 목록 조회
    
    Returns:
        {
            "emotions": ["기쁨", "슬픔", "분노", "불안", "당황", "상처"],
            "descriptions": {
                "기쁨": "긍정적이고 즐거운 감정",
                ...
            }
        }
    """
    emotions_info = {
        "emotions": ["기쁨", "슬픔", "분노", "불안", "당황", "상처"],
        "descriptions": {
            "기쁨": "긍정적이고 즐거운 감정",
            "슬픔": "우울하고 침울한 감정",
            "분노": "화나고 짜증나는 감정",
            "불안": "걱정되고 불안한 감정",
            "당황": "당황하고 혼란스러운 감정",
            "상처": "마음이 아프고 상처받은 감정"
        }
    }
    
    return jsonify(emotions_info), 200

# =====================================
# 에러 핸들러
# =====================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

# =====================================
# 메인 실행
# =====================================

if __name__ == '__main__':
    print("""
    ====================================
    감정 대화 챗봇 API 서버
    ====================================
    
    엔드포인트:
    - POST /api/session/create       : 새 세션 생성
    - POST /api/chat/text           : 텍스트 입력 처리
    - POST /api/chat/voice          : 음성 입력 처리
    - POST /api/diary/generate      : 일기 요약 생성
    - POST /api/session/reset       : 세션 초기화
    - GET  /api/session/history     : 대화 히스토리 조회
    - GET  /api/emotions/list       : 감정 목록 조회
    - GET  /api/health              : 헬스체크
    
    서버 시작 중...
    """)
    
    # 환경에 따른 설정
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    # 서버 실행
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )