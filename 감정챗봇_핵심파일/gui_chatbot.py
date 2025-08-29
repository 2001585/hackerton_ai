# -*- coding: utf-8 -*-
"""
GUI 기반 감정 대화 챗봇
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
from raptor_emotion_chatbot import EmotionChatbot

class EmotionChatbotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("감정 대화 챗봇")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # 챗봇 인스턴스
        self.chatbot = None
        self.is_loading = False
        
        self.setup_ui()
        self.load_chatbot()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 제목
        title_label = ttk.Label(main_frame, text="🤖 RAPTOR RAG 감정 대화 챗봇", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 채팅 영역
        self.chat_area = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            font=("Arial", 10),
            bg='white',
            state=tk.DISABLED
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 입력 프레임
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 입력 창
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame, 
            textvariable=self.input_var,
            font=("Arial", 12)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        # 전송 버튼
        self.send_button = ttk.Button(
            input_frame, 
            text="전송", 
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 일기 생성 버튼
        self.diary_button = ttk.Button(
            button_frame, 
            text="📖 일기 생성", 
            command=self.generate_diary
        )
        self.diary_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 대화 초기화 버튼
        self.reset_button = ttk.Button(
            button_frame, 
            text="🔄 초기화", 
            command=self.reset_conversation
        )
        self.reset_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 종료 버튼
        self.quit_button = ttk.Button(
            button_frame, 
            text="❌ 종료", 
            command=self.quit_app
        )
        self.quit_button.pack(side=tk.RIGHT)
        
        # 상태바
        self.status_var = tk.StringVar()
        self.status_var.set("챗봇 로딩 중...")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 초기 메시지
        self.add_system_message("감정 대화 챗봇에 오신 것을 환영합니다!")
        self.add_system_message("6가지 감정(기쁨, 슬픔, 분노, 불안, 당황, 상처)을 인식합니다.")
    
    def load_chatbot(self):
        """백그라운드에서 챗봇 로드"""
        def load_in_background():
            try:
                self.add_system_message("RAPTOR 시스템 로딩 중... 잠시 기다려주세요.")
                self.chatbot = EmotionChatbot()
                self.status_var.set("준비 완료 - 자유롭게 대화하세요!")
                self.add_system_message("✅ 챗봇 준비 완료! 자유롭게 대화해보세요.")
                
                # 버튼 활성화
                self.send_button.config(state='normal')
                self.input_entry.config(state='normal')
                self.input_entry.focus()
                
            except Exception as e:
                error_msg = f"챗봇 로드 실패: {str(e)}"
                self.add_system_message(f"❌ {error_msg}")
                self.status_var.set("오류 발생")
                messagebox.showerror("오류", error_msg)
        
        # 초기 버튼 비활성화
        self.send_button.config(state='disabled')
        self.input_entry.config(state='disabled')
        
        # 백그라운드 스레드에서 로드
        thread = threading.Thread(target=load_in_background)
        thread.daemon = True
        thread.start()
    
    def add_system_message(self, message):
        """시스템 메시지 추가"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"[시스템] {message}\n\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def add_user_message(self, message):
        """사용자 메시지 추가"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"😊 당신: {message}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def add_bot_message(self, message, emotion=None, confidence=None):
        """봇 메시지 추가"""
        self.chat_area.config(state=tk.NORMAL)
        
        # 감정 이모지 매핑
        emotion_emojis = {
            "기쁨": "😊", "슬픔": "😢", "분노": "😠",
            "불안": "😰", "당황": "😵", "상처": "💔"
        }
        
        emoji = emotion_emojis.get(emotion, "🤖")
        self.chat_area.insert(tk.END, f"{emoji} 챗봇: {message}\n")
        
        if emotion and confidence:
            self.chat_area.insert(tk.END, f"💭 감정: {emotion} ({confidence}%)\n")
        
        self.chat_area.insert(tk.END, "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def send_message(self, event=None):
        """메시지 전송"""
        if self.is_loading or not self.chatbot:
            return
        
        message = self.input_var.get().strip()
        if not message:
            return
        
        # 입력 필드 클리어
        self.input_var.set("")
        
        # 사용자 메시지 표시
        self.add_user_message(message)
        
        # 봇 응답 생성 (백그라운드)
        def get_response():
            try:
                self.is_loading = True
                self.status_var.set("생각 중...")
                self.send_button.config(state='disabled')
                
                response = self.chatbot.process_input(message, input_type="text")
                
                if response["status"] == "success":
                    self.add_bot_message(
                        response["bot_response"],
                        response["detected_emotion"],
                        response["emotion_confidence"]
                    )
                else:
                    self.add_system_message(f"❌ 오류: {response.get('message', '알 수 없는 오류')}")
                
            except Exception as e:
                self.add_system_message(f"❌ 처리 오류: {str(e)}")
            finally:
                self.is_loading = False
                self.status_var.set("대화 중...")
                self.send_button.config(state='normal')
                self.input_entry.focus()
        
        # 백그라운드에서 응답 생성
        thread = threading.Thread(target=get_response)
        thread.daemon = True
        thread.start()
    
    def generate_diary(self):
        """일기 생성"""
        if not self.chatbot or not self.chatbot.conversation_history:
            messagebox.showwarning("경고", "대화 기록이 없어서 일기를 생성할 수 없습니다.")
            return
        
        def create_diary():
            try:
                self.status_var.set("일기 생성 중...")
                diary = self.chatbot.generate_diary_summary()
                
                if diary["status"] == "success":
                    # 새 창에 일기 표시
                    self.show_diary_window(diary)
                    
                    # 파일 저장
                    filename = f"diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(diary, f, ensure_ascii=False, indent=2)
                    
                    self.add_system_message(f"📖 일기가 생성되어 {filename}에 저장되었습니다.")
                else:
                    messagebox.showerror("오류", "일기 생성에 실패했습니다.")
                    
            except Exception as e:
                messagebox.showerror("오류", f"일기 생성 중 오류 발생: {str(e)}")
            finally:
                self.status_var.set("대화 중...")
        
        thread = threading.Thread(target=create_diary)
        thread.daemon = True
        thread.start()
    
    def show_diary_window(self, diary_data):
        """일기 표시 창"""
        diary_window = tk.Toplevel(self.root)
        diary_window.title("📖 오늘의 일기")
        diary_window.geometry("600x500")
        diary_window.configure(bg='white')
        
        # 스크롤 가능한 텍스트
        diary_text = scrolledtext.ScrolledText(
            diary_window, 
            wrap=tk.WORD, 
            font=("Arial", 11),
            bg='#f9f9f9'
        )
        diary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 일기 내용 구성
        diary = diary_data["diary"]
        emotion_analysis = diary_data["emotion_analysis"]
        
        content = "="*50 + "\n"
        content += "📖 오늘의 일기\n"
        content += "="*50 + "\n\n"
        
        content += f"📝 요약:\n{diary['<<일기 요약>>']}\n\n"
        content += f"🔍 원인:\n{diary['<<원인>>']}\n\n"
        content += f"💡 조언:\n{diary['<<조언>>']}\n\n"
        
        content += "📋 투두리스트:\n"
        todos = diary['<<투두리스트>>']
        content += f"  📅 오늘: {todos['<<오늘>>']}\n"
        content += f"  📅 내일: {todos['<<내일>>']}\n"
        content += f"  📅 모레: {todos['<<모레>>']}\n"
        content += f"  📅 D+3: {todos['<<D-3>>']}\n\n"
        
        content += "📊 감정 분석:\n"
        content += f"  🎯 대표 감정: {emotion_analysis['dominant_emotion']}\n"
        content += "  📈 감정 분포 (TOP 3):\n"
        for emotion_data in emotion_analysis['top_3_emotions']:
            emotion = emotion_data['emotion']
            percentage = emotion_data['percentage']
            content += f"    - {emotion}: {percentage}%\n"
        
        diary_text.insert(tk.END, content)
        diary_text.config(state=tk.DISABLED)
    
    def reset_conversation(self):
        """대화 초기화"""
        if messagebox.askyesno("확인", "대화를 초기화하시겠습니까?"):
            if self.chatbot:
                self.chatbot.reset_conversation()
            
            # 채팅 영역 클리어
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state=tk.DISABLED)
            
            self.add_system_message("🔄 대화가 초기화되었습니다. 새로 시작해보세요!")
            self.status_var.set("대화 초기화됨")
    
    def quit_app(self):
        """애플리케이션 종료"""
        if messagebox.askyesno("확인", "정말 종료하시겠습니까?"):
            self.root.quit()
    
    def run(self):
        """애플리케이션 실행"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI 실행 오류: {e}")

def main():
    app = EmotionChatbotGUI()
    app.run()

if __name__ == "__main__":
    main()