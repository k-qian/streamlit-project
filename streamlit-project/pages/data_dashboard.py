import json

import pandas as pd
import streamlit as st

from database import get_health_logs


def data_dashboard_page():
    username = st.session_state.username

    st.caption("數據分析")
    st.title("數據儀錶板")

    logs = get_health_logs(username)

    if not logs:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding: 4rem 1rem;'>"
                "<p style='font-size:3rem;'>📈</p>"
                "<h3>尚無數據</h3>"
                "<p style='color:gray;'>請先記錄健康日誌，數據圖表將在此顯示</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        return

    # Build dataframe
    data = []
    for log in logs:
        symptoms = []
        if log["symptoms"]:
            try:
                symptoms = json.loads(log["symptoms"])
            except json.JSONDecodeError:
                pass
        data.append({
            "日期": log["log_date"],
            "週數": log["pregnancy_week"],
            "體重": log["weight"],
            "心率": log["heart_rate"],
            "心情": log["mood"],
            "睡眠": log["sleep_quality"],
            "症狀數": len(symptoms),
        })

    df = pd.DataFrame(data)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")

    st.markdown(f"共 {len(df)} 筆記錄的健康趨勢分析")

    # --- Metric cards ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.caption("📊 記錄筆數")
            st.markdown(f"**<span style='font-size:1.8rem;'>{len(df)}</span>**", unsafe_allow_html=True)
            st.caption("健康日誌")

    with col2:
        with st.container(border=True):
            st.caption("❤️ 最高週數")
            max_week = df["週數"].max()
            st.markdown(f"**<span style='font-size:1.8rem;'>第{max_week}週</span>**", unsafe_allow_html=True)
            st.caption("目前進度")

    with col3:
        with st.container(border=True):
            st.caption("📈 平均體重")
            avg_weight = df["體重"].mean()
            if pd.notna(avg_weight):
                st.markdown(f"**<span style='font-size:1.8rem;'>{avg_weight:.1f}kg</span>**", unsafe_allow_html=True)
            else:
                st.markdown(f"**<span style='font-size:1.8rem;'>—</span>**", unsafe_allow_html=True)
            st.caption("所有記錄")

    with col4:
        with st.container(border=True):
            st.caption("💓 平均心律")
            avg_hr = df["心率"].mean()
            if pd.notna(avg_hr):
                st.markdown(f"**<span style='font-size:1.8rem;'>{avg_hr:.0f}bpm</span>**", unsafe_allow_html=True)
            else:
                st.markdown(f"**<span style='font-size:1.8rem;'>—</span>**", unsafe_allow_html=True)
            st.caption("所有記錄")

    st.markdown("")

    # --- Mood distribution ---
    mood_data = df["心情"].dropna()
    if not mood_data.empty:
        with st.container(border=True):
            st.subheader("心情分佈")
            mood_counts = mood_data.value_counts()
            st.bar_chart(mood_counts)

    st.markdown("")

    # --- Trend charts side by side ---
    col_left, col_right = st.columns(2)

    with col_left:
        if df["體重"].notna().any():
            with st.container(border=True):
                st.subheader("體重趨勢")
                st.line_chart(df.set_index("日期")["體重"])

    with col_right:
        if df["心率"].notna().any():
            with st.container(border=True):
                st.subheader("心率趨勢")
                st.line_chart(df.set_index("日期")["心率"])
