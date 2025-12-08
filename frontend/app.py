import streamlit as st
import requests
import time
from datetime import date, datetime, timedelta
import logging
from typing import Dict
import json
import plotly.graph_objects as go
import plotly.express as px
from styles import get_main_styles

# === Show Logo (Top-Left) ===
st.logo(
    "/Users/DLP-I516-206/Desktop/ubi-code/suny/suny/frontend/State_University_of_New_York_seal.svg.png",
    size="large"
)

# Make logo bigger, centered, with white background
st.markdown("""
<style>
    [data-testid="stLogo"] {
        height: auto !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 1.5rem 0 !important;
    }
    [data-testid="stLogo"] img {
        width: 100% !important;
        height: auto !important;
        max-width: 180px !important;
        background: white !important;
        padding: 1.5rem !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# === Config & Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SUNY Academic Guidance",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE = "http://localhost:8888"

# === Apply Unified Design System ===
st.markdown(get_main_styles(), unsafe_allow_html=True)

# === Session State ===
for key in ['messages', 'citations', 'initialized', 'auto_init_done', 'study_materials', 
            'student_id', 'selected_escalation', 'user_mode', 'show_escalation_form',
            'last_question', 'last_answer', 'last_escalation_id', 'transcribed_text',
            'show_audio_input']:
    if key not in st.session_state:
        if key in ['messages', 'citations', 'study_materials']:
            st.session_state[key] = []
        elif key == 'student_id':
            st.session_state[key] = "STUDENT_001"  # Default student ID
        elif key == 'user_mode':
            st.session_state[key] = "Student"  # Default mode: Student, Advisor, or Administrator
        elif key in ['show_escalation_form', 'show_audio_input']:
            st.session_state[key] = False
        elif key in ['last_question', 'last_answer', 'transcribed_text']:
            st.session_state[key] = ""
        elif key == 'last_escalation_id':
            st.session_state[key] = None
        else:
            st.session_state[key] = False

# === Helper Functions ===
def check_health(): 
    try: 
        return requests.get(f"{API_BASE}/academic/health", timeout=10).status_code == 200 
    except: 
        return False

def check_vector_store_status():
    try:
        r = requests.get(f"{API_BASE}/academic/status", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('is_populated', False), data.get('count', 0)
        return False, 0
    except:
        return False, 0

def initialize_system(force_rebuild=False):
    try:
        with st.spinner("Processing PDFs..."):
            r = requests.post(
                f"{API_BASE}/academic/init", 
                json={"pdf_dir": "data/pdfs/", "force_rebuild": force_rebuild}, 
                timeout=300
            )
            if r.status_code == 200:
                data = r.json()
                st.session_state.initialized = True
                return True, data['message'], data.get('count', 0), data.get('skipped', False)
            return False, f"Error: {r.text}", 0, False
    except Exception as e:
        return False, str(e), 0, False

def transcribe_audio(audio_file):
    """Send audio file to backend for transcription"""
    try:
        files = {"audio_file": audio_file}
        r = requests.post(
            f"{API_BASE}/academic/transcribe-audio",
            files=files,
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data.get("text", "")
            else:
                st.error(f"Transcription failed: {data.get('error', 'Unknown error')}")
                return None
        else:
            st.error(f"Transcription error: {r.status_code}")
            return None
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return None

def send_message(question: str, top_k: int = 5, student_id: str = None):
    try:
        r = requests.post(
            f"{API_BASE}/academic/chat",
            json={"question": question, "top_k": top_k, "student_id": student_id},
            timeout=120
        )
        return r.json() if r.status_code == 200 else {"answer": "Error", "citations": [], "escalation_id": None}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"answer": "Connection error", "citations": [], "escalation_id": None}

# === Auto-Initialize on First Load ===
if not st.session_state.auto_init_done:
    st.session_state.auto_init_done = True
    
    if check_health():
        populated, count = check_vector_store_status()
        
        if populated and count > 0:
            st.session_state.initialized = True
            st.success(f"✅ Knowledge base loaded! ({count} chunks available)")
            logger.info(f"Auto-init: Vector store already populated with {count} chunks")
        else:
            logger.info("Auto-init: Vector store empty, initializing...")
            st.info("🔄 First-time setup: Processing academic documents...")
            success, msg, final_count, skipped = initialize_system(force_rebuild=False)
            
            if success:
                st.session_state.initialized = True
                st.success(f"✅ System initialized! {final_count} chunks loaded")
                logger.info(f"Auto-init complete: {final_count} chunks")
            else:
                st.error(f"❌ Initialization failed: {msg}")
                logger.error(f"Auto-init failed: {msg}")
    else:
        st.error("❌ Backend is offline. Please start the FastAPI server.")

# === Sidebar ===
with st.sidebar:
    st.markdown("# 📚 SUNY Academic Assistant")
    st.markdown("<small style='color: #E5E7EB;'>RAG + Study Tools + Analytics</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Mode toggle
    st.markdown("### 👤 User Mode")
    mode = st.radio(
        "Select Mode",
        ["🎓 Student", "👨‍🏫 Advisor", "📊 Administrator"],
        index=["Student", "Advisor", "Administrator"].index(st.session_state.get("user_mode", "Student")),
        key="mode_radio"
    )
    
    # Map emoji labels to plain text
    mode_map = {
        "🎓 Student": "Student",
        "👨‍🏫 Advisor": "Advisor",
        "📊 Administrator": "Administrator"
    }
    st.session_state.user_mode = mode_map[mode]
    
    if st.session_state.user_mode == "Student":
        # Student mode: show student ID input
        st.session_state.student_id = st.text_input(
            "Student ID",
            value=st.session_state.get("student_id", "STUDENT_001"),
            key="student_id_input"
        )
    
    st.markdown("---")

    healthy = check_health()
    st.markdown("### System Status")
    if healthy:
        st.success("✅ Backend Connected")
        populated, count = check_vector_store_status()
        if populated:
            st.success(f"✅ Knowledge Base Ready ({count} chunks)")
            st.session_state.initialized = True
        else:
            st.warning("⚠️ Knowledge Base Empty")
            st.session_state.initialized = False
    else:
        st.error("❌ Backend Offline")
        st.session_state.initialized = False

    st.markdown("---")
    st.markdown("### 🔧 Initialize System")
    
    force_rebuild = st.checkbox("🔄 Force Rebuild (Clear & Reprocess All)", key="force_cb")
    
    if force_rebuild:
        st.warning("⚠️ This will delete existing data and rebuild from scratch")
    
    if st.button("🚀 Initialize System", type="primary", use_container_width=True):
        if not healthy:
            st.error("Cannot initialize: Backend is offline")
        else:
            with st.spinner("Processing PDFs..."):
                success, msg, count, skipped = initialize_system(force_rebuild)
                
                if success:
                    if skipped:
                        st.info(f"ℹ️ {msg}")
                    else:
                        st.success(f"✅ {msg}")
                    
                    if count > 0:
                        st.info(f"📊 Vector store now has {count} chunks")
                    
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("📊 Retrieval Count", 1, 10, 5, key="top_k_slider", 
                      help="Number of document chunks to retrieve per query")
    
    if st.button("🗑️ Clear Academic Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.citations = []
        st.session_state.last_escalation_id = None
        st.session_state.last_question = ""
        st.session_state.last_answer = ""
        st.success("Chat cleared!")
        time.sleep(0.5)
        st.rerun()

# === TABS ===
if st.session_state.user_mode == "Administrator":
    # Administrator mode: Show analytics dashboard
    tab_admin = st.container()
    tab1 = None
    tab2 = None
    tab3 = None
elif st.session_state.user_mode == "Advisor":
    # Advisor mode: Only show escalation dashboard
    tab3 = st.container()
    tab1 = None
    tab2 = None
    tab_admin = None
else:
    # Student mode: Show chat and study tools
    tab1, tab2 = st.tabs(["💬 Academic Guidance Chat", "📖 Study Tools"])
    tab3 = None
    tab_admin = None

# === TAB 1: Academic Chat ===
if tab1:
    with tab1:
        st.markdown("# 💬 Academic Guidance Chat")
        
        if not st.session_state.initialized:
            st.warning("⚠️ Please initialize the system first using the sidebar")
            st.stop()

        # Audio input toggle and recording section (above chat)
        audio_mode = st.toggle("🎤 Voice Input", key="audio_toggle", help="Click to enable live audio recording")
        
        audio_send_clicked = False
        if audio_mode:
            # Browser-based audio recording using st.audio_input
            audio_data = st.audio_input(
                "Click to start recording",
                key="audio_recorder",
                help="🎤 Click the microphone icon to start recording. Click again to stop."
            )
            
            # Store audio in session state
            if audio_data is not None:
                st.session_state.recorded_audio = audio_data
                st.success("✅ Audio recorded!")
                
                # Show Send button right next to the audio
                audio_send_clicked = st.button("📤 Send", key="audio_send_btn", type="primary", use_container_width=True)
        
        st.markdown("---")

        # Display chat messages
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You</strong><br>{msg["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 AI Advisor</strong><br>{msg["content"]}</div>', 
                           unsafe_allow_html=True)
        
        # Show auto-escalation notice with remove option
        if st.session_state.get("last_escalation_id"):
            esc_id = st.session_state.last_escalation_id
            st.markdown(f"""
            <div class="escalation-notice">
                <h4 style="color:#5eead4; margin:0 0 0.5rem 0;">🎯 Question Auto-Escalated to Human Advisor</h4>
                <p style="color:#e2e8f0; margin:0;">Your question has been automatically flagged for human review to ensure you get the best possible assistance.</p>
                <p style="color:#94a3b8; font-size:0.9rem; margin:0.5rem 0 0 0;">📋 Escalation ID: <code>{esc_id[:8]}...</code></p>
                <p style="color:#10b981; font-weight:600; margin:0.5rem 0 0 0;">✅ An advisor will review this shortly and reach out to you.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("❌ Remove Escalation", key="remove_escalation_btn", type="secondary"):
                try:
                    # Delete the escalation
                    del_resp = requests.delete(f"{API_BASE}/advisor/escalations/{esc_id}", timeout=10)
                    if del_resp.status_code == 200:
                        st.success("✅ Escalation removed successfully!")
                        st.session_state.last_escalation_id = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to remove escalation")
                except Exception as e:
                    st.error(f"Error removing escalation: {e}")

        # Display citations
        if st.session_state.citations:
            with st.expander("📚 View Sources", expanded=False):
                for i, c in enumerate(st.session_state.citations, 1):
                    st.markdown(f"""
                    <div class="citation-box">
                        <div class="citation-title">Source {i}: {c['doc_id']}</div>
                        <div style="color:#94a3b8;font-style:italic;">"{c['snippet'][:250]}..."</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Text input (shown when audio mode is off)
        st.markdown("### 💬 Ask Your Question")
        
        user_prompt = ""
        if not audio_mode:
            # Traditional text input
            user_prompt = st.text_input(
                "Ask about courses, requirements, policies...", 
                key="chat_text_tab",
                placeholder="e.g., What are the CS major requirements?"
            )
        else:
            # Audio mode is active, user_prompt will be set when Send is clicked
            if st.session_state.get('recorded_audio') is not None:
                user_prompt = "[AUDIO_RECORDED]"  # Placeholder to indicate audio is ready
        
        # Action buttons (only show if not in audio mode or no audio recorded)
        if not audio_mode or st.session_state.get('recorded_audio') is None:
            col_send, col_clear, col_escalate = st.columns([2, 1, 2])
            
            with col_send:
                send_clicked = st.button("📤 Send", key="send_tab", type="primary", use_container_width=True)
            
            with col_clear:
                # Empty column for spacing
                st.empty()
            
            with col_escalate:
                if st.session_state.user_mode == "Student" and st.session_state.messages:
                    escalate_clicked = st.button("🆘 Escalate to Advisor", key="escalate_btn", use_container_width=True)
                else:
                    escalate_clicked = False
        else:
            # In audio mode with recording, send button is shown above
            send_clicked = False
            escalate_clicked = False
        
        # Handle send button click (from either location)
        if send_clicked or audio_send_clicked:
            final_text = ""
            
            # If in audio mode, transcribe the audio first
            if audio_mode and st.session_state.get('recorded_audio') is not None:
                with st.spinner("🎧 Transcribing your audio... Please wait"):
                    # Get audio data
                    audio_file = st.session_state.recorded_audio
                    audio_file.seek(0)  # Reset file pointer
                    
                    # Transcribe audio
                    transcribed = transcribe_audio(audio_file)
                    
                    if transcribed:
                        final_text = transcribed
                        st.success(f"✅ Transcribed: \"{transcribed}...\"")
                        time.sleep(1)  # Brief pause to show transcription
                    else:
                        st.error("❌ Failed to transcribe audio. Please try again.")
                        st.stop()
            
            # If in text mode, use the text input
            elif not audio_mode and user_prompt:
                final_text = user_prompt
            
            # Send to LLM if we have text
            if final_text and final_text.strip():
                st.session_state.last_prompt = final_text
                st.session_state.messages.append({"role": "user", "content": final_text})
                
                with st.spinner("🤖 AI is thinking... Searching knowledge base"):
                    resp = send_message(
                        final_text, 
                        st.session_state.get("top_k_slider", 5),
                        st.session_state.get("student_id") if st.session_state.user_mode == "Student" else None
                    )
                    answer = resp.get("answer", "No answer")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.citations = resp.get("citations", [])
                    
                    # Store last response for potential manual escalation
                    st.session_state.last_question = final_text
                    st.session_state.last_answer = answer
                    st.session_state.last_escalation_id = resp.get("escalation_id")
                    
                    # Clear audio recording if in audio mode
                    if audio_mode:
                        st.session_state.recorded_audio = None
                
                st.success("✅ Response received!")
                time.sleep(0.5)
                st.rerun()
            else:
                if audio_mode:
                    st.warning("⚠️ Please record audio first before sending")
                else:
                    st.warning("⚠️ Please enter a question first")
        
        # Manual Escalation Dialog
        if escalate_clicked and st.session_state.messages:
            st.session_state.show_escalation_form = True
            st.rerun()
        
        # Show manual escalation form
        if st.session_state.get("show_escalation_form", False):
            with st.form("manual_escalation_form"):
                st.markdown("### 🆘 Escalate to Human Advisor")
                st.markdown("Fill in the details below to send your question to a human advisor:")
                
                # Pre-fill with last conversation
                last_q = st.session_state.get("last_question", "")
                last_a = st.session_state.get("last_answer", "")
                
                question_text = st.text_area(
                    "Your Question",
                    value=last_q,
                    height=100,
                    help="Describe your question or concern"
                )
                
                ai_response_text = st.text_area(
                    "AI Response (optional - edit if needed)",
                    value=last_a,
                    height=100,
                    help="The response you received from the AI"
                )
                
                escalation_reason = st.selectbox(
                    "Why do you need human help?",
                    [
                        "AI answer was unclear or insufficient",
                        "Need personalized academic guidance",
                        "Financial aid or scholarship question",
                        "Course registration or prerequisite issue",
                        "Academic difficulty or failing course",
                        "Need accommodation or special request",
                        "Urgent or time-sensitive matter",
                        "Other - please explain in notes"
                    ],
                    key="reason_select"
                )
                
                priority_level = st.select_slider(
                    "How urgent is this?",
                    options=[1, 2, 3, 4, 5],
                    value=2,
                    format_func=lambda x: {
                        1: "⭐ Low - Can wait",
                        2: "⭐⭐ Normal",
                        3: "⭐⭐⭐ Medium - Soon",
                        4: "⭐⭐⭐⭐ High - Important",
                        5: "⭐⭐⭐⭐⭐ Critical - Urgent"
                    }[x],
                    key="priority_select"
                )
                
                additional_notes = st.text_area(
                    "Additional Context (optional)",
                    placeholder="Anything else the advisor should know...",
                    height=80,
                    key="notes_input"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_escalation = st.form_submit_button("✅ Submit to Advisor", type="primary", use_container_width=True)
                with col2:
                    cancel_escalation = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submit_escalation and question_text:
                    # Create manual escalation
                    try:
                        import uuid
                        from datetime import datetime
                        
                        # Build conversation history from session
                        conversation_history = []
                        for msg in st.session_state.messages[-6:]:  # Last 6 messages (3 exchanges)
                            conversation_history.append({
                                "role": msg["role"],
                                "content": msg["content"],
                                "timestamp": datetime.now().isoformat()
                            })
                        
                        # Combine reason with additional notes
                        full_reason = escalation_reason
                        if additional_notes:
                            full_reason += f" | Notes: {additional_notes}"
                        
                        escalation_data = {
                            "student_id": st.session_state.get("student_id", "UNKNOWN"),
                            "question": question_text,
                            "ai_response": ai_response_text or "Manual escalation - no AI response",
                            "conversation_history": conversation_history,
                            "escalation_reason": full_reason,
                            "priority": priority_level
                        }
                        
                        # Send to API
                        create_resp = requests.post(
                            f"{API_BASE}/advisor/escalations",
                            json=escalation_data,
                            timeout=10
                        )
                        
                        if create_resp.status_code == 200:
                            esc_id = create_resp.json().get("id", "")
                            st.markdown(f"""
                            <div class="escalation-notice">
                                <h4 style="color:#5eead4; margin:0 0 0.5rem 0;">✅ Escalation Submitted Successfully!</h4>
                                <p style="color:#e2e8f0; margin:0;">Your question has been sent to a human advisor for personalized assistance.</p>
                                <p style="color:#94a3b8; font-size:0.9rem; margin:0.5rem 0 0 0;">📋 Escalation ID: <code>{esc_id[:8]}...</code></p>
                                <p style="color:#10b981; font-weight:600; margin:0.5rem 0 0 0;">🎯 Priority: {'⭐' * priority_level}</p>
                                <p style="color:#5eead4; margin:0.5rem 0 0 0;">An advisor will review your question and contact you soon!</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.session_state.show_escalation_form = False
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to create escalation: {create_resp.text}")
                            
                    except Exception as e:
                        st.error(f"❌ Error creating escalation: {e}")
                
                if cancel_escalation:
                    st.session_state.show_escalation_form = False
                    st.rerun()

# === TAB 2: Study Tools ===
if tab2:
    with tab2:
        st.markdown("# 📖 Study Tools")
        st.markdown("### Upload once → use any tool below")

        # Upload section
        uploaded = st.file_uploader(
            "📄 Upload PDF / TXT files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key="study_upload",
            help="All tools use the same content"
        )

        if uploaded:
            with st.spinner("📖 Reading files..."):
                for file in uploaded:
                    if file.type == "application/pdf":
                        try:
                            from PyPDF2 import PdfReader
                            reader = PdfReader(file)
                            text = "\n".join([p.extract_text() or "" for p in reader.pages if p.extract_text()])
                        except Exception as e:
                            logger.error(f"Error reading PDF {file.name}: {e}")
                            text = "[Could not read PDF]"
                    else:
                        text = file.read().decode("utf-8", errors="ignore")

                    if text.strip() and text not in st.session_state.study_materials:
                        st.session_state.study_materials.append(text)
                        st.success(f"✅ Loaded: **{file.name}**")

        if not st.session_state.study_materials:
            st.info("📤 Upload your study material to unlock all tools")
            st.stop()

        total_words = sum(len(t.split()) for t in st.session_state.study_materials)
        st.caption(f"✅ Ready: {len(st.session_state.study_materials)} file(s) • ~{total_words:,} words")

        material_text = "\n\n".join(st.session_state.study_materials)

        # === 1. Flashcards ===
        with st.expander("🎴 Flashcards – Generate & Review", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                topic_fc = st.text_input("Topic (optional)", placeholder="e.g., Attention Mechanism", key="fc_topic")
            with col2:
                count_fc = st.selectbox("Cards", [2, 4, 6, 8, 10], index=2, key="fc_count")

            if st.button("🎴 Generate Flashcards", type="primary", use_container_width=True):
                with st.spinner("Creating flashcards..."):
                    r = requests.post(f"{API_BASE}/study/flashcards", json={
                        "topic": topic_fc or "key concepts",
                        "count": count_fc,
                        "context": material_text
                    })
                    if r.status_code == 200:
                        st.session_state.flashcards = r.json().get("flashcards", [])
                        st.success(f"✅ {len(st.session_state.flashcards)} cards ready!")

            if st.session_state.get("flashcards"):
                st.markdown("### Your Flashcards")
                for i, card in enumerate(st.session_state.flashcards):
                    q = card.get("question", "")
                    a = card.get("answer", "")
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:1.3rem; margin:1rem 0; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);">
                        <strong style="color:#1D4ED8;">Q{i+1}: {q}</strong><br><br>
                        <details><summary style="color:#64748B; cursor:pointer;">Show Answer</summary>
                        <p style="color:#1E293B; margin-top:0.8rem;">{a}</p></details>
                    </div>
                    """, unsafe_allow_html=True)

        # === 2. Practice Quiz ===
        with st.expander("✅ Practice Quiz – Test Yourself", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                topic_q = st.text_input("Quiz topic (optional)", placeholder="e.g., Transformers", key="quiz_topic")
            with col2:
                num_q = st.selectbox("Questions", [2, 4, 6, 8, 10], index=0, key="quiz_num")

            if st.button("✅ Generate Quiz", type="primary", use_container_width=True):
                with st.spinner("Generating quiz..."):
                    r = requests.post(f"{API_BASE}/study/quiz", json={
                        "topic": topic_q or "core concepts",
                        "num_questions": num_q,
                        "context": material_text
                    })
                    if r.status_code == 200:
                        st.session_state.quiz = r.json().get("quiz", [])
                        st.success("✅ Quiz ready!")

            if st.session_state.get("quiz"):
                for i, q in enumerate(st.session_state.quiz):
                    st.markdown(f"**Q{i+1}.** {q.get('question')}")
                    for j, opt in enumerate(q.get("options", [])):
                        if j == q.get("correct_index"):
                            st.markdown(f'<span style="color:#22C55E; font-weight:600;">✅ {opt}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span style="color:#64748B;">• {opt}</span>', unsafe_allow_html=True)

                    explanation = q.get("explanation", "")
                    if explanation:
                        st.markdown(f"""
                        <details style="margin:1rem 0;">
                            <summary style="color:#3B82F6; cursor:pointer; font-weight:600;">💡 Show Explanation</summary>
                            <p style="color:#1E293B; margin-top:0.5rem; padding-left:0.5rem;">{explanation}</p>
                        </details>
                        """, unsafe_allow_html=True)
                    st.markdown("---")

        # === 3. Summary ===
        with st.expander("📝 Summary – Key Points", expanded=False):
            if st.button("📝 Generate Summary", type="primary", use_container_width=True):
                with st.spinner("Summarizing..."):
                    r = requests.post(f"{API_BASE}/study/summary", json={"context": material_text})
                    if r.status_code == 200:
                        st.markdown("### Summary")
                        st.write(r.json().get("summary", ""))

        # === 4. Concept Explainer ===
        with st.expander("💡 Concept Explainer", expanded=False):
            concept = st.text_input("What do you want explained?", 
                                   placeholder="e.g., Positional Encoding", 
                                   key="explain_concept")
            if st.button("💡 Explain Concept", type="primary", use_container_width=True) and concept:
                with st.spinner("Explaining..."):
                    r = requests.post(f"{API_BASE}/study/explain", 
                                    json={"concept": concept, "context": material_text})
                    if r.status_code == 200:
                        st.markdown(f"### {concept}")
                        st.write(r.json().get("explanation", ""))

        # === 5. Study Schedule ===
        with st.expander("📅 Study Schedule – Personalized Plan", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                exam_date = st.date_input("Exam date", value=date.today(), min_value=date.today())
            with col2:
                hours_per_day = st.slider("Hours/day", 1, 8, 4)

            focus_topics = st.text_area("Focus topics (optional)", 
                                       placeholder="e.g., Attention, RNNs", 
                                       height=80)
            topic_list = [t.strip() for t in focus_topics.split(",") if t.strip()]

            if st.button("📅 Build Study Schedule", type="primary", use_container_width=True):
                days = (exam_date - date.today()).days
                if days < 1:
                    st.error("❌ Pick a future date")
                else:
                    with st.spinner("Planning your study schedule..."):
                        r = requests.post(f"{API_BASE}/study/schedule", json={
                            "exam_date": exam_date.isoformat(),
                            "hours_per_day": hours_per_day,
                            "topics": topic_list or ["all key concepts"],
                            "context": material_text
                        })
                        if r.status_code == 200:
                            st.session_state.schedule = r.json().get("schedule", [])
                            st.success(f"✅ Plan created for {days} days!")

            if st.session_state.get("schedule"):
                st.markdown("### Your Study Schedule")
                for day in st.session_state.schedule:
                    with st.container():
                        st.markdown(f"**{day.get('day')} – {day.get('focus')}**")
                        for task in day.get("tasks", []):
                            st.markdown(f"• {task}")
                        st.caption(f"⏱️ {day.get('hours', hours_per_day)} hours")
                        st.markdown("---")

# === TAB 3: Advisor Dashboard ===
if tab3 and st.session_state.user_mode == "Advisor":
    with tab3:
        st.markdown("# 🎯 Advisor Dashboard - Escalation Queue")
        st.markdown("### Monitor and respond to escalated student questions")
        st.info("👨‍🏫 **Advisor Mode Active** | Viewing escalations only | Switch to Student mode in sidebar to access chat and study tools")
        
        # Dashboard Stats
        try:
            stats_resp = requests.get(f"{API_BASE}/advisor/dashboard/stats", timeout=10)
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card-gradient-info" style="text-align:center;">
                        <div style="font-size:0.875rem; font-weight:600; opacity:0.9; margin-bottom:0.5rem;">TOTAL ESCALATIONS</div>
                        <div style="font-size:2.5rem; font-weight:700;">{stats.get("total_escalations", 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card-gradient-warning" style="text-align:center;">
                        <div style="font-size:0.875rem; font-weight:600; opacity:0.9; margin-bottom:0.5rem;">PENDING</div>
                        <div style="font-size:2.5rem; font-weight:700;">{stats.get("pending", 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card-gradient" style="text-align:center;">
                        <div style="font-size:0.875rem; font-weight:600; opacity:0.9; margin-bottom:0.5rem;">IN PROGRESS</div>
                        <div style="font-size:2.5rem; font-weight:700;">{stats.get("in_progress", 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card-gradient-success" style="text-align:center;">
                        <div style="font-size:0.875rem; font-weight:600; opacity:0.9; margin-bottom:0.5rem;">RESOLVED</div>
                        <div style="font-size:2.5rem; font-weight:700;">{stats.get("resolved", 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"""
                    <div class="metric-card-gradient-danger" style="text-align:center;">
                        <div style="font-size:0.875rem; font-weight:600; opacity:0.9; margin-bottom:0.5rem;">HIGH RISK STUDENTS</div>
                        <div style="font-size:2.5rem; font-weight:700;">{stats.get("high_risk_students", 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Visualizations
                st.markdown("### 📊 Escalation Analytics")
                
                viz_col1, viz_col2, viz_col3 = st.columns(3)
                
                with viz_col1:
                    # Pie Chart - Status Distribution
                    status_data = {
                        'Pending': stats.get("pending", 0),
                        'In Progress': stats.get("in_progress", 0),
                        'Resolved': stats.get("resolved", 0)
                    }
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=list(status_data.keys()),
                        values=list(status_data.values()),
                        hole=0.4,
                        marker=dict(colors=['#FACC15', '#3B82F6', '#22C55E']),
                        textinfo='label+percent',
                        textposition='auto',
                    )])
                    
                    fig_pie.update_layout(
                        title="Escalation Status Distribution",
                        showlegend=True,
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1E293B', size=12),
                        title_font=dict(size=16, color='#1D4ED8'),
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with viz_col2:
                    # Bar Chart - Priority Distribution
                    # Get all escalations to calculate priority distribution
                    try:
                        all_esc_resp = requests.get(f"{API_BASE}/advisor/escalations", timeout=10)
                        if all_esc_resp.status_code == 200:
                            all_escalations = all_esc_resp.json()
                            
                            priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                            for esc in all_escalations:
                                priority = esc.get('priority', 1)
                                priority_counts[priority] = priority_counts.get(priority, 0) + 1
                            
                            fig_bar = go.Figure(data=[go.Bar(
                                x=['⭐', '⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'],
                                y=[priority_counts[1], priority_counts[2], priority_counts[3], 
                                   priority_counts[4], priority_counts[5]],
                                marker=dict(
                                    color=[priority_counts[1], priority_counts[2], priority_counts[3], 
                                           priority_counts[4], priority_counts[5]],
                                    colorscale=[[0, '#22C55E'], [0.5, '#FACC15'], [1, '#EF4444']],
                                    showscale=False
                                ),
                                text=[priority_counts[1], priority_counts[2], priority_counts[3], 
                                      priority_counts[4], priority_counts[5]],
                                textposition='auto',
                            )])
                            
                            fig_bar.update_layout(
                                title="Priority Level Distribution",
                                xaxis_title="Priority Level",
                                yaxis_title="Number of Escalations",
                                height=350,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#1E293B', size=12),
                                title_font=dict(size=16, color='#1D4ED8'),
                                xaxis=dict(gridcolor='#E5E7EB'),
                                yaxis=dict(gridcolor='#E5E7EB'),
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info("Unable to load priority distribution")
                    except Exception as e:
                        st.info(f"Chart data unavailable: {e}")
                
                with viz_col3:
                    # Risk Level Distribution
                    try:
                        students_resp = requests.get(f"{API_BASE}/advisor/students", timeout=10)
                        if students_resp.status_code == 200:
                            students = students_resp.json()
                            
                            risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                            for student in students:
                                risk = student.get('risk_level', 'low')
                                risk_counts[risk] = risk_counts.get(risk, 0) + 1
                            
                            fig_risk = go.Figure(data=[go.Bar(
                                x=['Low', 'Medium', 'High', 'Critical'],
                                y=[risk_counts['low'], risk_counts['medium'], 
                                   risk_counts['high'], risk_counts['critical']],
                                marker=dict(
                                    color=['#22C55E', '#FACC15', '#EF4444', '#DC2626']
                                ),
                                text=[risk_counts['low'], risk_counts['medium'], 
                                      risk_counts['high'], risk_counts['critical']],
                                textposition='auto',
                            )])
                            
                            fig_risk.update_layout(
                                title="Student Risk Levels",
                                xaxis_title="Risk Level",
                                yaxis_title="Number of Students",
                                height=350,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#1E293B', size=12),
                                title_font=dict(size=16, color='#1D4ED8'),
                                xaxis=dict(gridcolor='#E5E7EB'),
                                yaxis=dict(gridcolor='#E5E7EB'),
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            
                            st.plotly_chart(fig_risk, use_container_width=True)
                        else:
                            st.info("Unable to load risk distribution")
                    except Exception as e:
                        st.info(f"Chart data unavailable: {e}")
                
                st.markdown("---")
                
        except Exception as e:
            st.error(f"Could not load dashboard stats: {e}")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All", "pending", "in_progress", "resolved"],
                key="filter_status"
            )
        with col2:
            filter_priority = st.slider("Min Priority", 1, 5, 1, key="filter_priority")
        with col3:
            if st.button("🔄 Refresh Dashboard", use_container_width=True, type="primary"):
                # Clear any cached data
                if 'escalations_cache' in st.session_state:
                    del st.session_state['escalations_cache']
                st.rerun()
        
        # Get escalations
        try:
            params = {}
            if filter_status != "All":
                params["status"] = filter_status
            if filter_priority > 1:
                params["priority_min"] = filter_priority
            
            with st.spinner("Loading escalations..."):
                esc_resp = requests.get(f"{API_BASE}/advisor/escalations", params=params, timeout=30)
            
            if esc_resp.status_code == 200:
                escalations = esc_resp.json()
                
                st.caption(f"💡 Debug: Loaded {len(escalations)} escalation(s) from API | Filters: Status={filter_status}, Priority>={filter_priority}")
                
                if not escalations:
                    st.info("📭 No escalations found with current filters")
                    st.info("💡 Try clicking '🔄 Refresh Dashboard' or change filter settings")
                    
                    # Debug: Show raw API response
                    with st.expander("🔍 Debug: View Raw API Response"):
                        st.json(esc_resp.json())
                        st.code(f"API URL: {API_BASE}/advisor/escalations")
                        st.code(f"Params: {params}")
                else:
                    st.markdown(f"### 📋 {len(escalations)} Escalation(s)")
                    
                    # Display each escalation
                    for esc in escalations:
                        with st.expander(
                            f"🔔 [{esc['status'].upper()}] Student: {esc['student_id']} | "
                            f"Priority: {'⭐' * esc.get('priority', 1)} | "
                            f"{esc['created_at'][:10]}",
                            expanded=False
                        ):
                            # Two column layout
                            col_left, col_right = st.columns([2, 1])
                            
                            with col_left:
                                # Question and Response
                                st.markdown("#### 💬 Student Question")
                                st.markdown(f'<div style="background:#DBEAFE; padding:1rem; border-radius:12px; border-left:4px solid #3B82F6; color:#1E293B;">{esc["question"]}</div>', 
                                          unsafe_allow_html=True)
                                
                                st.markdown("#### 🤖 AI Response")
                                st.markdown(f'<div style="background:#FFFFFF; padding:1rem; border-radius:12px; border:1px solid #E5E7EB; color:#1E293B;">{esc["ai_response"]}</div>', 
                                          unsafe_allow_html=True)
                                
                                st.markdown("#### 📝 Escalation Reason")
                                st.warning(f"⚠️ {esc['escalation_reason']}")
                                
                                # Conversation History - Using checkbox instead of nested expander
                                if esc.get("conversation_history"):
                                    show_history = st.checkbox("💬 View Full Conversation History", key=f"history_{esc['id']}")
                                    if show_history:
                                        st.markdown("---")
                                        for msg in esc["conversation_history"]:
                                            role = msg.get("role", "unknown")
                                            content = msg.get("content", "")
                                            timestamp = msg.get("timestamp", "")[:16]
                                            
                                            if role == "user":
                                                st.markdown(f'**🎓 Student** ({timestamp})')
                                                st.markdown(f'<div style="background:#DBEAFE; padding:0.5rem; border-radius:8px; margin-bottom:0.5rem; color:#1E293B;">{content}</div>', 
                                                          unsafe_allow_html=True)
                                            else:
                                                st.markdown(f'**🤖 AI** ({timestamp})')
                                                st.markdown(f'<div style="background:#F8FAFC; padding:0.5rem; border-radius:8px; margin-bottom:0.5rem; border:1px solid #E5E7EB; color:#1E293B;">{content}</div>', 
                                                          unsafe_allow_html=True)
                                        st.markdown("---")
                                
                                # Advisor Notes
                                if esc.get("advisor_notes"):
                                    st.markdown("#### 📌 Advisor Notes")
                                    for note in esc["advisor_notes"]:
                                        # Handle both string format (old) and dict format (new)
                                        if isinstance(note, str):
                                            note_text = note
                                            note_time = ""
                                        elif isinstance(note, dict):
                                            note_text = note.get("note", "")
                                            note_time = note.get("timestamp", "")[:16]
                                        else:
                                            continue
                                        
                                        if note_time:
                                            st.markdown(f'- {note_text} <small style="color:#64748b;">({note_time})</small>', 
                                                      unsafe_allow_html=True)
                                        else:
                                            st.markdown(f'- {note_text}', unsafe_allow_html=True)
                            
                            with col_right:
                                # Student Profile Card
                                st.markdown("#### 👤 Student Profile")
                                try:
                                    profile_resp = requests.get(
                                        f"{API_BASE}/advisor/students/{esc['student_id']}", 
                                        timeout=5
                                    )
                                    if profile_resp.status_code == 200:
                                        profile = profile_resp.json()
                                        
                                        # Risk level badge
                                        risk_level = profile.get("risk_level", "low")
                                        risk_colors = {
                                            "low": "#10b981",
                                            "medium": "#f59e0b",
                                            "high": "#ef4444",
                                            "critical": "#dc2626"
                                        }
                                        risk_color = risk_colors.get(risk_level, "#64748b")
                                        
                                        st.markdown(f"""
                                        <div style="background:#FFFFFF; padding:1rem; border-radius:12px; border:1px solid #E5E7EB; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04); word-wrap:break-word; overflow-wrap:break-word;">
                                            <p style="margin:0.3rem 0; word-wrap:break-word; color:#1E293B;"><strong>Name:</strong><br/>{profile.get('name', 'Unknown')}</p>
                                            <p style="margin:0.3rem 0; color:#1E293B;"><strong>Major:</strong><br/>{profile.get('major', 'Undeclared')}</p>
                                            <p style="margin:0.3rem 0; color:#1E293B;"><strong>GPA:</strong> {profile.get('gpa', 'N/A')}</p>
                                            <p style="margin:0.3rem 0; color:#1E293B;"><strong>Risk Level:</strong> <span style="color:{risk_color}; font-weight:bold;">{risk_level.upper()}</span></p>
                                            <p style="margin:0.3rem 0; color:#1E293B;"><strong>Total Escalations:</strong> {profile.get('total_escalations', 0)}</p>
                                            <p style="margin:0.3rem 0; color:#1E293B;"><strong>Last Interaction:</strong><br/>{profile.get('last_interaction', 'N/A')[:10]}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Show completed courses
                                        if profile.get("completed_courses"):
                                            st.markdown("**Completed Courses:**")
                                            for course in profile.get("completed_courses", [])[:5]:
                                                st.caption(f"✓ {course}")
                                        
                                        if profile.get("current_courses"):
                                            st.markdown("**Current Courses:**")
                                            for course in profile.get("current_courses", [])[:5]:
                                                st.caption(f"📚 {course}")
                                    else:
                                        st.warning("Could not load student profile")
                                except Exception as e:
                                    st.error(f"Error loading profile: {e}")
                            
                            st.markdown("---")
                            
                            # Action Section
                            st.markdown("#### 🎯 Take Action")
                            
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                new_status = st.selectbox(
                                    "Update Status",
                                    ["pending", "in_progress", "resolved", "closed"],
                                    index=["pending", "in_progress", "resolved", "closed"].index(esc.get("status", "pending")),
                                    key=f"status_{esc['id']}"
                                )
                            
                            with action_col2:
                                new_priority = st.selectbox(
                                    "Priority",
                                    [1, 2, 3, 4, 5],
                                    index=esc.get("priority", 1) - 1,
                                    key=f"priority_{esc['id']}"
                                )
                            
                            advisor_note = st.text_area(
                                "Add Note for Follow-up",
                                placeholder="Enter your notes, recommendations, or next steps...",
                                key=f"note_{esc['id']}",
                                height=100
                            )
                            
                            assigned_to = st.text_input(
                                "Assign To (Advisor Name)",
                                value=esc.get("assigned_to", ""),
                                key=f"assign_{esc['id']}"
                            )
                            
                            if st.button("💾 Update Escalation", key=f"update_{esc['id']}", type="primary"):
                                try:
                                    update_data = {}
                                    if new_status != esc.get("status"):
                                        update_data["status"] = new_status
                                    if advisor_note:
                                        update_data["note"] = advisor_note
                                    if assigned_to != esc.get("assigned_to", ""):
                                        update_data["assigned_to"] = assigned_to
                                    if new_priority != esc.get("priority", 1):
                                        update_data["priority"] = new_priority
                                    
                                    if update_data:
                                        update_resp = requests.patch(
                                            f"{API_BASE}/advisor/escalations/{esc['id']}",
                                            json=update_data,
                                            timeout=10
                                        )
                                        if update_resp.status_code == 200:
                                            st.success("✅ Escalation updated successfully!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update: {update_resp.text}")
                                    else:
                                        st.info("No changes to save")
                                except Exception as e:
                                    st.error(f"Error updating escalation: {e}")
                            
                            # ========== AI ASSIST TOOLS ==========
                            st.markdown("---")
                            st.markdown("#### 🤖 AI Assist Tools")
                            st.markdown("Generate AI-powered content to help respond to this student:")
                            
                            # Tool selector
                            assist_tool = st.selectbox(
                                "Select Tool",
                                [
                                    "📧 Outreach Email",
                                    "📅 Meeting Invitation",
                                    "📝 Session Summary",
                                    "📊 Academic Recovery Plan",
                                    "📋 Guidance Notes"
                                ],
                                key=f"tool_select_{esc['id']}"
                            )
                            
                            # Additional inputs for specific tools
                            additional_input = ""
                            if "Session Summary" in assist_tool:
                                additional_input = st.text_area(
                                    "Additional Session Notes (optional)",
                                    placeholder="Add any notes from your conversation with the student...",
                                    height=80,
                                    key=f"session_notes_{esc['id']}"
                                )
                            elif "Guidance Notes" in assist_tool:
                                additional_input = st.text_area(
                                    "Relevant Policy Context (optional)",
                                    placeholder="Add any specific SUNY policies or requirements...",
                                    height=80,
                                    key=f"policy_context_{esc['id']}"
                                )
                            
                            tool_col1, tool_col2 = st.columns([1, 1])
                            
                            with tool_col1:
                                if st.button("✨ Generate", key=f"generate_{esc['id']}", type="secondary"):
                                    # Determine which tool to call
                                    endpoint_map = {
                                        "📧 Outreach Email": "generate-email",
                                        "📅 Meeting Invitation": "generate-meeting",
                                        "📝 Session Summary": "generate-summary",
                                        "📊 Academic Recovery Plan": "generate-recovery-plan",
                                        "📋 Guidance Notes": "generate-guidance"
                                    }
                                    
                                    endpoint = endpoint_map[assist_tool]
                                    
                                    with st.spinner(f"🤖 Generating {assist_tool.split(' ', 1)[1]}..."):
                                        try:
                                            # Prepare request data
                                            req_data = {}
                                            if "Session Summary" in assist_tool and additional_input:
                                                req_data = {"notes": additional_input}
                                            elif "Guidance Notes" in assist_tool and additional_input:
                                                req_data = {"policy_context": additional_input}
                                            
                                            # Make API call
                                            gen_resp = requests.post(
                                                f"{API_BASE}/advisor/escalations/{esc['id']}/{endpoint}",
                                                json=req_data if req_data else None,
                                                timeout=30
                                            )
                                            
                                            if gen_resp.status_code == 200:
                                                result = gen_resp.json()
                                                content_key = list(result.keys())[1]  # Skip 'status', get content key
                                                generated_content = result.get(content_key, "")
                                                
                                                # Store in session state for display
                                                st.session_state[f"generated_content_{esc['id']}"] = generated_content
                                                st.success(f"✅ {assist_tool.split(' ', 1)[1]} generated successfully!")
                                                time.sleep(0.5)
                                                st.rerun()
                                            else:
                                                st.error(f"Generation failed: {gen_resp.text}")
                                        except Exception as e:
                                            st.error(f"Error generating content: {e}")
                            
                            # Display generated content
                            if st.session_state.get(f"generated_content_{esc['id']}"):
                                st.markdown("---")
                                st.markdown("##### 📄 Generated Content")
                                
                                generated_text = st.session_state[f"generated_content_{esc['id']}"]
                                
                                # Display in a nice text area for editing
                                edited_content = st.text_area(
                                    "Review and edit as needed:",
                                    value=generated_text,
                                    height=300,
                                    key=f"edit_content_{esc['id']}"
                                )
                                
                                action_col_a, action_col_b, action_col_c = st.columns(3)
                                
                                with action_col_a:
                                    if st.button("📋 Copy to Clipboard", key=f"copy_{esc['id']}"):
                                        # Use st.code to make it easy to copy
                                        st.code(edited_content, language=None)
                                        st.info("👆 Select text above and copy (Cmd/Ctrl+C)")
                                
                                with action_col_b:
                                    # Download as text file
                                    st.download_button(
                                        label="⬇️ Download",
                                        data=edited_content,
                                        file_name=f"{assist_tool.replace(' ', '_').replace('📧', '').replace('📅', '').replace('📝', '').replace('📊', '').replace('📋', '').strip()}_{esc['student_id']}.txt",
                                        mime="text/plain",
                                        key=f"download_{esc['id']}"
                                    )
                                
                                with action_col_c:
                                    if st.button("🗑️ Clear", key=f"clear_gen_{esc['id']}"):
                                        del st.session_state[f"generated_content_{esc['id']}"]
                                        st.rerun()
            else:
                st.error(f"Failed to load escalations: {esc_resp.text}")
        
        except Exception as e:
            st.error(f"Error loading escalations: {e}")
        
        st.markdown("---")
        
        # Repeat Students Section
        st.markdown("### 🚨 Students Needing Attention")
        try:
            stats_resp = requests.get(f"{API_BASE}/advisor/dashboard/stats", timeout=10)
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
                repeat_students = stats.get("repeat_students", [])
                
                if repeat_students:
                    for student in repeat_students[:5]:
                        with st.expander(
                            f"⚠️ {student['name']} ({student['student_id']}) - "
                            f"{student['escalation_count']} escalations - "
                            f"Risk: {student['risk_level'].upper()}",
                            expanded=False
                        ):
                            st.write(f"**Student ID:** {student['student_id']}")
                            st.write(f"**Name:** {student['name']}")
                            st.write(f"**Total Escalations:** {student['escalation_count']}")
                            st.write(f"**Risk Level:** {student['risk_level']}")
                            
                            if st.button(f"View All Escalations", key=f"view_all_{student['student_id']}"):
                                # This would filter to show only this student's escalations
                                st.info(f"Filtering for student {student['student_id']}...")
                else:
                    st.success("✅ No students with multiple escalations")
        except:
            pass

# === TAB 4: Administrator Analytics Dashboard ===
if tab_admin and st.session_state.user_mode == "Administrator":
    with tab_admin:
        st.markdown("""
        <div class="admin-banner">
            <div>
                <h1 style="margin:0; color:#E5E7EB;">📊 Administrator Analytics Dashboard</h1>
                <p style="margin:0; color:#E5E7EB;">Comprehensive system insights and student behavior analytics</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load analytics data
        try:
            with open("/Users/DLP-I516-206/Desktop/ubi-code/suny/suny/backend/backend/data/analytics_data.json", "r") as f:
                analytics_data = json.load(f)
            
            question_logs = analytics_data.get("question_logs", [])
            
            # ========== SECTION 1: USAGE & ENGAGEMENT OVERVIEW ==========
            st.markdown("## 📈 Usage & Engagement Overview")
            st.markdown("---")
            
            # Key Metrics Row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Total questions
            total_questions = len(question_logs)
            
            # Active users (unique students)
            active_users = len(set([log["student_id"] for log in question_logs]))
            
            # Calculate daily active users (last 7 days)
            recent_logs = [log for log in question_logs if 
                          (datetime.now() - datetime.fromisoformat(log["timestamp"])).days <= 7]
            daily_active = len(set([log["student_id"] for log in recent_logs]))
            
            # Average satisfaction
            ratings = [log.get("satisfaction_rating", 0) for log in question_logs if log.get("satisfaction_rating")]
            avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0
            
            # Escalation rate
            escalated_count = sum(1 for log in question_logs if log.get("escalated", False))
            escalation_rate = (escalated_count / total_questions * 100) if total_questions > 0 else 0
            
            with col1:
                st.metric(
                    "Total Questions",
                    f"{total_questions:,}",
                    help="Total number of student questions asked"
                )
            
            with col2:
                st.metric(
                    "Active Users",
                    f"{active_users}",
                    help="Unique students who have used the system"
                )
            
            with col3:
                st.metric(
                    "Weekly Active",
                    f"{daily_active}",
                    help="Active students in the last 7 days"
                )
            
            with col4:
                st.metric(
                    "Avg Satisfaction",
                    f"{avg_satisfaction:.1f}/5",
                    delta=f"{(avg_satisfaction - 3.5):.1f}" if avg_satisfaction > 0 else None,
                    help="Average student satisfaction rating"
                )
            
            with col5:
                st.metric(
                    "Escalation Rate",
                    f"{escalation_rate:.1f}%",
                    delta=f"{(10 - escalation_rate):.1f}%" if escalation_rate < 10 else f"-{(escalation_rate - 10):.1f}%",
                    delta_color="inverse",
                    help="Percentage of questions escalated to human advisors"
                )
            
            st.markdown("---")
            
            # Visualizations Row 1
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Peak Usage Hours Heatmap
                st.markdown("### ⏰ Peak Usage Hours")
                
                # Create hourly usage data
                hour_counts = {}
                for log in question_logs:
                    hour = log.get("hour_of_day", 0)
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                
                # Create heatmap data by day of week and hour
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                heatmap_data = []
                for day in day_order:
                    day_hours = []
                    for hour in range(24):
                        count = sum(1 for log in question_logs 
                                  if log.get("day_of_week") == day and log.get("hour_of_day") == hour)
                        day_hours.append(count)
                    heatmap_data.append(day_hours)
                
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=heatmap_data,
                    x=[f"{h:02d}:00" for h in range(24)],
                    y=day_order,
                    colorscale=[
                        [0, '#F8FAFC'],
                        [0.2, '#DBEAFE'],
                        [0.4, '#93C5FD'],
                        [0.6, '#3B82F6'],
                        [0.8, '#1D4ED8'],
                        [1, '#1E3A8A']
                    ],
                    text=heatmap_data,
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    hovertemplate='%{y}<br>%{x}<br>Questions: %{z}<extra></extra>'
                ))
                
                fig_heatmap.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1E293B', size=11),
                    xaxis_title="Hour of Day",
                    yaxis_title="Day of Week",
                    margin=dict(l=80, r=20, t=20, b=50)
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            with viz_col2:
                # Most Frequently Asked Topics
                st.markdown("### 📚 Top Topics")
                
                topic_counts = {}
                for log in question_logs:
                    topic = log.get("topic", "Other")
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
                # Sort and get top 10
                sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                topics, counts = zip(*sorted_topics) if sorted_topics else ([], [])
                
                fig_topics = go.Figure(data=[go.Bar(
                    y=list(topics),
                    x=list(counts),
                    orientation='h',
                    marker=dict(
                        color=list(counts),
                        colorscale=[
                            [0, '#3B82F6'],
                            [0.5, '#1D4ED8'],
                            [1, '#1E3A8A']
                        ],
                        showscale=False
                    ),
                    text=list(counts),
                    textposition='auto',
                    hovertemplate='%{y}<br>Questions: %{x}<extra></extra>'
                )])
                
                fig_topics.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1E293B', size=11),
                    xaxis_title="Number of Questions",
                    yaxis_title="",
                    xaxis=dict(gridcolor='#E5E7EB'),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=150, r=20, t=20, b=50)
                )
                
                st.plotly_chart(fig_topics, use_container_width=True)
            
            # Daily/Weekly Trend Line Chart
            st.markdown("### 📊 Activity Trend (Last 30 Days)")
            
            # Group by date
            date_counts = {}
            for log in question_logs:
                log_date = datetime.fromisoformat(log["timestamp"]).date()
                if (datetime.now().date() - log_date).days <= 30:
                    date_str = log_date.isoformat()
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
            
            # Create complete date range
            dates = []
            counts_by_date = []
            for i in range(30, -1, -1):
                date = (datetime.now().date() - timedelta(days=i)).isoformat()
                dates.append(date)
                counts_by_date.append(date_counts.get(date, 0))
            
            fig_trend = go.Figure()
            
            fig_trend.add_trace(go.Scatter(
                x=dates,
                y=counts_by_date,
                mode='lines+markers',
                name='Questions',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=8, color='#1D4ED8'),
                fill='tozeroy',
                fillcolor='rgba(59, 130, 246, 0.1)',
                hovertemplate='%{x}<br>Questions: %{y}<extra></extra>'
            ))
            
            fig_trend.update_layout(
                height=320,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1E293B', size=11),
                xaxis_title="Date",
                yaxis_title="Number of Questions",
                xaxis=dict(gridcolor='#E5E7EB', tickangle=-45),
                yaxis=dict(gridcolor='#E5E7EB'),
                margin=dict(l=60, r=20, t=20, b=100),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.markdown("---")
            
            # ========== SECTION 2: QUALITY & ACCURACY MONITORING ==========
            st.markdown("## ✅ Quality & Accuracy Monitoring")
            st.markdown("---")
            
            qual_col1, qual_col2, qual_col3, qual_col4 = st.columns(4)
            
            # Calculate metrics
            flagged_count = sum(1 for log in question_logs if log.get("flagged_incorrect", False))
            flagged_rate = (flagged_count / total_questions * 100) if total_questions > 0 else 0
            
            # Average response time
            response_times = [log.get("response_time_seconds", 0) for log in question_logs]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Satisfaction distribution
            satisfied_count = sum(1 for r in ratings if r >= 4)
            satisfaction_pct = (satisfied_count / len(ratings) * 100) if ratings else 0
            
            with qual_col1:
                st.metric(
                    "Escalated Questions",
                    f"{escalated_count}",
                    delta=f"{escalation_rate:.1f}% of total",
                    help="Questions that required human advisor intervention"
                )
            
            with qual_col2:
                st.metric(
                    "Flagged Incorrect",
                    f"{flagged_count}",
                    delta=f"{flagged_rate:.1f}% rate",
                    delta_color="inverse",
                    help="Responses flagged as incorrect by students"
                )
            
            with qual_col3:
                st.metric(
                    "Avg Response Time",
                    f"{avg_response_time:.2f}s",
                    help="Average time to generate a response"
                )
            
            with qual_col4:
                st.metric(
                    "Satisfaction Rate",
                    f"{satisfaction_pct:.1f}%",
                    delta=f"{(satisfaction_pct - 75):.1f}%",
                    help="Percentage of students rating 4+ stars"
                )
            
            st.markdown("---")
            
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Satisfaction Rating Distribution
                st.markdown("### ⭐ Satisfaction Distribution")
                
                rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for r in ratings:
                    rating_counts[r] = rating_counts.get(r, 0) + 1
                
                fig_satisfaction = go.Figure(data=[go.Bar(
                    x=['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
                    y=[rating_counts[1], rating_counts[2], rating_counts[3], 
                       rating_counts[4], rating_counts[5]],
                    marker=dict(
                        color=['#EF4444', '#F59E0B', '#FACC15', '#22C55E', '#10B981']
                    ),
                    text=[rating_counts[1], rating_counts[2], rating_counts[3], 
                          rating_counts[4], rating_counts[5]],
                    textposition='auto',
                    hovertemplate='%{x}<br>Count: %{y}<extra></extra>'
                )])
                
                fig_satisfaction.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1E293B', size=11),
                    xaxis_title="Rating",
                    yaxis_title="Number of Responses",
                    xaxis=dict(gridcolor='#E5E7EB'),
                    yaxis=dict(gridcolor='#E5E7EB'),
                    margin=dict(l=60, r=20, t=20, b=60)
                )
                
                st.plotly_chart(fig_satisfaction, use_container_width=True)
            
            with viz_col2:
                # Escalation Reasons Pie Chart
                st.markdown("### 🎯 Escalation Breakdown")
                
                escalation_data = {
                    'Auto-Escalated': escalated_count,
                    'Flagged Incorrect': flagged_count,
                    'Not Escalated': total_questions - escalated_count - flagged_count
                }
                
                fig_escalation_pie = go.Figure(data=[go.Pie(
                    labels=list(escalation_data.keys()),
                    values=list(escalation_data.values()),
                    hole=0.4,
                    marker=dict(colors=['#EF4444', '#FACC15', '#22C55E']),
                    textinfo='label+percent',
                    textposition='auto',
                    hovertemplate='%{label}<br>Count: %{value}<br>%{percent}<extra></extra>'
                )])
                
                fig_escalation_pie.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1E293B', size=11),
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=True
                )
                
                st.plotly_chart(fig_escalation_pie, use_container_width=True)
            
            st.markdown("---")
            
            # ========== SECTION 3: STUDENT BEHAVIOR INSIGHTS ==========
            st.markdown("## 👥 Student Behavior Insights")
            st.markdown("---")
            
            # Students with most questions
            student_question_counts = {}
            for log in question_logs:
                sid = log["student_id"]
                student_question_counts[sid] = student_question_counts.get(sid, 0) + 1
            
            # Get top 10 most active students
            top_students = sorted(student_question_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Repeat help seekers (students with 10+ questions)
            repeat_students = [s for s, count in student_question_counts.items() if count >= 10]
            
            # Long conversations (high friction)
            long_conversations = [log for log in question_logs if log.get("conversation_length", 0) > 5]
            high_friction_topics = {}
            for log in long_conversations:
                topic = log.get("topic", "Other")
                high_friction_topics[topic] = high_friction_topics.get(topic, 0) + 1
            
            behav_col1, behav_col2, behav_col3, behav_col4 = st.columns(4)
            
            with behav_col1:
                st.metric(
                    "Repeat Help Seekers",
                    f"{len(repeat_students)}",
                    help="Students with 10+ questions (may need intervention)"
                )
            
            with behav_col2:
                st.metric(
                    "High Friction Topics",
                    f"{len(high_friction_topics)}",
                    help="Topics that generate long conversations"
                )
            
            with behav_col3:
                avg_conversation_length = sum(log.get("conversation_length", 0) for log in question_logs) / len(question_logs) if question_logs else 0
                st.metric(
                    "Avg Conversation Length",
                    f"{avg_conversation_length:.1f}",
                    help="Average number of message exchanges per question"
                )
            
            with behav_col4:
                avg_questions_per_student = total_questions / active_users if active_users > 0 else 0
                st.metric(
                    "Avg Questions/Student",
                    f"{avg_questions_per_student:.1f}",
                    help="Average number of questions per active student"
                )
            
            st.markdown("---")
            
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Top 10 Most Active Students
                st.markdown("### 🔥 Most Active Students")
                
                if top_students:
                    students, counts = zip(*top_students)
                    
                    fig_active_students = go.Figure(data=[go.Bar(
                        y=list(students),
                        x=list(counts),
                        orientation='h',
                        marker=dict(
                            color=list(counts),
                            colorscale=[
                                [0, '#10B981'],
                                [0.5, '#F59E0B'],
                                [1, '#EF4444']
                            ],
                            showscale=False
                        ),
                        text=list(counts),
                        textposition='auto',
                        hovertemplate='%{y}<br>Questions: %{x}<extra></extra>'
                    )])
                    
                    fig_active_students.update_layout(
                        height=380,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1E293B', size=11),
                        xaxis_title="Number of Questions",
                        yaxis_title="Student ID",
                        xaxis=dict(gridcolor='#E5E7EB'),
                        yaxis=dict(autorange="reversed"),
                        margin=dict(l=120, r=20, t=20, b=50)
                    )
                    
                    st.plotly_chart(fig_active_students, use_container_width=True)
            
            with viz_col2:
                # High Friction Topics
                st.markdown("### 🔥 High Friction Areas")
                
                if high_friction_topics:
                    sorted_friction = sorted(high_friction_topics.items(), key=lambda x: x[1], reverse=True)[:8]
                    topics_fric, counts_fric = zip(*sorted_friction)
                    
                    fig_friction = go.Figure(data=[go.Bar(
                        y=list(topics_fric),
                        x=list(counts_fric),
                        orientation='h',
                        marker=dict(color='#EF4444'),
                        text=list(counts_fric),
                        textposition='auto',
                        hovertemplate='%{y}<br>Long Conversations: %{x}<extra></extra>'
                    )])
                    
                    fig_friction.update_layout(
                        height=380,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1E293B', size=11),
                        xaxis_title="Long Conversations (5+ exchanges)",
                        yaxis_title="",
                        xaxis=dict(gridcolor='#E5E7EB'),
                        yaxis=dict(autorange="reversed"),
                        margin=dict(l=150, r=20, t=20, b=60)
                    )
                    
                    st.plotly_chart(fig_friction, use_container_width=True)
            
            st.markdown("---")
            
            # ========== SECTION 4: RISK IDENTIFICATION ==========
            st.markdown("## ⚠️ Risk Identification & Patterns")
            st.markdown("---")
            
            # Load student profiles for risk analysis
            try:
                students_resp = requests.get(f"{API_BASE}/advisor/students", timeout=10)
                if students_resp.status_code == 200:
                    all_students = students_resp.json()
                    
                    # Risk level distribution
                    risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                    for student in all_students:
                        risk = student.get('risk_level', 'low')
                        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
                    
                    # Students at risk
                    at_risk_students = [s for s in all_students if s.get('risk_level') in ['high', 'critical']]
                    
                    risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
                    
                    with risk_col1:
                        st.metric(
                            "Low Risk",
                            risk_distribution['low'],
                            help="Students performing well"
                        )
                    
                    with risk_col2:
                        st.metric(
                            "Medium Risk",
                            risk_distribution['medium'],
                            help="Students needing monitoring"
                        )
                    
                    with risk_col3:
                        st.metric(
                            "High Risk",
                            risk_distribution['high'],
                            delta="Needs attention",
                            delta_color="off",
                            help="Students requiring intervention"
                        )
                    
                    with risk_col4:
                        st.metric(
                            "Critical Risk",
                            risk_distribution['critical'],
                            delta="Urgent",
                            delta_color="off",
                            help="Students in critical need of support"
                        )
                    
                    st.markdown("---")
                    
                    viz_col1, viz_col2 = st.columns(2)
                    
                    with viz_col1:
                        # Risk Level Pie Chart
                        st.markdown("### 📊 Risk Level Distribution")
                        
                        fig_risk_pie = go.Figure(data=[go.Pie(
                            labels=['Low', 'Medium', 'High', 'Critical'],
                            values=[risk_distribution['low'], risk_distribution['medium'],
                                   risk_distribution['high'], risk_distribution['critical']],
                            hole=0.4,
                            marker=dict(colors=['#22C55E', '#FACC15', '#EF4444', '#DC2626']),
                            textinfo='label+value',
                            textposition='auto',
                            hovertemplate='%{label} Risk<br>Students: %{value}<br>%{percent}<extra></extra>'
                        )])
                        
                        fig_risk_pie.update_layout(
                            height=380,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#1E293B', size=11),
                            margin=dict(l=20, r=20, t=20, b=20),
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig_risk_pie, use_container_width=True)
                    
                    with viz_col2:
                        # At-Risk Students Scatter Plot (GPA vs Escalations)
                        st.markdown("### 🎯 Student Risk Analysis")
                        
                        if at_risk_students:
                            gpas = [s.get('gpa', 0) for s in at_risk_students]
                            escalations = [s.get('total_escalations', 0) for s in at_risk_students]
                            names = [s.get('name', s.get('student_id', '')) for s in at_risk_students]
                            risk_levels = [s.get('risk_level', 'medium') for s in at_risk_students]
                            
                            # Color map
                            color_map = {'medium': '#FACC15', 'high': '#EF4444', 'critical': '#DC2626'}
                            colors = [color_map.get(r, '#94A3B8') for r in risk_levels]
                            
                            fig_scatter = go.Figure(data=[go.Scatter(
                                x=gpas,
                                y=escalations,
                                mode='markers',
                                marker=dict(
                                    size=12,
                                    color=colors,
                                    line=dict(width=2, color='#FFFFFF')
                                ),
                                text=names,
                                hovertemplate='%{text}<br>GPA: %{x:.2f}<br>Escalations: %{y}<extra></extra>'
                            )])
                            
                            fig_scatter.update_layout(
                                height=380,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#1E293B', size=11),
                                xaxis_title="GPA",
                                yaxis_title="Total Escalations",
                                xaxis=dict(gridcolor='#E5E7EB'),
                                yaxis=dict(gridcolor='#E5E7EB'),
                                margin=dict(l=60, r=20, t=20, b=60)
                            )
                            
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        else:
                            st.info("No at-risk students identified")
                    
                    # At-Risk Students Table
                    if at_risk_students:
                        st.markdown("### 🚨 Students Requiring Immediate Attention")
                        
                        for student in at_risk_students[:10]:
                            risk_level = student.get('risk_level', 'medium')
                            risk_class = f"risk-{risk_level}"
                            risk_emoji = {'medium': '⚠️', 'high': '🔴', 'critical': '🚨'}.get(risk_level, '⚠️')
                            
                            with st.expander(
                                f"{risk_emoji} {student.get('name', 'Unknown')} ({student.get('student_id', 'N/A')}) - "
                                f"GPA: {student.get('gpa', 0):.2f} - Risk: {risk_level.upper()}",
                                expanded=False
                            ):
                                col_a, col_b = st.columns(2)
                                
                                with col_a:
                                    st.markdown(f"**Student ID:** {student.get('student_id', 'N/A')}")
                                    st.markdown(f"**Name:** {student.get('name', 'Unknown')}")
                                    st.markdown(f"**Major:** {student.get('major', 'Undeclared')}")
                                    st.markdown(f"**GPA:** {student.get('gpa', 0):.2f}")
                                    st.markdown(f"**Risk Level:** <span class='{risk_class}'>{risk_level.upper()}</span>", 
                                              unsafe_allow_html=True)
                                
                                with col_b:
                                    st.markdown(f"**Total Escalations:** {student.get('total_escalations', 0)}")
                                    st.markdown(f"**Questions Asked:** {student_question_counts.get(student.get('student_id'), 0)}")
                                    st.markdown(f"**Last Interaction:** {student.get('last_interaction', 'N/A')[:10]}")
                                    
                                    if st.button(f"View Profile", key=f"view_profile_{student.get('student_id')}"):
                                        st.info(f"Viewing full profile for {student.get('student_id')}")
                
            except Exception as e:
                st.error(f"Could not load student risk data: {e}")
            
            st.markdown("---")
            
            # ========== SECTION 5: SYSTEM PERFORMANCE ==========
            st.markdown("## ⚡ System Performance Metrics")
            st.markdown("---")
            
            perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
            
            # Response time distribution
            fast_responses = sum(1 for t in response_times if t < 3)
            medium_responses = sum(1 for t in response_times if 3 <= t < 10)
            slow_responses = sum(1 for t in response_times if t >= 10)
            
            with perf_col1:
                st.metric(
                    "Fast Responses (<3s)",
                    f"{fast_responses}",
                    delta=f"{(fast_responses/len(response_times)*100):.1f}%" if response_times else "0%",
                    help="Responses generated in under 3 seconds"
                )
            
            with perf_col2:
                st.metric(
                    "Medium (3-10s)",
                    f"{medium_responses}",
                    delta=f"{(medium_responses/len(response_times)*100):.1f}%" if response_times else "0%",
                    help="Responses taking 3-10 seconds"
                )
            
            with perf_col3:
                st.metric(
                    "Slow (>10s)",
                    f"{slow_responses}",
                    delta=f"{(slow_responses/len(response_times)*100):.1f}%" if response_times else "0%",
                    delta_color="inverse",
                    help="Responses taking over 10 seconds"
                )
            
            with perf_col4:
                st.metric(
                    "Median Response Time",
                    f"{sorted(response_times)[len(response_times)//2]:.2f}s" if response_times else "0s",
                    help="Median system response time"
                )
            
            # Response Time Distribution Chart
            st.markdown("### 📈 Response Time Distribution")
            
            fig_response_time = go.Figure(data=[go.Histogram(
                x=response_times,
                nbinsx=30,
                marker=dict(
                    color='#3B82F6',
                    line=dict(color='#1D4ED8', width=1)
                ),
                hovertemplate='Response Time: %{x:.2f}s<br>Count: %{y}<extra></extra>'
            )])
            
            fig_response_time.update_layout(
                height=320,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1E293B', size=11),
                xaxis_title="Response Time (seconds)",
                yaxis_title="Frequency",
                xaxis=dict(gridcolor='#E5E7EB'),
                yaxis=dict(gridcolor='#E5E7EB'),
                margin=dict(l=60, r=20, t=20, b=60),
                bargap=0.1
            )
            
            st.plotly_chart(fig_response_time, use_container_width=True)
            
        except FileNotFoundError:
            st.error("📁 Analytics data file not found. Please ensure the backend has generated analytics data.")
        except Exception as e:
            st.error(f"❌ Error loading analytics data: {e}")
        
        st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ========== SECTION 6: CONTENT MANAGEMENT ==========
        st.markdown("## 📁 Content Management")
        st.markdown("### Upload and manage academic documents for the AI knowledge base")
        st.markdown("---")
        
        # Create tabs for Upload and Manage
        content_tab1, content_tab2 = st.tabs(["📤 Upload Documents", "📚 Manage Documents"])
        
        with content_tab1:
            st.markdown("### Upload New Documents")
            st.markdown("Upload PDF or TXT files containing course catalogs, policies, guides, or academic information.")
            
            # Upload area
            st.markdown("""
            <div class="upload-area">
                <div style="font-size:3rem; margin-bottom:1rem;">📄</div>
                <h3 style="color:#1D4ED8; margin-bottom:0.5rem;">Drag & Drop Files Here</h3>
                <p style="color:#64748B; margin-bottom:1.5rem;">or click below to browse</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose PDF or TXT files",
                type=["pdf", "txt"],
                accept_multiple_files=True,
                key="doc_uploader",
                help="Upload documents to add to the AI knowledge base"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} file(s) selected")
                
                # Show selected files
                for file in uploaded_files:
                    file_extension = file.name.split('.')[-1].upper()
                    file_size_kb = file.size / 1024
                    
                    icon_class = "document-icon-pdf" if file_extension == "PDF" else "document-icon-txt"
                    
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; padding:1rem; background:#F8FAFC; border-radius:12px; margin:0.5rem 0;">
                        <div class="document-icon {icon_class}">{file_extension}</div>
                        <div style="flex:1; margin-left:1rem;">
                            <div style="font-weight:600; color:#1E293B;">{file.name}</div>
                            <div style="font-size:0.875rem; color:#64748B;">{file_size_kb:.1f} KB</div>
                        </div>
                        <div style="color:#22C55E; font-weight:600;">Ready</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Process button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🚀 Process & Add to Knowledge Base", type="primary", use_container_width=True):
                        # Save uploaded files to pdf directory
                        import os
                        import shutil
                        
                        pdf_dir = "/Users/DLP-I516-206/Desktop/ubi-code/suny/suny/backend/data/pdfs"
                        os.makedirs(pdf_dir, exist_ok=True)
                        
                        saved_files = []
                        for file in uploaded_files:
                            # Save to pdfs directory
                            file_path = os.path.join(pdf_dir, file.name)
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())
                            saved_files.append(file.name)
                            logger.info(f"Saved file: {file.name}")
                        
                        # Processing status
                        with st.container():
                            st.markdown("""
                            <div class="processing-modal">
                                <h3 style="color:#1D4ED8; text-align:center; margin-bottom:1.5rem;">Processing Documents</h3>
                            """, unsafe_allow_html=True)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Show uploading status
                            status_text.markdown(f"""
                            <div class="processing-step processing-step-active">
                                <div style="margin-right:1rem; font-size:1.5rem;">📤</div>
                                <div>
                                    <div style="font-weight:600; color:#1E293B;">Uploading {len(uploaded_files)} file(s)</div>
                                    <div style="font-size:0.875rem; color:#64748B;">Saving to document directory...</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            progress_bar.progress(0.2)
                            time.sleep(0.5)
                            
                            # Call backend to process
                            status_text.markdown(f"""
                            <div class="processing-step processing-step-active">
                                <div style="margin-right:1rem; font-size:1.5rem;">🔄</div>
                                <div>
                                    <div style="font-weight:600; color:#1E293B;">Initializing Processing</div>
                                    <div style="font-size:0.875rem; color:#64748B;">Contacting backend API...</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            progress_bar.progress(0.4)
                            
                            # Call the same init endpoint used by the sidebar
                            try:
                                success, msg, count, skipped = initialize_system(force_rebuild=False)
                                
                                if success:
                                    progress_bar.progress(1.0)
                                    status_text.markdown(f"""
                                    <div class="processing-step processing-step-complete">
                                        <div style="margin-right:1rem; font-size:1.5rem;">✅</div>
                                        <div>
                                            <div style="font-weight:600; color:#1E293B;">Processing Complete!</div>
                                            <div style="font-size:0.875rem; color:#22C55E;">{msg}</div>
                                            <div style="font-size:0.875rem; color:#22C55E;">Total chunks in database: {count}</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    st.success(f"🎉 Successfully processed {len(uploaded_files)} document(s)!")
                                    st.info(f"💡 The AI assistant can now answer questions using these documents. Total chunks: {count}")
                                    
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    progress_bar.progress(1.0)
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    st.error(f"❌ Processing failed: {msg}")
                                    
                            except Exception as e:
                                progress_bar.progress(1.0)
                                st.markdown("</div>", unsafe_allow_html=True)
                                st.error(f"❌ Error during processing: {e}")
                                logger.error(f"Processing error: {e}")
        
        with content_tab2:
            st.markdown("### Indexed Documents")
            st.markdown("View and manage all documents currently in the knowledge base.")
            
            # Get document list from backend
            try:
                with open("/Users/DLP-I516-206/Desktop/ubi-code/suny/suny/backend/vector_store/processed_pdfs.json", "r") as f:
                    processed_docs = json.load(f)
                
                if processed_docs:
                    # Check if it's a simple list of strings (filenames only)
                    if isinstance(processed_docs, list) and all(isinstance(doc, str) for doc in processed_docs):
                        # Simple string list format - get actual file info
                        import os
                        pdf_dir = "/Users/DLP-I516-206/Desktop/ubi-code/suny/suny/backend/data/pdfs"
                        
                        doc_details = []
                        for filename in processed_docs:
                            file_path = os.path.join(pdf_dir, filename)
                            if os.path.exists(file_path):
                                size_bytes = os.path.getsize(file_path)
                                size_kb = size_bytes / 1024
                                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                
                                doc_details.append({
                                    'name': filename,
                                    'size_kb': size_kb,
                                    'upload_date': modified_time.isoformat(),
                                    'status': 'active',
                                    'version': 1,
                                    'chunk_count': 0  # Will be populated by backend later
                                })
                            else:
                                # File doesn't exist, use placeholder data
                                doc_details.append({
                                    'name': filename,
                                    'size_kb': 0,
                                    'upload_date': datetime.now().isoformat(),
                                    'status': 'active',
                                    'version': 1,
                                    'chunk_count': 0
                                })
                        
                        processed_docs = doc_details
                    
                    # Now process as list of dicts
                    doc_count = len(processed_docs)
                    total_size = sum(doc.get('size_kb', 0) for doc in processed_docs if isinstance(doc, dict))
                    total_chunks = sum(doc.get('chunk_count', 0) for doc in processed_docs if isinstance(doc, dict))
                    
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    
                    with metric_col1:
                        st.metric("Total Documents", doc_count)
                    
                    with metric_col2:
                        st.metric("Total Size", f"{total_size:.1f} KB")
                    
                    with metric_col3:
                        st.metric("Total Chunks", total_chunks if total_chunks > 0 else "N/A")
                    
                    with metric_col4:
                        active_docs = sum(1 for doc in processed_docs if isinstance(doc, dict) and doc.get('status') == 'active')
                        st.metric("Active Documents", active_docs)
                    
                    st.markdown("---")
                    
                    # Document list
                    st.markdown("### 📋 Document Library")
                    
                    # Sort by upload date (newest first)
                    sorted_docs = sorted(
                        processed_docs,
                        key=lambda x: x.get('upload_date', '') if isinstance(x, dict) else '',
                        reverse=True
                    )
                    
                    for doc_info in sorted_docs:
                        if not isinstance(doc_info, dict):
                            continue
                        
                        doc_name = doc_info.get('name', 'Unknown')
                        file_extension = doc_name.split('.')[-1].upper()
                        icon_class = "document-icon-pdf" if file_extension == "PDF" else "document-icon-txt"
                        
                        version = doc_info.get('version', 1)
                        upload_date = doc_info.get('upload_date', 'Unknown')
                        chunk_count = doc_info.get('chunk_count', 0)
                        size_kb = doc_info.get('size_kb', 0)
                        status = doc_info.get('status', 'active')
                        
                        status_badge = {
                            'active': '<span class="version-badge-active">Active</span>',
                            'deprecated': '<span class="version-badge-old">Deprecated</span>',
                            'replaced': '<span class="version-badge-old">Replaced</span>'
                        }.get(status, '<span class="version-badge-active">Active</span>')
                        
                        st.markdown(f"""
                        <div class="document-card">
                            <div style="display:flex; align-items:center;">
                                <div class="document-icon {icon_class}">{file_extension}</div>
                                <div style="flex:1; margin-left:1.5rem;">
                                    <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                                        <h4 style="margin:0; color:#1E293B;">{doc_name}</h4>
                                        <div style="margin-left:1rem;">
                                            {status_badge}
                                            <span class="version-badge version-badge-old" style="margin-left:0.5rem;">v{version}</span>
                                        </div>
                                    </div>
                                    <div style="display:flex; gap:2rem; font-size:0.875rem; color:#64748B;">
                                        <div><strong>Uploaded:</strong> {upload_date[:10] if len(upload_date) > 10 else upload_date}</div>
                                        <div><strong>Chunks:</strong> {chunk_count}</div>
                                        <div><strong>Size:</strong> {size_kb:.1f} KB</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            if st.button("👁️ View", key=f"view_{doc_name}", use_container_width=True):
                                st.info(f"Viewing metadata for: {doc_name}")
                        
                        with col2:
                            if st.button("🔄 Replace", key=f"replace_{doc_name}", use_container_width=True):
                                st.info(f"Upload a new version to replace: {doc_name}")
                        
                        with col3:
                            if st.button("📋 Duplicate", key=f"duplicate_{doc_name}", use_container_width=True):
                                st.info(f"Creating duplicate of: {doc_name}")
                        
                        with col4:
                            if status == 'active':
                                if st.button("⏸️ Deactivate", key=f"deactivate_{doc_name}", use_container_width=True):
                                    st.warning(f"Deactivating: {doc_name}")
                            else:
                                if st.button("▶️ Activate", key=f"activate_{doc_name}", use_container_width=True):
                                    st.success(f"Activating: {doc_name}")
                        
                        with col5:
                            if st.button("🗑️ Delete", key=f"delete_{doc_name}", use_container_width=True, type="secondary"):
                                st.error(f"⚠️ Delete {doc_name}? This action cannot be undone!")
                        
                        st.markdown("<hr style='margin:0.5rem 0; border:none; border-top:1px solid #F1F5F9;'>", unsafe_allow_html=True)
                    
                else:
                    st.info("📭 No documents have been uploaded yet. Use the 'Upload Documents' tab to add your first document.")
            
            except FileNotFoundError:
                # Show sample/demo documents
                st.info("📁 Knowledge Base Status: Using default configuration")
                st.markdown("### Sample Documents")
                
                sample_docs = [
                    {"name": "attention.pdf", "date": "2025-12-04", "chunks": 142, "size": 245.3, "version": 1},
                    {"name": "cs229.pdf", "date": "2025-12-03", "chunks": 289, "size": 512.8, "version": 1},
                    {"name": "lim.pdf", "date": "2025-12-02", "chunks": 98, "size": 178.4, "version": 1},
                    {"name": "quant.pdf", "date": "2025-12-01", "chunks": 156, "size": 298.7, "version": 1},
                    {"name": "quantum-mech.pdf", "date": "2025-11-30", "chunks": 234, "size": 421.2, "version": 1},
                    {"name": "scaling.pdf", "date": "2025-11-29", "chunks": 187, "size": 356.9, "version": 1},
                ]
                
                for doc in sample_docs:
                    st.markdown(f"""
                    <div class="document-card">
                        <div style="display:flex; align-items:center;">
                            <div class="document-icon document-icon-pdf">PDF</div>
                            <div style="flex:1; margin-left:1.5rem;">
                                <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                                    <h4 style="margin:0; color:#1E293B;">{doc['name']}</h4>
                                    <span class="version-badge-active" style="margin-left:1rem;">Active</span>
                                    <span class="version-badge version-badge-old" style="margin-left:0.5rem;">v{doc['version']}</span>
                                </div>
                                <div style="display:flex; gap:2rem; font-size:0.875rem; color:#64748B;">
                                    <div><strong>Uploaded:</strong> {doc['date']}</div>
                                    <div><strong>Chunks:</strong> {doc['chunks']}</div>
                                    <div><strong>Size:</strong> {doc['size']} KB</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)