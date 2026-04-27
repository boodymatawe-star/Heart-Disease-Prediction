import streamlit as st
from database import init_db, verify_user, create_user

# Must be the very first Streamlit call
st.set_page_config(
    page_title="CardioPredict",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database on startup
init_db()

# ── Shared CSS (applies to all pages via the browser session) ──────────────────
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%);
    }
    [data-testid="stSidebar"] * { color: #f0f0f0 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.18);
        color: white !important;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.18);
    }

    /* ── Stat cards ── */
    .stat-card {
        border-radius: 16px;
        padding: 22px 16px;
        color: white;
        text-align: center;
        margin-bottom: 6px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    .stat-card h2  { font-size: 2.4rem; margin: 0; font-weight: 700; }
    .stat-card p   { margin: 4px 0 0 0; opacity: 0.9; font-size: 0.95rem; }
    .card-blue  { background: linear-gradient(135deg, #667eea, #764ba2); }
    .card-green { background: linear-gradient(135deg, #43e97b, #38f9d7); color: #1a1a1a !important; }
    .card-red   { background: linear-gradient(135deg, #f093fb, #f5576c); }
    .card-cyan  { background: linear-gradient(135deg, #4facfe, #00f2fe); color: #1a1a1a !important; }
    .card-green p, .card-cyan p { color: #1a1a1a !important; }

    /* ── Result banners ── */
    .result-positive {
        background: linear-gradient(135deg, #f5576c, #f093fb);
        color: white; border-radius: 12px;
        padding: 20px; text-align: center; margin: 10px 0;
    }
    .result-negative {
        background: linear-gradient(135deg, #43e97b, #38f9d7);
        color: #1a1a1a; border-radius: 12px;
        padding: 20px; text-align: center; margin: 10px 0;
    }
    .result-positive h2, .result-negative h2 { margin: 0; }

    /* ── Patient card ── */
    .patient-header {
        background: white;
        border-left: 5px solid #667eea;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def _show_login() -> None:
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center;color:#e63946;'>❤️ CardioPredict</h1>"
            "<p style='text-align:center;color:#666;font-size:1.1rem;'>"
            "Heart Disease Risk Assessment System</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐  Login", "📝  Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button(
                    "Login", use_container_width=True, type="primary"
                )
                if submitted:
                    user = verify_user(username.strip(), password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            st.caption("Default credentials: **admin** / **admin123**")

        with tab_register:
            with st.form("register_form", clear_on_submit=True):
                r_name = st.text_input("Full Name *")
                r_user = st.text_input("Username *")
                r_email = st.text_input("Email (optional)")
                r_spec = st.selectbox(
                    "Specialization",
                    ["Cardiology", "General Medicine", "Internal Medicine",
                     "Emergency Medicine", "Other"],
                )
                r_pw  = st.text_input("Password *", type="password")
                r_pw2 = st.text_input("Confirm Password *", type="password")
                reg = st.form_submit_button("Create Account", use_container_width=True)
                if reg:
                    if not r_name or not r_user or not r_pw:
                        st.error("Name, username, and password are required.")
                    elif r_pw != r_pw2:
                        st.error("Passwords do not match.")
                    elif len(r_pw) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        ok, msg = create_user(r_user.strip(), r_pw, r_name, r_email, r_spec)
                        if ok:
                            st.success(msg + " Please switch to the Login tab.")
                        else:
                            st.error(msg)


# ── Gate: show login if not authenticated ─────────────────────────────────────
if not _is_logged_in():
    _show_login()
    st.stop()


# ── Sidebar user info + logout ────────────────────────────────────────────────
user = st.session_state.user
with st.sidebar:
    st.markdown(
        f"<div style='padding:8px 0'>"
        f"<h3 style='margin:0'>👨‍⚕️ Dr. {user['full_name']}</h3>"
        f"<small>🏥 {user.get('specialization', 'General')}</small>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("🚪  Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ── Multi-page navigation ─────────────────────────────────────────────────────
dashboard = st.Page("pages/dashboard.py",  title="Dashboard",       icon="🏠", default=True)
predict   = st.Page("pages/predict.py",    title="New Prediction",  icon="🔬")
patients  = st.Page("pages/patients.py",   title="Patients",        icon="👥")
history   = st.Page("pages/history.py",    title="Prediction History", icon="📋")
analytics = st.Page("pages/analytics.py",  title="Analytics",       icon="📊")

pg = st.navigation(
    {"Main": [dashboard], "Clinical": [predict, patients, history], "Insights": [analytics]}
)
pg.run()
