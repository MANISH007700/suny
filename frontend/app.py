
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
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE = "http://localhost:8888"

# === Modern CSS (from Code 2) ===
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
    .block-container {padding-bottom: 6rem;}  /* Make room for fixed input */
</style>
""", unsafe_allow_html=True)

# === Session State ===
for key in ['messages', 'citations', 'initialized', 'auto_init_done', 'study_materials']:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ['messages', 'citations', 'study_materials'] else False

# === Helper Functions (unchanged) ===
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
            r = requests.post(f"{API_BASE}/academic/init", json={"pdf_dir": "./backend/data/pdfs/", "force_rebuild": force_rebuild}, timeout=300)
            if r.status_code == 200:
                data = r.json()
                st.session_state.initialized = True
                return True, data['message'], data.get('count', 0), data.get('skipped', False)
            return False, f"Error: {r.text}", 0, False
    except Exception as e:
        return False, str(e), 0, False

def send_message(question: str, top_k: int = 5):
    try:
        r = requests.post(f"{API_BASE}/academic/chat", json={"question": question, "top_k": top_k}, timeout=120)
        return r.json() if r.status_code == 200 else {"answer": "Error", "citations": []}
    except:
        return {"answer": "Connection error", "citations": []}

# === Sidebar ===
with st.sidebar:
    st.markdown("# SUNY Academic Assistant")
    st.markdown("<small style='color: #64748b;'>RAG + Study Tools</small>", unsafe_allow_html=True)
    st.markdown("---")

    healthy = check_health()
    st.markdown("### System Status")
    if healthy:
        st.success("Backend Connected")
    else:
        st.error("Backend Offline")

    if st.session_state.initialized:
        st.success("Knowledge Base Ready")
    else:
        st.warning("Not Initialized")

    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("Initialize System"):
            success, msg, count, _ = initialize_system(st.checkbox("Force rebuild", key="force_cb"))
            if success:
                st.success(msg)
                if count: st.info(f"Loaded {count} chunks")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    st.markdown("### Settings")
    top_k = st.slider("Retrieval count", 1, 10, 5, key="top_k_slider")
    if st.button("Clear Academic Chat"):
        st.session_state.messages = []
        st.session_state.citations = []
        st.rerun()

# === Auto Init ===
if not st.session_state.auto_init_done and healthy:
    st.session_state.auto_init_done = True
    populated, count = check_vector_store_status()
    if populated:
        st.session_state.initialized = True  # ← ADD THIS LINE
        st.success(f"Knowledge base ready! ({count} chunks loaded)")
    else:
        with st.spinner("First-time setup: Processing academic documents..."):
            success, msg, count, skipped = initialize_system(False)
            if success:
                st.success(f"Initialized! {count} chunks loaded")
                st.session_state.initialized = True

    
# === TABS ===
tab1, tab2 = st.tabs(["Academic Guidance Chat", "Study Tools"])

# === TAB 1: Academic Chat ===
with tab1:
    st.markdown("# Academic Guidance Chat")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>AI Advisor</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)

    if st.session_state.citations:
        with st.expander("View Sources", expanded=False):
            for i, c in enumerate(st.session_state.citations, 1):
                st.markdown(f"""
                <div class="citation-box">
                    <div class="citation-title">Source {i}: {c['doc_id']}</div>
                    <div style="color:#94a3b8;font-style:italic;">"{c['snippet'][:250]}..."</div>
                </div>
                """, unsafe_allow_html=True)


    user_prompt = st.text_input("Ask about courses, requirements, policies...", key="chat_text_tab")
    if st.button("Send", key="send_tab"):
        if user_prompt:
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.spinner("Searching knowledge base..."):
                resp = send_message(user_prompt, st.session_state.get("top_k_slider", 5))
                st.session_state.messages.append({"role": "assistant", "content": resp.get("answer", "No answer")})
                st.session_state.citations = resp.get("citations", [])
            st.rerun()

# === TAB 2: Study Tools – 100% WORKING, NO NESTED EXPANDERS ===
with tab2:
    st.markdown("# Study Tools")
    st.markdown("### Upload once → use any tool below")

    # === Upload ===
    uploaded = st.file_uploader(
        "Upload PDF / TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="study_upload",
        help="All tools use the same content"
    )

    if uploaded:
        with st.spinner("Reading files..."):
            for file in uploaded:
                if file.type == "application/pdf":
                    try:
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file)
                        text = "\n".join([p.extract_text() or "" for p in reader.pages if p.extract_text()])
                    except:
                        text = "[Could not read PDF]"
                else:
                    text = file.read().decode("utf-8", errors="ignore")

                if text.strip() and text not in st.session_state.study_materials:
                    st.session_state.study_materials.append(text)
                    st.success(f"Loaded: **{file.name}**")

    if not st.session_state.study_materials:
        st.info("Upload your study material to unlock all tools")
        st.stop()

    total_words = sum(len(t.split()) for t in st.session_state.study_materials)
    st.caption(f"Ready: {len(st.session_state.study_materials)} file(s) • ~{total_words:,} words")

    material_text = "\n\n".join(st.session_state.study_materials)

    # === 1. Flashcards ===
    with st.expander("Flashcards – Generate & Review", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            topic_fc = st.text_input("Topic (optional)", placeholder="e.g., Attention", key="fc_topic")
        with col2:
            count_fc = st.selectbox("Cards", [2, 4, 6, 8, 10], index=2, key="fc_count")

        if st.button("Generate Flashcards", type="primary", use_container_width=True):
            with st.spinner("Creating flashcards..."):
                r = requests.post(f"{API_BASE}/study/flashcards", json={
                    "topic": topic_fc or "key concepts",
                    "count": count_fc,
                    "context": material_text
                })
                if r.status_code == 200:
                    st.session_state.flashcards = r.json().get("flashcards", [])
                    st.success(f"{len(st.session_state.flashcards)} cards ready")

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

    # === 2. Practice Quiz (NO NESTED EXPANDERS!) ===
    with st.expander("Practice Quiz – Test Yourself", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            topic_q = st.text_input("Quiz topic (optional)", placeholder="e.g., Transformers", key="quiz_topic")
        with col2:
            num_q = st.selectbox("Questions", [2, 4, 6, 8, 10], index=0, key="quiz_num")

        if st.button("Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("Generating quiz..."):
                r = requests.post(f"{API_BASE}/study/quiz", json={
                    "topic": topic_q or "core concepts",
                    "num_questions": num_q,
                    "context": material_text
                })
                if r.status_code == 200:
                    st.session_state.quiz = r.json().get("quiz", [])
                    st.success("Quiz ready!")

        if st.session_state.get("quiz"):
            for i, q in enumerate(st.session_state.quiz):
                st.markdown(f"**Q{i+1}.** {q.get('question')}")
                for j, opt in enumerate(q.get("options", [])):
                    if j == q.get("correct_index"):
                        st.markdown(f'<div class="correct-answer">Correct: {opt}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span style="color:#94a3b8;">{opt}</span>', unsafe_allow_html=True)

                # Explanation with HTML <details> instead of st.expander
                explanation = q.get("explanation", "")
                if explanation:
                    st.markdown(f"""
                    <details style="margin:1rem 0;">
                        <summary style="color:#5eead4; cursor:pointer; font-weight:600;">Show Explanation</summary>
                        <p style="color:#cbd5e1; margin-top:0.5rem; padding-left:0.5rem;">{explanation}</p>
                    </details>
                    """, unsafe_allow_html=True)
                st.markdown("---")

    # === 3. Summary ===
    with st.expander("Summary – Key Points", expanded=False):
        if st.button("Generate Summary", type="primary", use_container_width=True):
            with st.spinner("Summarizing..."):
                r = requests.post(f"{API_BASE}/study/summary", json={"context": material_text})
                if r.status_code == 200:
                    st.markdown("### Summary")
                    st.write(r.json().get("summary", ""))
                    st.code(r.json().get("summary", ""), language=None)

    # === 4. Concept Explainer ===
    with st.expander("Concept Explainer", expanded=False):
        concept = st.text_input("What do you want explained?", placeholder="e.g., Positional Encoding", key="explain_concept")
        if st.button("Explain Concept", type="primary", use_container_width=True) and concept:
            with st.spinner("Explaining..."):
                r = requests.post(f"{API_BASE}/study/explain", json={"concept": concept, "context": material_text})
                if r.status_code == 200:
                    st.markdown(f"### {concept}")
                    st.write(r.json().get("explanation", ""))

    # === 5. Study Schedule ===
    with st.expander("Study Schedule – Personalized Plan", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            exam_date = st.date_input("Exam date", value=date.today(), min_value=date.today())
        with col2:
            hours_per_day = st.slider("Hours/day", 1, 8, 4)

        focus_topics = st.text_area("Focus topics (optional)", placeholder="e.g., Attention, RNNs", height=80)
        topic_list = [t.strip() for t in focus_topics.split(",") if t.strip()]

        if st.button("Build Study Schedule", type="primary", use_container_width=True):
            days = (exam_date - date.today()).days
            if days < 1:
                st.error("Pick a future date")
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
                        st.success(f"Plan created for {days} days!")

        if st.session_state.get("schedule"):
            st.markdown("### Your Study Schedule")
            for day in st.session_state.schedule:
                with st.container():
                    st.markdown(f"**{day.get('day')} – {day.get('focus')}**")
                    for task in day.get("tasks", []):
                        st.markdown(f"• {task}")
                    st.caption(f"{day.get('hours', hours_per_day)} hours")
                    st.markdown("---")

# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)