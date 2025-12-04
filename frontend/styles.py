"""
Unified Design System for SUNY Academic Assistant
Color Palette:
- Primary: #0A1E44 (Deep Academic Navy)
- Secondary: #1D4ED8 (Royal Blue)
- Accent: #3B82F6 (Sky Blue)
- Success: #22C55E (Green)
- Warning: #FACC15 (Yellow)
- Danger: #EF4444 (Red)
- Background: #F8FAFC (Subtle grey-white)
"""

def get_main_styles():
    """Returns the main CSS styling for the application"""
    return """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* === Global Reset & Typography === */
    * {
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    
    /* === Main Background === */
    .main {
        background: #F8FAFC !important;
    }
    
    .block-container {
        padding: 2rem 3rem;
        max-width: 100%;
    }
    
    /* === Sidebar Gradient === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A1E44 0%, #1D4ED8 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    [data-testid="stSidebar"] * {
        color: #E5E7EB !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    /* === Headers === */
    h1 {
        color: #0A1E44 !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    h2 {
        color: #1D4ED8 !important;
        font-weight: 600 !important;
        font-size: 2rem !important;
        margin-top: 2rem !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    h3 {
        color: #1E3A8A !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    h4 {
        color: #1E3A8A !important;
        font-weight: 500 !important;
        font-size: 1.25rem !important;
    }
    
    /* === Buttons === */
    .stButton>button {
        background: linear-gradient(135deg, #0A1E44 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 12px rgba(10, 30, 68, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(10, 30, 68, 0.25) !important;
    }
    
    .stButton>button:active {
        transform: translateY(0) !important;
    }
    
    /* === Cards & Containers === */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    
    /* === Chat Messages === */
    .chat-message {
        padding: 1.25rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: #FFFFFF;
        margin-left: 15%;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
    }
    
    .assistant-message {
        background: #FFFFFF;
        color: #1E293B;
        margin-right: 15%;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    /* === Citation Box === */
    .citation-box {
        background: #FFFFFF;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }
    
    .citation-title {
        color: #1D4ED8;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* === Escalation Notice === */
    .escalation-notice {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(29, 78, 216, 0.1) 100%);
        border: 2px solid #3B82F6;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
        }
        50% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
        }
    }
    
    /* === Tabs === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #94A3B8;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #3B82F6 !important;
        border-bottom: 3px solid #3B82F6 !important;
        font-weight: 600;
    }
    
    /* === Input Fields === */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        color: #1E293B !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* === Select Boxes === */
    .stSelectbox>div>div {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
    }
    
    /* === Metrics === */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748B;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    [data-testid="stMetricValue"] {
        color: #0A1E44;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* === Gradient Metric Cards === */
    .metric-card-gradient {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
        color: #FFFFFF;
        transition: all 0.3s ease;
    }
    
    .metric-card-gradient:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
    }
    
    .metric-card-gradient-warning {
        background: linear-gradient(135deg, #FACC15 0%, #F59E0B 100%);
        box-shadow: 0 4px 16px rgba(250, 204, 21, 0.3);
    }
    
    .metric-card-gradient-success {
        background: linear-gradient(135deg, #22C55E 0%, #10B981 100%);
        box-shadow: 0 4px 16px rgba(34, 197, 94, 0.3);
    }
    
    .metric-card-gradient-danger {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
    }
    
    .metric-card-gradient-info {
        background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.3);
    }
    
    /* === Upload Area === */
    .upload-area {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 2px dashed #3B82F6;
        border-radius: 16px;
        padding: 3rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-area:hover {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-color: #1D4ED8;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
    }
    
    /* === Document Card === */
    .document-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    
    .document-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border-color: #3B82F6;
    }
    
    .document-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    .document-icon-pdf {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    }
    
    .document-icon-txt {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
    }
    
    /* === Processing Status === */
    .processing-modal {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        max-width: 500px;
        margin: 2rem auto;
    }
    
    .processing-step {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background: #F8FAFC;
    }
    
    .processing-step-active {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
        border-left: 4px solid #3B82F6;
    }
    
    .processing-step-complete {
        background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%);
        border-left: 4px solid #22C55E;
    }
    
    /* === Version Badge === */
    .version-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .version-badge-active {
        background: linear-gradient(135deg, #22C55E 0%, #10B981 100%);
        color: #FFFFFF;
    }
    
    .version-badge-old {
        background: #F1F5F9;
        color: #64748B;
    }
    
    /* === Expander === */
    .streamlit-expanderHeader {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
        color: #1E293B;
    }
    
    .streamlit-expanderHeader:hover {
        background: #F8FAFC;
        border-color: #3B82F6;
    }
    
    /* === Spinner === */
    .stSpinner > div {
        border-top-color: #3B82F6 !important;
    }
    
    /* === Footer === */
    .footer {
        text-align: center;
        color: #64748B;
        font-size: 0.85rem;
        padding: 2rem 0;
        border-top: 1px solid #E5E7EB;
        margin-top: 3rem;
    }
    
    .footer-highlight {
        color: #1D4ED8;
        font-weight: 600;
    }
    
    /* === Dashboard Specific === */
    .dashboard-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 1rem;
    }
    
    .dashboard-card h3 {
        margin-top: 0;
        color: #1D4ED8;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .stat-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    
    .badge-success {
        background: #DCFCE7;
        color: #166534;
    }
    
    .badge-warning {
        background: #FEF3C7;
        color: #92400E;
    }
    
    .badge-danger {
        background: #FEE2E2;
        color: #991B1B;
    }
    
    .badge-info {
        background: #DBEAFE;
        color: #1E40AF;
    }
    
    /* === Charts === */
    .plotly-chart {
        background: #FFFFFF !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    
    /* === Admin Mode Banner === */
    .admin-banner {
        background: linear-gradient(135deg, #0A1E44 0%, #1D4ED8 100%);
        color: #FFFFFF;
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(10, 30, 68, 0.2);
    }
    
    /* === Risk Level Indicators === */
    .risk-low {
        color: #22C55E;
        font-weight: 600;
    }
    
    .risk-medium {
        color: #FACC15;
        font-weight: 600;
    }
    
    .risk-high {
        color: #EF4444;
        font-weight: 600;
    }
    
    .risk-critical {
        color: #DC2626;
        font-weight: 700;
    }
    
    /* === Data Table Styling === */
    .dataframe {
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background: #F8FAFC !important;
        color: #1E293B !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border-bottom: 2px solid #E5E7EB !important;
    }
    
    .dataframe td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid #F1F5F9 !important;
    }
    
    /* === Progress Bars === */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3B82F6 0%, #1D4ED8 100%);
    }
</style>
"""

