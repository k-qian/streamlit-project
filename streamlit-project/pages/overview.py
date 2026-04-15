import json

import streamlit as st

from database import (
    get_health_log_count,
    get_health_logs,
    get_latest_health_log,
    get_unread_notification_count,
)


def overview_page():
    username = st.session_state.username

    # Header
    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.caption("歡迎回來")
        st.title(f"{username} 👋")
        st.markdown("開始記錄您的孕期健康旅程")
    with col_btn:
        if st.button("＋ 記錄今日", type="primary"):
            st.switch_page(st.session_state.pages["journal"])

    st.markdown("")

    # Metric cards
    latest_log = get_latest_health_log(username)
    log_count = get_health_log_count(username)
    unread_count = get_unread_notification_count(username)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.caption("❤️ 目前週數")
            if latest_log:
                st.markdown(f"### 第 {latest_log['pregnancy_week']} 週")
            else:
                st.markdown("### —")
                st.caption("尚無記錄")
    with c2:
        with st.container(border=True):
            st.caption("📈 最新體重")
            if latest_log and latest_log["weight"]:
                st.markdown(f"### {latest_log['weight']} kg")
            else:
                st.markdown("### —")
                st.caption("最近一次記錄")
    with c3:
        with st.container(border=True):
            st.caption("📋 健康日誌")
            st.markdown(f"### {log_count} 筆")
            st.caption("累積記錄")
    with c4:
        with st.container(border=True):
            st.caption("⚠️ 未讀通知")
            st.markdown(f"### {unread_count} 則")
            st.caption("一切正常" if unread_count == 0 else "")

    st.markdown("")

    # Quick actions
    st.subheader("快速操作")
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        with st.container(border=True):
            if st.button("➕\n\n記錄今日健康", use_container_width=True):
                st.switch_page(st.session_state.pages["journal"])
    with a2:
        with st.container(border=True):
            if st.button("📊\n\n查看數據圖表", use_container_width=True):
                st.switch_page(st.session_state.pages["data"])
    with a3:
        with st.container(border=True):
            if st.button("🍎\n\n營養飲食建議", use_container_width=True):
                st.switch_page(st.session_state.pages["nutrition"])
    with a4:
        with st.container(border=True):
            if st.button("⚠️\n\nAI 風險預警", use_container_width=True):
                st.switch_page(st.session_state.pages["risk"])
    with a5:
        with st.container(border=True):
            if st.button("📄\n\n生成健康報告", use_container_width=True):
                st.switch_page(st.session_state.pages["report"])

    st.markdown("")

    # Recent logs or empty state
    if log_count == 0:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding: 3rem 1rem;'>"
                "<p style='font-size:3rem;'>💙</p>"
                "<h3>開始您的健康旅程</h3>"
                "<p style='color:gray;'>記錄第一筆健康日誌，讓 AI 為您提供個性化的孕期建議</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            col_center = st.columns([1, 2, 1])[1]
            with col_center:
                if st.button(
                    "＋ 記錄今日健康", type="primary", use_container_width=True, key="cta"
                ):
                    st.switch_page(st.session_state.pages["journal"])
    else:
        st.subheader("📋 近期健康日誌")
        recent_logs = get_health_logs(username, limit=5)
        for log in recent_logs:
            with st.container(border=True):
                col_date, col_week, col_weight, col_hr = st.columns([2, 1, 1, 1])
                with col_date:
                    st.markdown(f"**{log['log_date']}**")
                with col_week:
                    st.caption("週數")
                    st.markdown(f"第 {log['pregnancy_week']} 週")
                with col_weight:
                    st.caption("體重")
                    st.markdown(f"{log['weight']} kg" if log["weight"] else "—")
                with col_hr:
                    st.caption("心率")
                    st.markdown(f"{log['heart_rate']} bpm" if log["heart_rate"] else "—")

                details = []
                if log["mood"]:
                    details.append(f"心情：{log['mood']}")
                if log["sleep_quality"]:
                    details.append(f"睡眠：{log['sleep_quality']}")
                if log["exercise"]:
                    details.append(f"運動：{log['exercise']}")
                if log["symptoms"]:
                    try:
                        syms = json.loads(log["symptoms"])
                        if syms:
                            details.append(f"症狀：{'、'.join(syms)}")
                    except json.JSONDecodeError:
                        pass
                if details:
                    st.caption(" ｜ ".join(details))
