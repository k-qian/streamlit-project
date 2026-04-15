import json

import streamlit as st

from database import save_health_log, get_health_logs, update_health_log_ai_advice
from ai_utils import analyze_emotion


SYMPTOMS = [
    "噁心嘔吐", "頭痛", "背痛", "腳腫", "疲勞",
    "胃灼熱", "便秘", "頻尿", "腹痛", "胸悶",
    "頭暈", "水腫", "抽筋", "失眠", "其他",
]


def _trimester_label(week: int) -> str:
    if week <= 12:
        return "第一孕期"
    elif week <= 27:
        return "第二孕期"
    else:
        return "第三孕期"


def health_journal_page():
    username = st.session_state.username

    st.caption("今日記錄")
    st.title("健康日誌")
    st.markdown("記錄您的孕期生理數據，獲取 AI 個性化建議")

    with st.container(border=True):
        st.subheader("❤️ 生理數據輸入")

        # Slider outside form for real-time updates
        col_label, col_week = st.columns([3, 1])
        with col_label:
            pregnancy_week = st.slider("懷孕週數", 1, 42, 20, key="pregnancy_week")
        with col_week:
            st.markdown("")
            st.markdown(
                f"<h2 style='color:#1E88E5; text-align:right;'>第 {pregnancy_week} 週</h2>"
                f"<p style='color:#1E88E5; text-align:right;'>{_trimester_label(pregnancy_week)}</p>",
                unsafe_allow_html=True,
            )

        st.divider()

        with st.form("health_form"):
            # Weight / Height
            col_w, col_h = st.columns(2)
            with col_w:
                weight = st.number_input(
                    "體重 (kg)", min_value=30.0, max_value=200.0,
                    value=None, placeholder="例：65.5", step=0.1,
                )
            with col_h:
                height = st.number_input(
                    "身高 (cm)", min_value=100.0, max_value=200.0,
                    value=None, placeholder="例：165", step=0.1,
                )

            # Heart rate
            heart_rate = st.number_input(
                "心律 (bpm)", min_value=40, max_value=200,
                value=None, placeholder="例：80",
            )

            st.divider()

            # Mood / Sleep / Exercise
            col_m, col_s, col_e = st.columns(3)
            with col_m:
                mood = st.selectbox(
                    "今日心情",
                    ["選擇心情", "😊 很好", "🙂 好", "😐 普通", "😔 不好", "😢 很差"],
                )
            with col_s:
                sleep_quality = st.selectbox(
                    "睡眠品質",
                    ["選擇品質", "很好", "好", "普通", "差", "很差"],
                )
            with col_e:
                exercise = st.selectbox(
                    "運動狀況",
                    ["選擇狀況", "有運動", "輕度活動", "無運動"],
                )

            st.divider()

            # Symptoms
            symptoms = st.multiselect("今日症狀", SYMPTOMS)

            # Notes
            notes = st.text_area("其他補充", placeholder="記錄任何其他想補充的健康資訊...")

            submitted = st.form_submit_button(
                "＋ 儲存並生成AI建議", type="primary", use_container_width=True,
            )

        # Handle form submission
        if submitted:
            mood_val = None if mood == "選擇心情" else mood
            sleep_val = None if sleep_quality == "選擇品質" else sleep_quality
            exercise_val = None if exercise == "選擇狀況" else exercise
            symptoms_json = json.dumps(symptoms, ensure_ascii=False) if symptoms else None

            log_id = save_health_log(
                username=username,
                pregnancy_week=pregnancy_week,
                weight=weight,
                height=height,
                heart_rate=heart_rate,
                mood=mood_val,
                sleep_quality=sleep_val,
                exercise=exercise_val,
                symptoms_json=symptoms_json,
                notes=notes or None,
            )
            st.session_state.last_saved_log_id = log_id
            st.success("日誌已儲存！")

            if notes and notes.strip():
                with st.spinner("🤖 AI 情緒分析中..."):
                    try:
                        result = analyze_emotion(notes)
                        update_health_log_ai_advice(log_id, result)
                        st.info(f"🤖 AI 情緒分析：{result}")
                    except Exception as e:
                        st.warning(f"情緒分析失敗：{e}")

    # History
    st.markdown("")
    st.subheader("📋 歷史日誌")

    logs = get_health_logs(username)
    if not logs:
        st.caption("尚無記錄")
        return

    for log in logs:
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

            # Second row: mood, sleep, exercise
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
            if log["notes"]:
                st.caption(f"備註：{log['notes']}")
            if log["ai_advice"]:
                st.caption(f"🤖 AI 情緒分析：{log['ai_advice']}")
