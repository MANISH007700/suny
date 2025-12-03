
import streamlit as st
import requests
import time
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
    
    /* Global Font & Background */
    * {font-family: 'Inter', sans-serif !important;}
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e2139 0%, #16182d 100%);
        border-right: 1px solid rgba(94, 234, 212, 0.1);
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #5eead4 !important;
        font-weight: 700 !important;
    }
    
    /* Buttons - Primary */
    .stButton > button {
        background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(94, 234, 212, 0.3) !important;
        transition: all 0.3s ease !important;
        height: 3.2em !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(94, 234, 212, 0.4) !important;
    }
    .stButton > button[kind="primary"] {
        height: 3.6em !important;
        font-size: 1.05rem !important;
    }
    
    /* Chat Messages */
    .chat-message {
        padding: 1.25rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        animation: fadeIn 0.4s ease;
        backdrop-filter: blur(10px);
    }
    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }
    .user-message {
        background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%);
        color: #0f172a;
        margin-left: 15%;
        box-shadow: 0 4px 20px rgba(94, 234, 212, 0.3);
        border-radius: 16px 16px 4px 16px;
    }
    .assistant-message {
        background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
        color: #e2e8f0;
        margin-right: 15%;
        border: 1px solid rgba(94, 234, 212, 0.15);
        border-radius: 16px 16px 16px 4px;
    }
    
    /* Citations */
    .citation-box {
        background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
        border-left: 4px solid #5eead4;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 8px;
        border: 1px solid rgba(94, 234, 212, 0.2);
    }
    .citation-title {color: #5eead4; font-weight: 600;}
    
    /* Spinner */
    .stSpinner > div {border-top-color: #5eead4 !important;}
    
    /* Beautiful Expanders (Flashcards & Quiz) */
    div[data-testid="stExpander"] details {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(94, 234, 212, 0.25) !important;
        margin: 1rem 0 !important;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"] details:hover {
        border-color: #5eead4 !important;
        box-shadow: 0 0 25px rgba(94, 234, 212, 0.25);
        transform: translateY(-2px);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #5eead4 !important;
        padding: 1.1rem !important;
        cursor: pointer;
        font-size: 1.1rem !important;
        border-radius: 16px;
    }
    
    /* Quiz: Correct Answer (Green Glow) */
    .correct-answer {
        color: #10b981 !important;
        font-weight: 700 !important;
        background: rgba(16, 185, 129, 0.15) !important;
        padding: 0.6rem 1rem !important;
        border-radius: 12px !important;
        border-left: 5px solid #10b981 !important;
        margin: 0.5rem 0 !important;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% {box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);}
        70% {box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);}
        100% {box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);}
    }
    
    /* Wrong Answer (Subtle) */
    .wrong-answer {
        color: #94a3b8 !important;
        opacity: 0.7;
        text-decoration: line-through;
        font-style: italic;
    }
    
    /* Layout Spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 8rem !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        padding: 3rem 0 1rem;
        border-top: 1px solid rgba(94, 234, 212, 0.1);
        margin-top: 5rem;
    }
    .footer-highlight {
        color: #5eead4;
        font-weight: 600;
    }
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
# === TAB 2: Study Tools (PREMIUM VERSION) ===
# === TAB 2: Study Tools (FINAL CLEAN VERSION) ===
with tab2:
    st.markdown("# Study Tools")
    st.markdown("### Upload notes, syllabus, or readings → generate smart study aids")

    uploaded = st.file_uploader(
        "Upload PDF/TXT",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="study_upload",
        help="Max 200MB per file • Multiple files supported"
    )

    if uploaded:
        with st.spinner("Extracting text from uploaded files..."):
            for file in uploaded:
                if file.type == "application/pdf":
                    try:
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file)
                        text = "\n".join([p.extract_text() or "" for p in reader.pages if p.extract_text()])
                    except:
                        text = "[Error reading this PDF]"
                else:
                    text = file.read().decode("utf-8", errors="ignore")

                if text.strip():
                    st.session_state.study_materials.append(text)
                    st.success(f"Uploaded: **{file.name}** — {len(text.split()):,} words")

    if not st.session_state.study_materials:
        st.info("Upload your study material to unlock flashcards, quizzes, and summaries")
        st.stop()

    material_text = "\n\n".join(st.session_state.study_materials)

    col1, col2 = st.columns(2)

    # === Flashcards ===
    with col1:
        st.markdown("#### Flashcards")
        topic_fc = st.text_input("Topic (optional)", placeholder="e.g., Multi-Head Attention", key="fc_topic", label_visibility="collapsed")
        if st.button("Generate Flashcards", type="primary", use_container_width=True, key="gen_fc"):
            with st.spinner("Generating high-quality flashcards..."):
                r = requests.post(f"{API_BASE}/study/flashcards", json={
                    "topic": topic_fc or "key concepts",
                    "count": 10,
                    "context": material_text
                })
                if r.status_code == 200:
                    st.session_state.flashcards = r.json().get("flashcards", [])
                    st.success("Flashcards ready!")
                else:
                    st.error("Failed to generate flashcards")

        if st.session_state.get("flashcards"):
            for i, card in enumerate(st.session_state.flashcards):
                q = card.get("question", "")
                a = card.get("answer", "")
                with st.expander(f"**Card {i+1}:** {q[:80]}{'...' if len(q)>80 else ''}", expanded=False):
                    st.markdown(f"**Q:** {q}")
                    st.markdown(f"**A:** {a}")

    # === Quiz ===
    with col2:
        st.markdown("#### Practice Quiz")
        topic_q = st.text_input("Quiz topic (optional)", placeholder="e.g., Self-Attention", key="quiz_topic", label_visibility="collapsed")
        if st.button("Generate Quiz", type="primary", use_container_width=True, key="gen_quiz"):
            with st.spinner("Creating challenging quiz questions..."):
                r = requests.post(f"{API_BASE}/study/quiz", json={
                    "topic": topic_q or "core concepts",
                    "num_questions": 8,
                    "context": material_text
                })
                if r.status_code == 200:
                    st.session_state.quiz = r.json().get("quiz", [])
                    st.success("Quiz ready!")
                else:
                    st.error("Failed to generate quiz")

        if st.session_state.get("quiz"):
            for i, q in enumerate(st.session_state.quiz):
                question = q.get("question", "")
                options = q.get("options", [])
                correct_idx = q.get("correct_index", -1)
                explanation = q.get("explanation", "")

                st.markdown(f"**Q{i+1}:** {question}")

                for j, opt in enumerate(options):
                    if j == correct_idx:
                        st.markdown(f'<div class="correct-answer">Correct: {opt}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span style="color:#94a3b8; opacity:0.8;">{opt}</span>', unsafe_allow_html=True)

                if explanation:
                    with st.expander("Show Explanation", expanded=False):
                        st.caption(explanation)
                st.markdown("---")

    # === Quick Actions: Only Summary ===
    st.markdown("#### Quick Actions")
    col_a, col_b = st.columns([1, 3])  # Only one button
    with col_a:
        if st.button("Summarize Material", type="secondary", use_container_width=True):
            with st.spinner("Generating concise summary..."):
                r = requests.post(f"{API_BASE}/study/summary", json={"context": material_text})
                if r.status_code == 200:
                    summary = r.json().get("summary", "")
                    st.markdown("### Summary")
                    st.write(summary)
                    with st.expander("Copy Summary"):
                        st.code(summary, language=None)

# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)