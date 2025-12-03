# import streamlit as st
# import requests
# import time
# import logging
# from typing import Dict, List

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Page configuration
# st.set_page_config(
#     page_title="SUNY Academic Guidance",
#     page_icon="🎓",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # API Configuration
# API_BASE = "http://localhost:8888"

# # Enhanced Custom CSS with Modern Dark Theme
# st.markdown("""
#     <style>
#     /* Import Google Fonts */
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
#     /* Global Styles */
#     * {
#         font-family: 'Inter', sans-serif;
#     }
    
#     /* Main Background */
#     .main {
#         background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
#     }
    
#     /* Sidebar Styling */
#     [data-testid="stSidebar"] {
#         background: linear-gradient(180deg, #1e2139 0%, #16182d 100%);
#         border-right: 1px solid rgba(94, 234, 212, 0.1);
#     }
    
#     [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
#         color: #5eead4;
#         font-weight: 700;
#         font-size: 1.5rem;
#         margin-bottom: 0.5rem;
#     }
    
#     [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
#     [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
#         color: #94a3b8;
#         font-weight: 600;
#         font-size: 0.875rem;
#         text-transform: uppercase;
#         letter-spacing: 1px;
#         margin-top: 1.5rem;
#     }
    
#     /* Status Cards */
#     .status-card {
#         background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
#         border-radius: 12px;
#         padding: 1rem;
#         margin: 0.75rem 0;
#         border: 1px solid rgba(94, 234, 212, 0.15);
#         transition: all 0.3s ease;
#     }
    
#     .status-card:hover {
#         border-color: rgba(94, 234, 212, 0.3);
#         box-shadow: 0 4px 20px rgba(94, 234, 212, 0.1);
#     }
    
#     .status-success {
#         border-left: 4px solid #10b981;
#         background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, transparent 100%);
#     }
    
#     .status-warning {
#         border-left: 4px solid #f59e0b;
#         background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, transparent 100%);
#     }
    
#     .status-error {
#         border-left: 4px solid #ef4444;
#         background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, transparent 100%);
#     }
    
#     /* Buttons */
#     .stButton>button {
#         width: 100%;
#         background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%);
#         color: #0f172a;
#         border: none;
#         border-radius: 10px;
#         padding: 0.75rem 1.5rem;
#         font-weight: 600;
#         font-size: 0.9rem;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 15px rgba(94, 234, 212, 0.3);
#     }
    
#     .stButton>button:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 6px 25px rgba(94, 234, 212, 0.4);
#         background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
#     }
    
#     /* Chat Messages */
#     .chat-message {
#         padding: 1.25rem;
#         border-radius: 16px;
#         margin-bottom: 1rem;
#         animation: fadeIn 0.3s ease;
#         backdrop-filter: blur(10px);
#     }
    
#     @keyframes fadeIn {
#         from { opacity: 0; transform: translateY(10px); }
#         to { opacity: 1; transform: translateY(0); }
#     }
    
#     .user-message {
#         background: linear-gradient(135deg, #5eead4 0%, #14b8a6 100%);
#         color: #0f172a;
#         margin-left: 15%;
#         box-shadow: 0 4px 20px rgba(94, 234, 212, 0.3);
#         border: 1px solid rgba(94, 234, 212, 0.2);
#     }
    
#     .assistant-message {
#         background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
#         color: #e2e8f0;
#         margin-right: 15%;
#         border: 1px solid rgba(94, 234, 212, 0.15);
#         box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
#     }
    
#     .system-message {
#         background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%);
#         color: #93c5fd;
#         border: 1px solid rgba(59, 130, 246, 0.3);
#         text-align: center;
#         font-size: 0.9rem;
#     }
    
#     /* Citation Box */
#     .citation-box {
#         background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
#         border-left: 4px solid #5eead4;
#         padding: 1rem;
#         margin: 0.75rem 0;
#         border-radius: 8px;
#         transition: all 0.3s ease;
#         border: 1px solid rgba(94, 234, 212, 0.2);
#     }
    
#     .citation-box:hover {
#         border-color: rgba(94, 234, 212, 0.4);
#         box-shadow: 0 4px 15px rgba(94, 234, 212, 0.15);
#     }
    
#     .citation-title {
#         color: #5eead4;
#         font-weight: 600;
#         font-size: 0.85rem;
#         margin-bottom: 0.5rem;
#     }
    
#     .citation-text {
#         color: #94a3b8;
#         font-size: 0.8rem;
#         font-style: italic;
#         line-height: 1.5;
#     }
    
#     /* Input Field */
#     .stTextInput>div>div>input {
#         background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
#         color: #e2e8f0;
#         border: 1px solid rgba(94, 234, 212, 0.2);
#         border-radius: 12px;
#         padding: 0.875rem 1.25rem;
#         font-size: 0.95rem;
#         transition: all 0.3s ease;
#     }
    
#     .stTextInput>div>div>input:focus {
#         border-color: #5eead4;
#         box-shadow: 0 0 0 3px rgba(94, 234, 212, 0.1);
#     }
    
#     .stTextInput>div>div>input::placeholder {
#         color: #64748b;
#     }
    
#     /* Slider */
#     .stSlider>div>div>div {
#         background: #5eead4;
#     }
    
#     /* Expander */
#     .streamlit-expanderHeader {
#         background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
#         border-radius: 10px;
#         color: #5eead4;
#         font-weight: 600;
#         border: 1px solid rgba(94, 234, 212, 0.2);
#     }
    
#     /* Main Title */
#     h1 {
#         color: #5eead4;
#         font-weight: 700;
#         text-align: center;
#         margin-bottom: 2rem;
#         text-shadow: 0 0 30px rgba(94, 234, 212, 0.3);
#     }
    
#     /* Help Section */
#     .help-item {
#         color: #94a3b8;
#         padding: 0.35rem 0;
#         font-size: 0.875rem;
#         line-height: 1.6;
#     }
    
#     /* Footer */
#     .footer {
#         text-align: center;
#         color: #64748b;
#         font-size: 0.85rem;
#         padding: 2rem 0;
#         border-top: 1px solid rgba(94, 234, 212, 0.1);
#         margin-top: 3rem;
#     }
    
#     .footer-highlight {
#         color: #5eead4;
#         font-weight: 600;
#     }
    
#     /* Loading Spinner */
#     .stSpinner > div {
#         border-top-color: #5eead4 !important;
#     }
    
#     /* Divider */
#     hr {
#         border-color: rgba(94, 234, 212, 0.1);
#         margin: 1.5rem 0;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'messages' not in st.session_state:           st.session_state.messages = []
# if 'initialized' not in st.session_state:        st.session_state.initialized = False
# if 'citations' not in st.session_state:          st.session_state.citations = []
# if 'auto_init_done' not in st.session_state:     st.session_state.auto_init_done = False
# if 'study_materials' not in st.session_state:    st.session_state.study_materials = []   # for Study Tools tab


# def check_vector_store_status():
#     """Check if vector store is already populated"""
#     try:
#         response = requests.get(f"{API_BASE}/academic/status", timeout=5)
#         if response.status_code == 200:
#             data = response.json()
#             return data.get('is_populated', False), data.get('count', 0)
#         return False, 0
#     except:
#         return False, 0

# def initialize_system(force_rebuild=False):
#     """Initialize the RAG system"""
#     try:
#         with st.spinner("🔄 Processing PDFs and building knowledge base..."):
#             response = requests.post(
#                 f"{API_BASE}/academic/init",
#                 json={
#                     "pdf_dir": "./backend/data/pdfs/", 
#                     "force_rebuild": force_rebuild
#                 },
#                 timeout=300
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 st.session_state.initialized = True
#                 return True, data['message'], data['count'], data.get('skipped', False)
#             else:
#                 return False, f"Error: {response.text}", 0, False
                
#     except requests.exceptions.ConnectionError:
#         return False, "Cannot connect to backend. Please ensure FastAPI is running on port 8888.", 0, False
#     except Exception as e:
#         return False, f"Error: {str(e)}", 0, False

# def send_message(question: str, top_k: int = 5) -> Dict:
#     try:
#         r = requests.post(f"{API_BASE}/academic/chat", json={"question": question, "top_k": top_k}, timeout=120)
#         if r.status_code == 200:
#             return r.json()
#         else:
#             return {"answer": f"Error: {r.text}", "citations": []}
#     except Exception as e:
#         return {"answer": f"Error: {str(e)}", "citations": []}

# def check_health():
#     try:
#         return requests.get(f"{API_BASE}/academic/health", timeout=5).status_code == 200
#     except:
#         return False

# # Sidebar
# with st.sidebar:
#     st.markdown("# 🎓 SUNY Academic Guidance")
#     st.markdown("<small style='color: #64748b;'>AI-Powered Academic Assistant</small>", unsafe_allow_html=True)
#     st.markdown("---")
    
#     # Status Section
#     st.markdown("### 📊 System Status")
    
#     backend_healthy = check_health()
    
#     if backend_healthy:
#         st.markdown("""
#         <div class="status-card status-success">
#             <div style="display: flex; align-items: center; gap: 0.5rem;">
#                 <span style="font-size: 1.2rem;">✅</span>
#                 <div>
#                     <div style="color: #10b981; font-weight: 600; font-size: 0.9rem;">Backend Connected</div>
#                     <div style="color: #6ee7b7; font-size: 0.75rem;">All systems operational</div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.markdown("""
#         <div class="status-card status-error">
#             <div style="display: flex; align-items: center; gap: 0.5rem;">
#                 <span style="font-size: 1.2rem;">❌</span>
#                 <div>
#                     <div style="color: #ef4444; font-weight: 600; font-size: 0.9rem;">Backend Offline</div>
#                     <div style="color: #fca5a5; font-size: 0.75rem;">Start backend to continue</div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     if st.session_state.initialized:
#         st.markdown("""
#         <div class="status-card status-success">
#             <div style="display: flex; align-items: center; gap: 0.5rem;">
#                 <span style="font-size: 1.2rem;">📚</span>
#                 <div>
#                     <div style="color: #10b981; font-weight: 600; font-size: 0.9rem;">Documents Loaded</div>
#                     <div style="color: #6ee7b7; font-size: 0.75rem;">Knowledge base ready</div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.markdown("""
#         <div class="status-card status-warning">
#             <div style="display: flex; align-items: center; gap: 0.5rem;">
#                 <span style="font-size: 1.2rem;">⏳</span>
#                 <div>
#                     <div style="color: #f59e0b; font-weight: 600; font-size: 0.9rem;">Not Initialized</div>
#                     <div style="color: #fbbf24; font-size: 0.75rem;">Click button below</div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # Initialization Button
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         init_button = st.button("🔄 Initialize System")
#     with col2:
#         force_rebuild = st.checkbox("Force", help="Force rebuild even if data exists")
    
#     if init_button:
#         success, message, count, skipped = initialize_system(force_rebuild)
#         if success:
#             if skipped:
#                 st.info(f"ℹ️ {message}")
#             else:
#                 st.success(f"✅ {message}")
#                 if count > 0:
#                     st.info(f"📊 Processed {count} document chunks")
#             time.sleep(1.5)
#             st.rerun()
#         else:
#             st.error(message)
    
#     st.markdown("---")
    
#     # Settings
#     st.markdown("### ⚙️ Settings")
#     top_k = st.slider("Documents to retrieve", 1, 10, 5, help="Number of relevant document chunks to use for answering")
    
#     st.markdown("---")
    
#     # Help Section
#     st.markdown("### 💡 What can I help with?")
#     st.markdown("""
#     <div class="help-item">📚 Course selection & planning</div>
#     <div class="help-item">🎯 Prerequisites & requirements</div>
#     <div class="help-item">🎓 Graduation requirements</div>
#     <div class="help-item">📖 Major/minor information</div>
#     <div class="help-item">🗓️ Academic planning & policies</div>
#     """, unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # Clear Chat
#     if st.button("🗑️ Clear Chat History"):
#         st.session_state.messages = []
#         st.session_state.citations = []
#         st.rerun()

# # Main content
# st.markdown("# 💬 Academic Guidance Chat")

# # Auto-initialize on first load (check if vector store exists first)
# if not st.session_state.auto_init_done and backend_healthy:
#     st.session_state.auto_init_done = True
    
#     # First check if vector store already has data
#     is_populated, doc_count = check_vector_store_status()
    
#     if is_populated:
#         # Vector store already exists, just mark as initialized
#         st.session_state.initialized = True
#         logger.info(f"Vector store already populated with {doc_count} documents. Skipping auto-init.")
#     else:
#         # Vector store is empty, need to initialize
#         with st.spinner("🚀 First-time setup: Processing PDFs..."):
#             success, message, count, skipped = initialize_system(force_rebuild=False)
#             if success:
#                 st.success(f"✅ System initialized! Processed {count} document chunks.")
#                 time.sleep(2)
#                 st.rerun()

# # Display chat messages
# for message in st.session_state.messages:
#     if message["role"] == "user":
#         st.markdown(f"""
#         <div class="chat-message user-message">
#             <strong style="font-size: 0.85rem; opacity: 0.8;">You</strong><br>
#             <div style="margin-top: 0.5rem; font-size: 0.95rem; line-height: 1.6;">{message["content"]}</div>
#         </div>
#         """, unsafe_allow_html=True)
#     elif message["role"] == "system":
#         st.markdown(f"""
#         <div class="chat-message system-message">
#             {message["content"]}
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.markdown(f"""
#         <div class="chat-message assistant-message">
#             <strong style="font-size: 0.85rem; color: #5eead4;">🤖 AI Assistant</strong><br>
#             <div style="margin-top: 0.5rem; font-size: 0.95rem; line-height: 1.7;">{message["content"]}</div>
#         </div>
#         """, unsafe_allow_html=True)

# # Display citations if available
# if st.session_state.citations:
#     with st.expander("📚 View Source Citations", expanded=False):
#         for i, citation in enumerate(st.session_state.citations, 1):
#             st.markdown(f"""
#             <div class="citation-box">
#                 <div class="citation-title">📄 Source {i}: {citation['doc_id']}</div>
#                 <div class="citation-text">"{citation['snippet']}"</div>
#             </div>
#             """, unsafe_allow_html=True)

# # Chat input
# if st.session_state.initialized:
#     user_input = st.chat_input("Ask about courses, requirements, or academic planning...")
    
#     if user_input:
#         # Add user message
#         st.session_state.messages.append({"role": "user", "content": user_input})
        
#         # Get response
#         with st.spinner("🤔 Analyzing documents and generating response..."):
#             response = send_message(user_input, top_k)
            
#             # Add assistant message
#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": response['answer']
#             })
            
#             # Store citations
#             st.session_state.citations = response.get('citations', [])
        
#         st.rerun()
# else:
#     st.info("👈 Please initialize the system using the sidebar button to start chatting.")

# # Footer
# st.markdown("""
# <div class="footer">
#     <p><span class="footer-highlight">SUNY Academic Guidance System</span> | Powered by RAG & Gemini 2.5 Flash</p>
#     <p style="margin-top: 0.5rem;">⚠️ Always verify important academic decisions with your academic advisor</p>
# </div>
# """, unsafe_allow_html=True)


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
    if not populated:
        with st.spinner("First-time setup..."):
            success, msg, count, _ = initialize_system(False)
            if success:
                st.success(f"Initialized! {count} chunks")
                time.sleep(2)
                st.rerun()

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
                with st.spinner("Generating..."):
                    r = requests.post(f"{API_BASE}/study/quiz", json={"topic": topic_q or "key concepts", "num_questions": 6, "context": material_text})
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

# === FIXED CHAT INPUT — NOW OUTSIDE TABS (Fixed to bottom) ===
if st.session_state.initialized:
    # This is the ONLY valid place for st.chat_input
    prompt = st.chat_input("Ask about courses, requirements, policies...", key="main_chat_input")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Searching knowledge base..."):
            resp = send_message(prompt, st.session_state.get("top_k_slider", 5))
            st.session_state.messages.append({"role": "assistant", "content": resp.get("answer", "No answer")})
            st.session_state.citations = resp.get("citations", [])
        st.rerun()
else:
    st.info("Please initialize the system in the sidebar to start chatting.")

# === Footer ===
st.markdown("""<div class="footer">
    <p><span class="footer-highlight">SUNY Academic Assistant</span> | RAG + Study Tools</p>
    <p>Always double-check with your advisor for official info</p>
</div>""", unsafe_allow_html=True)