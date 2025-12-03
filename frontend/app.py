
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

# === TAB 2: Study Tools (from Code 1) ===
with tab2:
    st.markdown("# Study Tools")
    st.markdown("### Upload notes, syllabus, or readings → generate study aids")

    uploaded = st.file_uploader("Upload PDF/TXT", type=["pdf", "txt"], accept_multiple_files=True, key="study_upload")
    print(uploaded)
    if uploaded:
        with st.spinner("Extracting text..."):
            for file in uploaded:
                if file.type == "application/pdf":
                    try:
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file)
                        text = "\n".join([p.extract_text() or "" for p in reader.pages])
                    except:
                        text = "[PDF read error]"
                else:
                    text = file.read().decode("utf-8", errors="ignore")
                st.session_state.study_materials.append(text)
                st.success(f"Uploaded: {file.name}")

    material_text = "\n\n".join(st.session_state.study_materials)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Flashcards")
        topic_fc = st.text_input("Topic (optional)", placeholder="e.g., Mitosis", key="fc_topic")
        if st.button("Generate Flashcards", type="primary", key="gen_fc"):
            if not material_text.strip():
                st.warning("Upload material first")
            else:
                with st.spinner("Generating..."):
                    r = requests.post(f"{API_BASE}/study/flashcards", json={"topic": topic_fc or "key concepts", "count": 8, "context": material_text})
                    if r.status_code == 200:
                        for i, card in enumerate(r.json().get("flashcards", [])):
                            with st.expander(f"Card {i+1}: {card.get('question','')[:60]}..."):
                                st.write("**Q:**", card.get("question"))
                                st.write("**A:**", card.get("answer"))

    with col2:
        st.markdown("#### Practice Quiz")
        topic_q = st.text_input("Quiz topic (optional)", placeholder="e.g., Cell Division", key="quiz_topic")
        if st.button("Generate Quiz", type="primary", key="gen_quiz"):
            if not material_text.strip():
                st.warning("Upload material first")
            else:
                with st.spinner("Generating..."):
                    r = requests.post(
                        f"{API_BASE}/study/quiz",
                        json={"topic": topic_q or "key concepts", "num_questions": 6, "context": material_text}
                    )
                    if r.status_code == 200:
                        for i, q in enumerate(r.json().get("quiz", [])):
                            with st.expander(f"Q{i+1}: {q.get('question','')[:80]}..."):
                                for j, opt in enumerate(q.get("options", [])):
                                    mark = "Correct" if j == q.get("correct_index") else ""
                                    st.markdown(f"**{chr(65+j)}. {opt}** {mark}")
                                if q.get("explanation"):
                                    st.caption(q["explanation"])

    st.markdown("#### Quick Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Summarize Material"):
            if material_text.strip():
                with st.spinner("Summarizing..."):
                    r = requests.post(f"{API_BASE}/study/summary", json={"context": material_text})
                    if r.status_code == 200:
                        st.info(r.json().get("summary", ""))
    with c2:
        concept = st.text_input("Explain concept", placeholder="e.g., Quantum Entanglement", key="explain_input")
        if st.button("Explain", key="explain_btn") and concept and material_text.strip():
            with st.spinner("Explaining..."):
                r = requests.post(f"{API_BASE}/study/explain", json={"concept": concept, "context": material_text})
                if r.status_code == 200:
                    st.write(r.json().get("explanation", ""))


# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)