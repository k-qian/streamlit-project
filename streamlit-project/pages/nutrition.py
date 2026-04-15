import streamlit as st

from database import get_exercise_videos, get_music_recommendations
from ai_utils import get_nutrition_advice


def _trimester_label(week: int) -> str:
    if week <= 12:
        return "第一孕期"
    elif week <= 27:
        return "第二孕期"
    else:
        return "第三孕期"



def nutrition_page():
    st.caption("飲食管理")
    st.title("孕期營養建議")
    st.markdown("依據您的懷孕週數和體重，獲取個性化飲食建議")

    # --- 1. Input form + AI button ---
    with st.container(border=True):
        st.subheader("🍎 輸入您的資訊")

        col_label, col_week = st.columns([3, 1])
        with col_label:
            pregnancy_week = st.slider("懷孕週數", 1, 42, 20, key="nutrition_week")
        with col_week:
            st.markdown("")
            st.markdown(
                f"<h2 style='color:#1E88E5; text-align:right;'>第 {pregnancy_week} 週</h2>"
                f"<p style='color:#1E88E5; text-align:right;'>{_trimester_label(pregnancy_week)}</p>",
                unsafe_allow_html=True,
            )

        st.divider()

        col_w, col_h = st.columns(2)
        with col_w:
            st.number_input(
                "體重 (kg) 選填", min_value=30.0, max_value=200.0,
                value=None, placeholder="例：65.5", step=0.1,
                key="nutrition_weight",
            )
        with col_h:
            st.number_input(
                "身高 (cm) 選填", min_value=100.0, max_value=200.0,
                value=None, placeholder="例：165", step=0.1,
                key="nutrition_height",
            )

        if st.button("🍎 獲取營養建議", type="primary", use_container_width=True):
            weight = st.session_state.get("nutrition_weight")
            height = st.session_state.get("nutrition_height")
            with st.spinner("🤖 AI 營養建議生成中..."):
                try:
                    advice = get_nutrition_advice(pregnancy_week, weight, height)
                    st.session_state.nutrition_advice = advice
                except Exception as e:
                    st.error(f"營養建議生成失敗：{e}")

    if "nutrition_advice" in st.session_state:
        st.markdown("")
        with st.container(border=True):
            st.subheader("🤖 AI 營養建議")
            st.markdown(st.session_state.nutrition_advice)

    st.markdown("")

    # --- 3. Exercise videos from DB ---
    videos = get_exercise_videos()

    if videos:
        with st.container(border=True):
            st.subheader("🏃 運動建議")
            for i in range(0, len(videos), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(videos):
                        with col:
                            st.video(videos[idx]["url"])
                            st.caption(videos[idx]["title"])

    # --- 4. Music recommendations from DB ---
    music = get_music_recommendations()

    if music:
        st.markdown("")
        with st.container(border=True):
            st.subheader("🎵 音樂建議")
            for i in range(0, len(music), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(music):
                        with col:
                            st.video(music[idx]["url"])
                            st.caption(music[idx]["title"])

