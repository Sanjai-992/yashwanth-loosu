import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import streamlit.components.v1 as components

from database.db_helper import (
    init_db,
    seed_default_data,
    get_all_employees,
    get_employee_by_id,
    mark_attendance,
    end_attendance_period,
    get_all_tasks,
    get_absent_employees_with_tasks,
    find_best_replacement,
    confirm_task_reassignment,
    mark_email_sent,
    get_reassignments_history,
    get_cycle_info,
    reset_24h_cycle,
    get_dashboard_metrics
)
from services.email_service import send_reassignment_email, send_test_email
from services.ollama_service import OllamaService
from services.chatbot_service import query_workforce_x

# Page Configuration
st.set_page_config(
    page_title="WORKFORCE-X | Smart Workforce Attendance & Task Reassignment",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End Dashboard Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main {
        background: #f8fafc;
    }

    /* Executive Header */
    .dashboard-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #312e81 100%);
        border-radius: 18px;
        padding: 24px 28px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(10px);
        padding: 4px 12px;
        border-radius: 9999px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #93c5fd;
        margin-bottom: 8px;
    }

    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
        border-color: #cbd5e1;
    }
    .metric-val {
        font-size: 30px;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
        margin: 6px 0 2px 0;
    }
    .metric-lbl {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* 24-Hr Cycle Card */
    .cycle-card {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        padding: 12px 16px;
        color: #ffffff;
    }

    /* RFID Keyboard Panel */
    .rfid-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 22px;
    }
    .listener-active-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.04em;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        background: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulseGreen 1.8s infinite;
    }
    @keyframes pulseGreen {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Tactile Buttons */
    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05) !important;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(15, 23, 42, 0.1) !important;
        border-color: #94a3b8 !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 9px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.02em;
    }
    .pill-present { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .pill-absent { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .pill-waiting { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }

    /* Employee Card */
    .emp-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .emp-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
        border-color: #cbd5e1;
    }

    /* Smart Replacement Card */
    .smart-analysis-card {
        background: #ffffff;
        border: 1px solid #bfdbfe;
        border-top: 4px solid #2563eb;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.08);
        margin-bottom: 24px;
    }
    .analysis-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 18px;
    }
    .analysis-cell {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
    }
    .analysis-cell-title {
        font-size: 11px;
        font-weight: 800;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }

    /* Workflow Pipeline Stepper */
    .workflow-stepper {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 14px 18px;
        gap: 8px;
    }
    .step-pill {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BROWSER KEYBOARD RFID LISTENER COMPONENT
# -----------------------------------------------------------------------------
COMPONENT_PATH = Path(__file__).resolve().parent / "components" / "keyboard_listener"
if not COMPONENT_PATH.exists():
    COMPONENT_PATH.mkdir(parents=True, exist_ok=True)

_rfid_listener = components.declare_component("rfid_keyboard_listener", path=str(COMPONENT_PATH))

# Initialize database schema
init_db()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_rfid_event" not in st.session_state:
    st.session_state.last_rfid_event = None
if "last_processed_ts" not in st.session_state:
    st.session_state.last_processed_ts = 0
if "selected_model" not in st.session_state:
    st.session_state.selected_model = os.getenv("OLLAMA_MODEL", "gemma2:latest")
if "email_provider" not in st.session_state:
    st.session_state.email_provider = os.getenv("EMAIL_PROVIDER", "resend")

# Mount custom keyboard listener component (runs invisibly in browser background)
rfid_event = _rfid_listener(key="rfid_hardware_component")
if rfid_event and isinstance(rfid_event, dict):
    pressed_key = rfid_event.get("key")
    event_ts = rfid_event.get("timestamp", 0)
    
    # Process event if it's a new timestamp
    if pressed_key and event_ts > st.session_state.last_processed_ts:
        st.session_state.last_processed_ts = event_ts
        att_res = mark_attendance(pressed_key)
        if att_res:
            st.session_state.last_rfid_event = {
                "key": pressed_key,
                "name": att_res["name"],
                "role": att_res["role"],
                "status": "PRESENT",
                "time": att_res["time"]
            }
            st.rerun()

def get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

# Sidebar - Settings & Credentials
with st.sidebar:
    st.markdown("### 🤖 Ollama AI Model Switcher")
    st.caption("Dynamic local inference model selection for workforce analysis.")
    
    # Check Ollama status & installed models
    ollama_status = OllamaService.get_status(st.session_state.selected_model)
    ollama_online = ollama_status.get("connected", False)
    installed_models = ollama_status.get("available_models", [])

    if ollama_online:
        st.markdown(
            '<div style="display:flex; align-items:center; gap:6px; background:#ecfdf5; border:1px solid #a7f3d0; padding:6px 12px; border-radius:8px; font-size:12px; color:#047857; font-weight:700; margin-bottom:10px;">'
            '<span class="pulse-dot"></span> Ollama Online (localhost:11434)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background:#fef2f2; border:1px solid #fecaca; padding:6px 12px; border-radius:8px; font-size:12px; color:#b91c1c; font-weight:700; margin-bottom:10px;">'
            '⚠️ Ollama Offline (Fallback Engine Active)</div>',
            unsafe_allow_html=True
        )

    # Preset common models + installed models
    popular_presets = [
        "gemma2:latest",
        "qwen2.5:latest",
        "qwen2.5:7b",
        "qwen2.5-coder:1.5b",
        "llama3:latest",
        "llama3.2:latest",
        "mistral:latest",
        "deepseek-r1:latest"
    ]
    all_options = list(dict.fromkeys(installed_models + popular_presets)) + ["Custom Model..."]

    # Current index
    current_idx = 0
    if st.session_state.selected_model in all_options:
        current_idx = all_options.index(st.session_state.selected_model)
    elif st.session_state.selected_model:
        current_idx = len(all_options) - 1  # Custom Model

    picked_model = st.selectbox("Active Inference Model", options=all_options, index=current_idx)

    if picked_model == "Custom Model...":
        custom_input = st.text_input(
            "Enter Model Name / Tag",
            value=st.session_state.selected_model if st.session_state.selected_model not in all_options[:-1] else "qwen2.5:latest",
            help="E.g. qwen2.5:3b, llama3.1:8b, codellama, etc."
        )
        active_model = custom_input.strip()
    else:
        active_model = picked_model

    st.session_state.selected_model = active_model

    # Model status badge
    is_model_installed = any(
        active_model in m or m.startswith(active_model.split(":")[0]) 
        for m in installed_models
    )
    if is_model_installed:
        st.markdown(
            f'<div style="font-size:11px; color:#059669; font-weight:700; margin-top:2px;">✓ Model <code>{active_model}</code> installed locally</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="font-size:11px; color:#d97706; font-weight:700; margin-top:2px;">⬇️ Not installed locally. Pull with:</div>'
            f'<div style="background:#1e293b; color:#38bdf8; font-family:monospace; font-size:11px; padding:4px 8px; border-radius:6px; margin-top:4px;">ollama pull {active_model}</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # -------------------------------------------------------------------------
    # Resend & Email Notification System
    # -------------------------------------------------------------------------
    st.markdown("### ✉️ Email Dispatch System")
    st.caption("Resend API & SMTP task reallocation notifications.")

    provider_choice = st.selectbox(
        "Email Provider",
        options=["Resend API (Recommended)", "Gmail SMTP", "Simulation Mode"],
        index=0 if st.session_state.email_provider == "resend" else (1 if st.session_state.email_provider == "smtp" else 2)
    )

    if "Resend" in provider_choice:
        st.session_state.email_provider = "resend"
        resend_api_key = st.text_input(
            "Resend API Key",
            type="password",
            value=os.getenv("RESEND_API_KEY", get_secret("RESEND_API_KEY", "")),
            help="Generate a free API key at https://resend.com (starts with 're_')"
        )
        resend_from_email = st.text_input(
            "From Sender Address",
            value=os.getenv("RESEND_FROM_EMAIL", get_secret("RESEND_FROM_EMAIL", "WORKFORCE-X Operations <onboarding@resend.dev>")),
            help="Default sandbox sender is 'onboarding@resend.dev'"
        )
        recipient_email = st.text_input(
            "Operations Recipient Email",
            value=os.getenv("GMAIL_RECIPIENT", get_secret("GMAIL_RECIPIENT", "delivered@resend.dev")),
            help="With onboarding@resend.dev, Resend permits delivery to your registered Resend account email."
        )

        st.info("💡 **Resend Sandbox Note:** When using `onboarding@resend.dev`, deliver to your own Resend account email. To deliver anywhere, verify your domain at [resend.com](https://resend.com).")

        sender_email = None
        app_password = None

        if st.button("🧪 Send Test Email via Resend", use_container_width=True):
            if not resend_api_key:
                st.warning("⚠️ Please provide a Resend API key first.")
            else:
                with st.spinner("Dispatching test email via Resend..."):
                    test_res = send_test_email(
                        provider="resend",
                        resend_api_key=resend_api_key,
                        resend_from_email=resend_from_email,
                        to_email=recipient_email
                    )
                    if test_res["success"]:
                        st.success(f"✓ {test_res['message']}")
                    else:
                        st.error(f"❌ {test_res['message']}")

    elif "Gmail" in provider_choice:
        st.session_state.email_provider = "smtp"
        resend_api_key = None
        resend_from_email = None
        sender_email = st.text_input(
            "Sender Dispatch Address", 
            value=os.getenv("GMAIL_SENDER", get_secret("GMAIL_SENDER", "workforce.x.dispatch@gmail.com"))
        )
        app_password = st.text_input(
            "SMTP Authentication Token", 
            type="password",
            value=os.getenv("GMAIL_APP_PASSWORD", get_secret("GMAIL_APP_PASSWORD", ""))
        )
        recipient_email = st.text_input(
            "Operations Recipient Email", 
            value=os.getenv("GMAIL_RECIPIENT", get_secret("GMAIL_RECIPIENT", "manager@enterprise.com"))
        )

        if st.button("🧪 Send Test Email via Gmail SMTP", use_container_width=True):
            if not sender_email or not app_password:
                st.warning("⚠️ Please enter both Sender Email and Gmail App Password.")
            else:
                with st.spinner("Dispatching test email via Gmail SMTP..."):
                    test_res = send_test_email(
                        provider="smtp",
                        sender_email=sender_email,
                        app_password=app_password,
                        to_email=recipient_email
                    )
                    if test_res["success"]:
                        st.success("✓ Test email sent successfully via Gmail SMTP!")
                    else:
                        st.error(f"❌ {test_res['message']}")

    else:
        st.session_state.email_provider = "simulation"
        resend_api_key = None
        resend_from_email = None
        sender_email = None
        app_password = None
        recipient_email = st.text_input(
            "Simulated Recipient Email",
            value="operations@enterprise.internal"
        )
        st.info("Simulation Mode: Reassignment emails will be formatted and logged locally without sending external web requests.")

    st.divider()
    if st.button("↺ Reset All Records to Initial State", use_container_width=True):
        seed_default_data()
        st.session_state.messages = []
        st.session_state.last_rfid_event = None
        st.success("Database restored to initial demo state!")
        st.rerun()

# -----------------------------------------------------------------------------
# 1. HEADER & 24-HOUR ATTENDANCE PERIOD
# -----------------------------------------------------------------------------
cycle_info = get_cycle_info()

st.markdown(f"""
<div class="dashboard-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <div class="header-badge">
                <span style="display:inline-block; width:6px; height:6px; background:#38bdf8; border-radius:50%;"></span>
                Enterprise Operations Engine
            </div>
            <h1 style="font-size: 26px; font-weight: 800; color: #ffffff; margin: 0;">⚡ WORKFORCE-X Attendance &amp; Task Reassignment</h1>
            <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">RFID-Style Keyboard Hardware Simulation &bull; Dynamic Absent-Gap Analysis &bull; Workload-Balanced Task Reallocation</div>
        </div>
        <div class="cycle-card">
            <div style="font-size: 11px; font-weight: 800; color: #38bdf8; letter-spacing: 0.06em; text-transform: uppercase;">
                24-Hour Cycle Window
            </div>
            <div style="font-size: 12px; color: #cbd5e1; margin-top: 2px;">
                Start: <b>{cycle_info['start_time']}</b> &bull; End: <b>{cycle_info['end_time']}</b>
            </div>
            <div style="font-size: 15px; font-weight: 800; color: #ffffff; margin-top: 2px;">
                ⏱️ Remaining: {cycle_info['time_remaining']}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. TOP DASHBOARD SUMMARY METRICS
# -----------------------------------------------------------------------------
metrics = get_dashboard_metrics()
waiting_count = metrics["total"] - metrics["present"] - metrics["absent"]
m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">TOTAL EMPLOYEES</div><div class="metric-val">{metrics["total"]}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl" style="color:#059669;">PRESENT</div><div class="metric-val" style="color:#059669;">{metrics["present"]}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl" style="color:#dc2626;">ABSENT</div><div class="metric-val" style="color:#dc2626;">{metrics["absent"]}</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl" style="color:#d97706;">PENDING</div><div class="metric-val" style="color:#d97706;">{waiting_count}</div></div>', unsafe_allow_html=True)
with m5:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl" style="color:#2563eb;">TASKS REASSIGNED</div><div class="metric-val" style="color:#2563eb;">{metrics["reassigned"]}</div></div>', unsafe_allow_html=True)
with m6:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl" style="color:#7c3aed;">UTILIZATION</div><div class="metric-val" style="color:#7c3aed;">{metrics["utilization"]}%</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. VISUAL KEYBOARD RFID PANEL
# -----------------------------------------------------------------------------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
    <div>
        <h3 style="margin:0; font-size:18px; font-weight:800; color:#0f172a;">⌨️ RFID Keyboard Verification Station</h3>
        <p style="margin:0; font-size:12px; color:#64748b;">Press physical keys <b>A-I</b> on your keyboard or tap below to simulate RFID badge taps.</p>
    </div>
    <div class="listener-active-pill">
        <span class="pulse-dot"></span> RFID KEYBOARD LISTENER &bull; ACTIVE
    </div>
</div>
""", unsafe_allow_html=True)

# Display Last RFID Event if exists
if st.session_state.last_rfid_event:
    ev = st.session_state.last_rfid_event
    st.success(f"✓ **Last RFID Event**: Key `[{ev['key']}]` &bull; Employee: **{ev['name']}** ({ev.get('role', 'Staff')}) &bull; Status: **{ev['status']}** &bull; Attendance Time: **{ev['time']}**")

# 2-Row RFID Keypad
row1_keys = [("A", "Arjun"), ("B", "Priya"), ("C", "Karthik"), ("D", "Divya"), ("E", "Rahul")]
row2_keys = [("F", "Sneha"), ("G", "Vikram"), ("H", "Ananya"), ("I", "Sanjay")]

row1_cols = st.columns(5)
for idx, (k, name) in enumerate(row1_keys):
    with row1_cols[idx]:
        if st.button(f"┌────┐\n│ {k} │\n│{name}│\n└────┘", key=f"rfid_btn_{k}", use_container_width=True):
            res = mark_attendance(k)
            if res:
                st.session_state.last_rfid_event = {
                    "key": k,
                    "name": res["name"],
                    "role": res["role"],
                    "status": "PRESENT",
                    "time": res["time"]
                }
                st.rerun()

row2_cols = st.columns([1, 1, 1, 1, 1])
for idx, (k, name) in enumerate(row2_keys):
    with row2_cols[idx]:
        if st.button(f"┌────┐\n│ {k} │\n│{name}│\n└────┘", key=f"rfid_btn_{k}", use_container_width=True):
            res = mark_attendance(k)
            if res:
                st.session_state.last_rfid_event = {
                    "key": k,
                    "name": res["name"],
                    "role": res["role"],
                    "status": "PRESENT",
                    "time": res["time"]
                }
                st.rerun()

with row2_cols[4]:
    if st.button("⏱️ Finalize Period\n(Mark Absent)", type="primary", use_container_width=True):
        end_attendance_period()
        st.warning("Attendance finalized! Unverified staff marked ABSENT.")
        st.rerun()

st.info("💡 **Hackathon Demo Step**: Press **A, C, D, E, G, H, I** on your physical keyboard. Leave **B (Priya)** and **F (Sneha)** unpressed, then click **Finalize Period**.")

st.divider()

# -----------------------------------------------------------------------------
# 4. PERSONNEL STATUS MATRIX
# -----------------------------------------------------------------------------
st.markdown("### 👥 Personnel Status Matrix (9 Registered Members)")
st.caption("Live allocation status, assigned operational tasks, roles, and current workload metrics.")

all_employees = get_all_employees()
cols = st.columns(3)

for idx, emp in enumerate(all_employees):
    with cols[idx % 3]:
        att_status = emp["attendance_status"]
        if att_status == "PRESENT":
            badge_html = f'<span class="status-pill pill-present">🟢 PRESENT</span>'
            time_display = f"<div style='font-size:11px; color:#059669; font-weight:600; margin-top:2px;'>Logged: {emp['attendance_time'] or 'Verified'}</div>"
        elif att_status == "ABSENT":
            badge_html = '<span class="status-pill pill-absent">🔴 ABSENT</span>'
            time_display = "<div style='font-size:11px; color:#dc2626; font-weight:600; margin-top:2px;'>Unverified (Marked Absent)</div>"
        else:
            badge_html = '<span class="status-pill pill-waiting">⏳ WAITING</span>'
            time_display = "<div style='font-size:11px; color:#d97706; font-weight:600; margin-top:2px;'>Awaiting Badge Check-in</div>"

        st.markdown(f"""
        <div class="emp-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div>
                    <span style="font-size:16px; font-weight:800; color:#0f172a;">{emp['name']}</span>
                    <span style="font-size:12px; color:#64748b; font-family:'JetBrains Mono',monospace;"> [ID: {emp['id']} | RFID Key: {emp['rfid_key']}]</span>
                </div>
                <div>{badge_html}</div>
            </div>
            {time_display}
            <div style="font-size:12px; color:#334155; margin-top:6px;"><b>Role:</b> {emp.get('role', 'Engineer')}</div>
            <div style="font-size:12px; color:#334155; margin-top:2px;"><b>Skill:</b> <span style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-weight:600;">{emp['skill']}</span></div>
            <div style="font-size:12px; color:#334155; margin-top:2px;"><b>Assigned Task:</b> <span style="color:#2563eb; font-weight:700;">{emp['current_task'] or 'None'}</span></div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; margin-top:8px;">
                <span style="color:#64748b; font-weight:600;">Workload:</span>
                <span style="font-weight:800; color:#0f172a;">{emp['workload']}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(emp['workload'] / 100.0)

st.divider()

# -----------------------------------------------------------------------------
# 5. AUTOMATED REALLOCATION WORKFLOW PIPELINE
# -----------------------------------------------------------------------------
st.markdown("### ⚡ Automated Task Reallocation Pipeline")
st.markdown("""
<div class="workflow-stepper">
    <div class="step-pill">1. RFID / Keypad Check-in</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill">2. 24-Hr Cycle Filter</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill" style="background:#fef2f2; border-color:#fecaca; color:#b91c1c;">3. Absent Detection</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill">4. Identify Halted Task</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill">5. Match Required Skill</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill">6. Filter Present Staff</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill">7. Compare Workload</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill" style="background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8;">8. Smart Recommendation</div>
    <span style="color:#94a3b8; font-weight:bold;">➔</span>
    <div class="step-pill" style="background:#ecfdf5; border-color:#a7f3d0; color:#047857;">9. Confirm &amp; Gmail Alert</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. ABSENT TASK GAP DETECTION & SMART REPLACEMENT ANALYSIS
# -----------------------------------------------------------------------------
st.markdown("### 🔄 Smart Replacement Analysis")

absent_with_tasks = get_absent_employees_with_tasks()

if not absent_with_tasks:
    st.info("✅ All operational positions and tasks are actively manned. No halted workflows detected.")
else:
    for item in absent_with_tasks:
        absent_id = item["absent_id"]
        absent_name = item["absent_name"]
        absent_role = item.get("absent_role", "Database Engineer")
        absent_workload = item.get("absent_workload", 80)
        absent_skill = item.get("absent_skill", "Database")
        task_id = item["task_id"]
        task_name = item["task_name"]
        req_skill = item["required_skill"]

        replacement_data = find_best_replacement(req_skill, absent_id)

        if replacement_data and replacement_data.get("candidate"):
            best = replacement_data["candidate"]
            candidates_list = replacement_data.get("all_candidates", [])
            rep_id = best["id"]
            rep_name = best["name"]
            rep_role = best.get("role", "Database Engineer")
            rep_skill = best["skill"]
            rep_workload = best["workload"]
            rep_score = best["score"]

            st.markdown(f"""
            <div class="smart-analysis-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <span style="font-size:14px; font-weight:800; color:#2563eb; letter-spacing:0.06em; text-transform:uppercase;">
                        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>
                        SMART TASK REPLACEMENT
                    </span>
                    <span class="status-pill pill-absent">HALTED TASK DETECTED</span>
                </div>
                
                <div class="analysis-grid">
                    <div class="analysis-cell">
                        <div class="analysis-cell-title">🔴 Absent Employee</div>
                        <div style="font-size:16px; font-weight:800; color:#dc2626;">{absent_name} (ID: {absent_id})</div>
                        <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Role:</b> {absent_role}</div>
                        <div style="font-size:12px; color:#475569;"><b>Skill:</b> {absent_skill}</div>
                        <div style="font-size:12px; color:#475569;"><b>Workload:</b> {absent_workload}%</div>
                        <div style="font-size:12px; color:#dc2626; font-weight:700;">Status: ABSENT</div>
                    </div>
                    
                    <div class="analysis-cell">
                        <div class="analysis-cell-title">⚠️ Halted Task</div>
                        <div style="font-size:16px; font-weight:800; color:#0f172a;">{task_name}</div>
                        <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Required Skill:</b> {req_skill}</div>
                        <div style="font-size:12px; color:#475569;"><b>Required Role:</b> {absent_role}</div>
                        <div style="font-size:12px; color:#b91c1c; font-weight:700;">Task Status: HALTED</div>
                    </div>
                    
                    <div class="analysis-cell" style="background:#f0fdf4; border-color:#bbf7d0;">
                        <div class="analysis-cell-title" style="color:#047857;">🟢 Recommended Replacement</div>
                        <div style="font-size:16px; font-weight:800; color:#059669;">{rep_name} (ID: {rep_id})</div>
                        <div style="font-size:12px; color:#334155; margin-top:4px;"><b>Role:</b> {rep_role}</div>
                        <div style="font-size:12px; color:#334155;"><b>Skill:</b> {rep_skill}</div>
                        <div style="font-size:12px; color:#334155;"><b>Current Workload:</b> {rep_workload}%</div>
                        <div style="font-size:12px; color:#059669; font-weight:700;">Status: PRESENT</div>
                    </div>
                </div>

                <div style="background:#eff6ff; border-left:4px solid #2563eb; padding:12px 16px; border-radius:8px; margin-bottom:16px;">
                    <div style="font-weight:800; font-size:13px; color:#1e40af; margin-bottom:6px;">WHY WAS {rep_name.upper()} SELECTED?</div>
                    <div style="font-size:12px; color:#1e3a8a; line-height:1.6;">
                        ✓ <b>Same required skill</b> ({req_skill})<br>
                        ✓ <b>Currently present</b> (Logged in today's cycle)<br>
                        ✓ <b>Available bandwidth</b> ({rep_workload}% workload is lowest among qualified present staff)<br>
                        ✓ <b>Role compatibility verified</b> ({best['role_match']} match - {best['role_reason']})<br>
                        ✓ <b>Highest composite suitability score</b> ({rep_score}/100)
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # 8. ABSENT vs REPLACEMENT COMPARISON TABLE
            # -----------------------------------------------------------------
            st.markdown(f"#### 📊 Role & Resource Comparison: {absent_name} vs {rep_name}")
            
            comp_table = [
                {"DETAIL": "Employee ID", "ABSENT EMPLOYEE": absent_id, "REPLACEMENT EMPLOYEE": rep_id},
                {"DETAIL": "Name", "ABSENT EMPLOYEE": absent_name, "REPLACEMENT EMPLOYEE": rep_name},
                {"DETAIL": "Role", "ABSENT EMPLOYEE": absent_role, "REPLACEMENT EMPLOYEE": rep_role},
                {"DETAIL": "Skill", "ABSENT EMPLOYEE": absent_skill, "REPLACEMENT EMPLOYEE": rep_skill},
                {"DETAIL": "Attendance", "ABSENT EMPLOYEE": "ABSENT", "REPLACEMENT EMPLOYEE": "PRESENT"},
                {"DETAIL": "Workload", "ABSENT EMPLOYEE": f"{absent_workload}%", "REPLACEMENT EMPLOYEE": f"{rep_workload}%"},
                {"DETAIL": "Availability", "ABSENT EMPLOYEE": "Unavailable", "REPLACEMENT EMPLOYEE": "Available (YES)"},
                {"DETAIL": "Assigned Task", "ABSENT EMPLOYEE": task_name, "REPLACEMENT EMPLOYEE": task_name},
                {"DETAIL": "Replacement Reason", "ABSENT EMPLOYEE": "Absent (Unverified)", "REPLACEMENT EMPLOYEE": "Same skill + lower workload + present"},
                {"DETAIL": "Role Match", "ABSENT EMPLOYEE": "N/A", "REPLACEMENT EMPLOYEE": f"{best['role_match']} ({best['role_reason']})"}
            ]
            st.table(comp_table)

            # -----------------------------------------------------------------
            # 9. REPLACEMENT RANKING LIST
            # -----------------------------------------------------------------
            st.markdown("#### 🏆 Eligible Replacement Rankings (Calculated Decision Matrix)")
            rank_cols = st.columns(min(3, len(candidates_list)))
            for r_idx, c in enumerate(candidates_list[:3]):
                with rank_cols[r_idx]:
                    is_top = (r_idx == 0)
                    card_border = "#2563eb" if is_top else "#e2e8f0"
                    card_bg = "#f0fdf4" if is_top else "#ffffff"
                    st.markdown(f"""
                    <div style="background:{card_bg}; border:2px solid {card_border}; border-radius:12px; padding:14px; margin-bottom:12px;">
                        <div style="font-size:14px; font-weight:800; color:{'#059669' if is_top else '#0f172a'};">
                            #{r_idx+1}. {c['name']} (ID: {c['id']}) {'⭐ SELECTED' if is_top else ''}
                        </div>
                        <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Skill Match:</b> {c['skill_match']} ({c['skill']})</div>
                        <div style="font-size:12px; color:#475569;"><b>Workload:</b> {c['workload']}%</div>
                        <div style="font-size:12px; color:#475569;"><b>Availability:</b> {c['availability']}</div>
                        <div style="font-size:12px; color:#475569;"><b>Role Match:</b> {c['role_match']}</div>
                        <div style="font-size:14px; font-weight:800; color:#2563eb; margin-top:6px;">Score: {c['score']}/100</div>
                    </div>
                    """, unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # 10. REASSIGNMENT CONFIRMATION BUTTON
            # -----------------------------------------------------------------
            if st.button(f"✓ CONFIRM TASK REASSIGNMENT: {task_name} ➔ {rep_name}", key=f"confirm_btn_{task_id}", type="primary", use_container_width=True):
                # 1. Update task in SQLite & record reassignment
                reassign_reason = f"Employee {absent_id} was absent. Employee {rep_id} matched the required skill and had lower workload."
                reassign_id = confirm_task_reassignment(task_id, absent_id, rep_id, reassign_reason)
                
                # 2. Dispatch task reallocation notification
                email_result = send_reassignment_email(
                    target_recipient=recipient_email,
                    absent_employee_id=absent_id,
                    halted_task=task_name,
                    replacement_id=rep_id,
                    reason=reassign_reason,
                    provider=st.session_state.email_provider,
                    resend_api_key=resend_api_key if 'resend_api_key' in locals() else None,
                    resend_from_email=resend_from_email if 'resend_from_email' in locals() else None,
                    sender_email=sender_email if 'sender_email' in locals() else None,
                    app_password=app_password if 'app_password' in locals() else None
                )

                if email_result.get("success"):
                    mark_email_sent(reassign_id)
                    prov_title = email_result.get("provider", "Resend").title()
                    msg_id_info = f" (ID: {email_result.get('message_id')})" if email_result.get('message_id') else ""
                    st.success(f"""
                    ✓ **Replacement confirmed & recorded**
                    
                    • **Task**: {task_name}  
                    • **Previous Employee**: {absent_name} ({absent_id})  
                    • **New Assigned Specialist**: {rep_name} ({rep_id})  
                    • **Reason**: {reassign_reason}  
                    
                    ✉️ **Dispatch Status**: Notification successfully delivered via **{prov_title}**{msg_id_info}!
                    """)
                else:
                    st.success(f"""
                    ✓ **Replacement confirmed & recorded**
                    
                    • **Task**: {task_name}  
                    • **Previous Employee**: {absent_name} ({absent_id})  
                    • **New Assigned Specialist**: {rep_name} ({rep_id})  
                    • **Reason**: {reassign_reason}
                    """)
                    st.warning(f"⚠️ Task reassigned, but email dispatch failed: {email_result.get('message', 'Check email configuration.')}")

                st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 7. REASSIGNMENT HISTORY TABLE
# -----------------------------------------------------------------------------
reassignments = get_reassignments_history()
if reassignments:
    st.markdown("### 📋 Reassignment Log & Audit Records")
    reassign_table = [
        {
            "ID": r["id"],
            "Task": r["task_name"],
            "Absent Employee": f"{r['absent_name']} ({r['absent_employee_id']})",
            "Replacement Employee": f"{r['replacement_name']} ({r['replacement_employee_id']})",
            "Timestamp": r["timestamp"],
            "Reason": r["reason"],
            "Email Dispatch": "Delivered ✓" if r["email_sent"] else "Simulated / Pending"
        }
        for r in reassignments
    ]
    st.dataframe(reassign_table, use_container_width=True)
    st.divider()

# -----------------------------------------------------------------------------
# 8. WORKFORCE-X EXECUTIVE MANAGER ASSISTANT CHATBOT
# -----------------------------------------------------------------------------
st.markdown("### 🤖 WORKFORCE-X Executive Manager Assistant")
st.caption(f"AI-Powered Digital Twin Assistant &bull; Active Engine: **Ollama ({st.session_state.selected_model})** &bull; Real-time Operational Telemetry")

# Quick Query Suggestions
q1, q2, q3, q4 = st.columns(4)
user_prompt_suggestion = None

with q1:
    if st.button("❓ Who is absent?", use_container_width=True):
        user_prompt_suggestion = "Who is absent today and what tasks are affected?"
with q2:
    if st.button("⚡ Lowest Workload?", use_container_width=True):
        user_prompt_suggestion = "Which present employee has the lowest workload?"
with q3:
    if st.button("🔍 Why was Vikram selected?", use_container_width=True):
        user_prompt_suggestion = "Why was Vikram selected to replace Priya for the Database Module task?"
with q4:
    if st.button("📊 Show Workforce Status", use_container_width=True):
        user_prompt_suggestion = "Show today's overall workforce status and task allocations."

# Conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
chat_input = st.chat_input("Ask WORKFORCE-X about workforce allocation, replacement decisions, workload, or attendance...")
prompt_to_send = user_prompt_suggestion or chat_input

if prompt_to_send:
    # Append user prompt
    st.session_state.messages.append({"role": "user", "content": prompt_to_send})
    with st.chat_message("user"):
        st.markdown(prompt_to_send)

    # Query Ollama engine
    with st.chat_message("assistant"):
        with st.spinner(f"WORKFORCE-X analyzing real-time digital twin with {st.session_state.selected_model}..."):
            response_text = query_workforce_x(
                user_message=prompt_to_send,
                chat_history=st.session_state.messages,
                model_name=st.session_state.selected_model
            )
            st.markdown(response_text)

    # Append response
    st.session_state.messages.append({"role": "assistant", "content": response_text})
