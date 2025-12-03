import streamlit as st
import requests
import time
from datetime import date
import logging
from typing import Dict

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

# === Modern CSS ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {font-family: 'Inter', sans-serif;}
    .main {background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #1e2139 0%, #16182d 100%); border-right: 1px solid rgba(94, 234, 212, 0.1);}
    h1 {color: #5eead4; font-weight: 700; text-align: center; text-shadow: 0 0 30px rgba(94, 234, 212, 0.3);}
    .stButton>button {background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%); color: #0f172a; border: none; border-radius: 10px; padding: 0.75rem; font-weight: 600; box-shadow: 0 4px 15px rgba(94, 234, 212, 0.3);}
    .stButton>button:hover {transform: translateY(-2px); box-shadow: 0 6px 25px rgba(94, 234, 212, 0.4);}
    .chat-message {padding: 1.25rem; border-radius: 16px; margin-bottom: 1rem; animation: fadeIn 0.3s ease; backdrop-filter: blur(10px);}
    @keyframes fadeIn {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: translateY(0);}}
    .user-message {background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%); color: #0f172a; margin-left: 15%; box-shadow: 0 4px 20px rgba(94, 234, 212, 0.3);}
    .assistant-message {background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%); color: #e2e8f0; margin-right: 15%; border: 1px solid rgba(94, 234, 212, 0.15);}
    .citation-box {background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%); border-left: 4px solid #5eead4; padding: 1rem; margin: 0.75rem 0; border-radius: 8px; border: 1px solid rgba(94, 234, 212, 0.2);}
    .citation-title {color: #5eead4; font-weight: 600;}
    .footer {text-align: center; color: #64748b; font-size: 0.85rem; padding: 2rem 0; border-top: 1px solid rgba(94, 234, 212, 0.1); margin-top: 3rem;}
    .footer-highlight {color: #5eead4; font-weight: 600;}
    .stSpinner > div {border-top-color: #5eead4 !important;}
    .block-container {padding-bottom: 6rem;}
    .escalation-notice {
        background: linear-gradient(135deg, rgba(94, 234, 212, 0.2) 0%, rgba(20, 184, 166, 0.2) 100%);
        border: 2px solid #5eead4;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 10px rgba(94, 234, 212, 0.4); }
        50% { box-shadow: 0 0 20px rgba(94, 234, 212, 0.6); }
    }
</style>
""", unsafe_allow_html=True)

# === Session State ===
for key in ['messages', 'citations', 'initialized', 'auto_init_done', 'study_materials', 
            'student_id', 'selected_escalation', 'advisor_mode', 'show_escalation_form',
            'last_question', 'last_answer', 'last_escalation_id']:
    if key not in st.session_state:
        if key in ['messages', 'citations', 'study_materials']:
            st.session_state[key] = []
        elif key == 'student_id':
            st.session_state[key] = "STUDENT_001"  # Default student ID
        elif key in ['advisor_mode', 'show_escalation_form']:
            st.session_state[key] = False
        elif key in ['last_question', 'last_answer']:
            st.session_state[key] = ""
        elif key == 'last_escalation_id':
            st.session_state[key] = None
        else:
            st.session_state[key] = False

# === Helper Functions ===
def check_health(): 
    try: 
        return requests.get(f"{API_BASE}/academic/health", timeout=5).status_code == 200 
    except: 
        return False

def check_vector_store_status():
    try:
        r = requests.get(f"{API_BASE}/academic/status", timeout=5)
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
    st.markdown("<small style='color: #64748b;'>RAG + Study Tools</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Mode toggle
    st.markdown("### 👤 User Mode")
    mode = st.radio(
        "Select Mode",
        ["🎓 Student", "👨‍🏫 Advisor"],
        index=1 if st.session_state.advisor_mode else 0,
        key="mode_radio"
    )
    st.session_state.advisor_mode = (mode == "👨‍🏫 Advisor")
    
    if not st.session_state.advisor_mode:
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
if st.session_state.advisor_mode:
    # Advisor mode: Only show dashboard
    tab3 = st.container()
    tab1 = None
    tab2 = None
else:
    # Student mode: Show chat and study tools
    tab1, tab2 = st.tabs(["💬 Academic Guidance Chat", "📖 Study Tools"])
    tab3 = None

# === TAB 1: Academic Chat ===
if tab1:
    with tab1:
        st.markdown("# 💬 Academic Guidance Chat")
        
        if not st.session_state.initialized:
            st.warning("⚠️ Please initialize the system first using the sidebar")
            st.stop()

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

        # Chat input
        user_prompt = st.text_input("Ask about courses, requirements, policies...", 
                                    key="chat_text_tab",
                                    placeholder="e.g., What are the CS major requirements?")
        
        col_send, col_escalate = st.columns([3, 1])
        
        with col_send:
            send_clicked = st.button("📤 Send", key="send_tab", type="primary", use_container_width=True)
        
        with col_escalate:
            if not st.session_state.advisor_mode and st.session_state.messages:
                escalate_clicked = st.button("🆘 Escalate to Advisor", key="escalate_btn", use_container_width=True)
            else:
                escalate_clicked = False
        
        if send_clicked or (user_prompt and user_prompt != st.session_state.get('last_prompt', '')):
            if user_prompt:
                st.session_state.last_prompt = user_prompt
                st.session_state.messages.append({"role": "user", "content": user_prompt})
                
                with st.spinner("🔍 Searching knowledge base..."):
                    resp = send_message(
                        user_prompt, 
                        st.session_state.get("top_k_slider", 5),
                        st.session_state.get("student_id") if not st.session_state.advisor_mode else None
                    )
                    answer = resp.get("answer", "No answer")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.citations = resp.get("citations", [])
                    
                    # Store last response for potential manual escalation
                    st.session_state.last_question = user_prompt
                    st.session_state.last_answer = answer
                    st.session_state.last_escalation_id = resp.get("escalation_id")
                
                st.rerun()
        
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
                    <div style="background:rgba(30,41,59,0.9); border:1px solid rgba(94,234,212,0.3); border-radius:16px; padding:1.3rem; margin:1rem 0;">
                        <strong style="color:#5eead4;">Q{i+1}: {q}</strong><br><br>
                        <details><summary style="color:#94a3b8; cursor:pointer;">Show Answer</summary>
                        <p style="color:#e2e8f0; margin-top:0.8rem;">{a}</p></details>
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
                            st.markdown(f'<span style="color:#5eead4;">✅ {opt}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span style="color:#94a3b8;">• {opt}</span>', unsafe_allow_html=True)

                    explanation = q.get("explanation", "")
                    if explanation:
                        st.markdown(f"""
                        <details style="margin:1rem 0;">
                            <summary style="color:#5eead4; cursor:pointer; font-weight:600;">💡 Show Explanation</summary>
                            <p style="color:#cbd5e1; margin-top:0.5rem; padding-left:0.5rem;">{explanation}</p>
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
if tab3 and st.session_state.advisor_mode:
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
                    st.metric("Total Escalations", stats.get("total_escalations", 0))
                with col2:
                    st.metric("Pending", stats.get("pending", 0), delta=None, delta_color="off")
                with col3:
                    st.metric("In Progress", stats.get("in_progress", 0))
                with col4:
                    st.metric("Resolved", stats.get("resolved", 0))
                with col5:
                    st.metric("High Risk Students", stats.get("high_risk_students", 0))
                
                st.markdown("---")
                
                # Visualizations
                st.markdown("### 📊 Escalation Analytics")
                
                viz_col1, viz_col2, viz_col3 = st.columns(3)
                
                with viz_col1:
                    # Pie Chart - Status Distribution
                    import plotly.graph_objects as go
                    
                    status_data = {
                        'Pending': stats.get("pending", 0),
                        'In Progress': stats.get("in_progress", 0),
                        'Resolved': stats.get("resolved", 0)
                    }
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=list(status_data.keys()),
                        values=list(status_data.values()),
                        hole=0.4,
                        marker=dict(colors=['#f59e0b', '#3b82f6', '#10b981']),
                        textinfo='label+percent',
                        textposition='auto',
                    )])
                    
                    fig_pie.update_layout(
                        title="Escalation Status Distribution",
                        showlegend=True,
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0', size=12),
                        title_font=dict(size=16, color='#5eead4'),
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
                                    colorscale=[[0, '#10b981'], [0.5, '#f59e0b'], [1, '#ef4444']],
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
                                font=dict(color='#e2e8f0', size=12),
                                title_font=dict(size=16, color='#5eead4'),
                                xaxis=dict(gridcolor='rgba(94,234,212,0.1)'),
                                yaxis=dict(gridcolor='rgba(94,234,212,0.1)'),
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
                                    color=['#10b981', '#f59e0b', '#ef4444', '#dc2626']
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
                                font=dict(color='#e2e8f0', size=12),
                                title_font=dict(size=16, color='#5eead4'),
                                xaxis=dict(gridcolor='rgba(94,234,212,0.1)'),
                                yaxis=dict(gridcolor='rgba(94,234,212,0.1)'),
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
                            expanded=(esc['status'] == 'pending')
                        ):
                            # Two column layout
                            col_left, col_right = st.columns([2, 1])
                            
                            with col_left:
                                # Question and Response
                                st.markdown("#### 💬 Student Question")
                                st.markdown(f'<div style="background:rgba(94,234,212,0.1); padding:1rem; border-radius:8px; border-left:4px solid #5eead4;">{esc["question"]}</div>', 
                                          unsafe_allow_html=True)
                                
                                st.markdown("#### 🤖 AI Response")
                                st.markdown(f'<div style="background:rgba(30,41,59,0.9); padding:1rem; border-radius:8px; color:#e2e8f0;">{esc["ai_response"]}</div>', 
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
                                                st.markdown(f'<div style="background:rgba(94,234,212,0.1); padding:0.5rem; border-radius:4px; margin-bottom:0.5rem;">{content}</div>', 
                                                          unsafe_allow_html=True)
                                            else:
                                                st.markdown(f'**🤖 AI** ({timestamp})')
                                                st.markdown(f'<div style="background:rgba(30,41,59,0.5); padding:0.5rem; border-radius:4px; margin-bottom:0.5rem;">{content}</div>', 
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
                                        <div style="background:rgba(30,41,59,0.9); padding:1rem; border-radius:8px; border:1px solid rgba(94,234,212,0.2); word-wrap:break-word; overflow-wrap:break-word;">
                                            <p style="margin:0.3rem 0; word-wrap:break-word;"><strong>Name:</strong><br/>{profile.get('name', 'Unknown')}</p>
                                            <p style="margin:0.3rem 0;"><strong>Major:</strong><br/>{profile.get('major', 'Undeclared')}</p>
                                            <p style="margin:0.3rem 0;"><strong>GPA:</strong> {profile.get('gpa', 'N/A')}</p>
                                            <p style="margin:0.3rem 0;"><strong>Risk Level:</strong> <span style="color:{risk_color}; font-weight:bold;">{risk_level.upper()}</span></p>
                                            <p style="margin:0.3rem 0;"><strong>Total Escalations:</strong> {profile.get('total_escalations', 0)}</p>
                                            <p style="margin:0.3rem 0;"><strong>Last Interaction:</strong><br/>{profile.get('last_interaction', 'N/A')[:10]}</p>
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
                            f"Risk: {student['risk_level'].upper()}"
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

# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)