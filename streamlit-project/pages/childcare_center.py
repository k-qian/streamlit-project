import streamlit as st

from database import get_childcare_centers


def childcare_center_page():
    st.title("🏠 托嬰中心查找")

    data = get_childcare_centers()

    if not data:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding: 4rem 1rem;'>"
                "<p style='font-size:3rem;'>🏠</p>"
                "<h3>尚無資料</h3>"
                "<p style='color:gray;'>請聯繫管理員匯入托嬰中心資料</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        return

    records = [
        {
            "機構類型": r["type"],
            "機構名稱": r["name"],
            "地址": r["address"],
            "電話": r["phone"],
        }
        for r in data
    ]

    # Filters
    col1, col2 = st.columns(2)

    types = sorted(set(r["機構類型"] for r in records if r["機構類型"]))
    with col1:
        selected_type = st.selectbox("機構類型", ["全部"] + types)
    with col2:
        keyword = st.text_input("搜尋（名稱或地址）", placeholder="輸入關鍵字...")

    # Apply filters
    filtered = records
    if selected_type != "全部":
        filtered = [r for r in filtered if r["機構類型"] == selected_type]
    if keyword:
        kw = keyword.strip().lower()
        filtered = [
            r
            for r in filtered
            if kw in r["機構名稱"].lower() or kw in r["地址"].lower()
        ]

    st.caption(f"共 {len(filtered)} 筆結果")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
