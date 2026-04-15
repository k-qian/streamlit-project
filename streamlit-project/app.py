import streamlit as st

from database import (
    seed_default_user,
    verify_user,
    create_user,
    create_session,
    validate_session,
    delete_session,
)
from pages.overview import overview_page
from pages.health_journal import health_journal_page
from pages.data_dashboard import data_dashboard_page
from pages.nutrition import nutrition_page
from pages.risk_alert import risk_alert_page
from pages.health_report import health_report_page
from pages.notifications import notifications_page
from pages.childcare_center import childcare_center_page
from pages.admin.data_manage import data_manage_page

st.set_page_config(page_title="媽媽健康日誌", page_icon="🤰", layout="wide")

# Ensure default admin user exists
seed_default_user()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.session_token = ""

# Cookie helpers — st.html() runs in main DOM (no iframe race condition)
def set_session_cookie(token: str):
    """Set session cookie and reload page via JavaScript."""
    st.html(
        f"<script>document.cookie='session_token={token}; path=/; max-age={30*86400}; SameSite=Strict'; window.location.reload();</script>",
        unsafe_allow_javascript=True,
    )


def clear_session_cookie():
    """Remove session cookie and reload page via JavaScript."""
    st.html(
        "<script>document.cookie='session_token=; path=/; max-age=0'; window.location.reload();</script>",
        unsafe_allow_javascript=True,
    )


# Auto-login from cookie (fresh value available after F5 via new WebSocket)
if not st.session_state.logged_in:
    token = st.context.cookies.get("session_token")
    if token:
        username = validate_session(token)
        if username:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.session_token = token


def login_page():
    st.title("登入")

    tab_login, tab_register = st.tabs(["登入", "註冊"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入", use_container_width=True)
            if submitted:
                if verify_user(username, password):
                    token = create_session(username)
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.session_token = token
                    set_session_cookie(token)
                    st.stop()
                else:
                    st.error("帳號或密碼錯誤。")

    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("設定帳號")
            new_pass = st.text_input("設定密碼", type="password")
            confirm_pass = st.text_input("確認密碼", type="password")
            registered = st.form_submit_button(
                "建立帳號", use_container_width=True
            )
            if registered:
                if not new_user or not new_pass:
                    st.error("請輸入帳號及密碼。")
                elif new_pass != confirm_pass:
                    st.error("兩次輸入的密碼不一致。")
                elif len(new_pass) < 6:
                    st.error("密碼長度至少需要 6 個字元。")
                elif create_user(new_user, new_pass):
                    st.success("帳號建立成功！請切換至登入頁面。")
                else:
                    st.error("此帳號已被使用。")


def logout():
    delete_session(st.session_state.session_token)
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.session_token = ""
    clear_session_cookie()
    st.stop()


# Conditional navigation based on auth state
if st.session_state.logged_in:
    pages = {
        "overview": st.Page(overview_page, title="總覽", icon=":material/dashboard:", default=True, url_path="overview"),
        "journal": st.Page(health_journal_page, title="健康日誌", icon=":material/favorite:", url_path="journal"),
        "data": st.Page(data_dashboard_page, title="數據儀錶板", icon=":material/monitoring:", url_path="data"),
        "nutrition": st.Page(nutrition_page, title="營養建議", icon=":material/restaurant:", url_path="nutrition"),
        "risk": st.Page(risk_alert_page, title="AI 風險預警", icon=":material/warning:", url_path="risk"),
        "report": st.Page(health_report_page, title="健康報告", icon=":material/description:", url_path="report"),
        "notifications": st.Page(notifications_page, title="通知中心", icon=":material/notifications:", url_path="notifications"),
        "childcare": st.Page(childcare_center_page, title="托嬰中心查找", icon=":material/child_care:", url_path="childcare"),
        "logout": st.Page(logout, title="登出", icon=":material/logout:", url_path="logout"),
    }
    if st.session_state.username == "admin":
        pages["admin"] = st.Page(data_manage_page, title="資料管理", icon=":material/admin_panel_settings:", url_path="admin")
    st.session_state.pages = pages
    pg = st.navigation(list(pages.values()))
else:
    pg = st.navigation([st.Page(login_page, title="登入", icon=":material/login:")])

pg.run()
