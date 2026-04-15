import streamlit as st

from database import get_health_logs
from ai_utils import analyze_health_risk, format_logs_summary


def risk_alert_page():
    username = st.session_state.username

    st.caption("健康預警")
    st.title("AI 風險預警")
    st.markdown("基於您的健康日誌數據，AI 分析潛在健康風險")

    logs = get_health_logs(username)

    if not logs:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding: 4rem 1rem;'>"
                "<p style='font-size:3rem;'>🔍</p>"
                "<h3>尚無風險評估數據</h3>"
                "<p style='color:gray;'>請先記錄健康日誌，AI 將自動分析您的健康風險</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            col_center = st.columns([1, 2, 1])[1]
            with col_center:
                if st.button(
                    "🔍 前往記錄健康日誌", type="primary", use_container_width=True,
                ):
                    st.switch_page(st.session_state.pages["journal"])
        return

    # --- Summary cards ---
    latest = logs[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.caption("📊 分析筆數")
            st.markdown(f"**<span style='font-size:1.8rem;'>{min(len(logs), 20)}</span>**", unsafe_allow_html=True)
            st.caption(f"共 {len(logs)} 筆記錄")
    with col2:
        with st.container(border=True):
            st.caption("❤️ 最新週數")
            st.markdown(f"**<span style='font-size:1.8rem;'>第{latest['pregnancy_week']}週</span>**", unsafe_allow_html=True)
            st.caption("最近記錄")
    with col3:
        with st.container(border=True):
            st.caption("📅 最近記錄")
            st.markdown(f"**<span style='font-size:1.8rem;'>{latest['log_date']}</span>**", unsafe_allow_html=True)
            st.caption("記錄日期")

    st.markdown("")

    # --- AI analysis button ---
    if st.button("🔍 開始 AI 風險分析", type="primary", use_container_width=True):
        summary = format_logs_summary(logs)
        with st.spinner("🤖 AI 風險分析中..."):
            try:
                result = analyze_health_risk(summary, username)
                st.session_state.risk_analysis = result
            except Exception as e:
                st.error(f"風險分析失敗：{e}")

    # --- Display result ---
    if "risk_analysis" in st.session_state:
        st.markdown("")
        with st.container(border=True):
            st.subheader("🤖 AI 風險評估報告")
            st.markdown(st.session_state.risk_analysis)
