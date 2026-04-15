import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st
from fpdf import FPDF

from ai_utils import generate_health_report, format_logs_summary
from database import get_health_logs_in_range

PERIOD_DAYS = {
    "近 1 週": 7,
    "近 2 週": 14,
    "近 4 週": 28,
    "近 8 週": 56,
    "近 12 週": 84,
}

_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansTC-Regular.ttf"


def _build_pdf(report_text: str, period: str, count: int) -> bytes:
    """Convert markdown report text to a styled PDF and return bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Register Chinese font
    pdf.add_font("NotoSansTC", "", str(_FONT_PATH))
    pdf.set_font("NotoSansTC", size=10)

    # --- Header ---
    pdf.set_font("NotoSansTC", size=18)
    pdf.cell(0, 12, "媽媽健康日誌 — 孕期健康報告", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("NotoSansTC", size=9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 8,
        f"期間：{period}　｜　分析筆數：{count}　｜　生成時間：{datetime.now():%Y-%m-%d %H:%M}",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Divider line
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    # --- Body: parse markdown lines ---
    for line in report_text.splitlines():
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue

        # Heading levels
        heading_match = re.match(r"^(#{1,3})\s+(.*)", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            size = {1: 16, 2: 13, 3: 11}.get(level, 11)
            pdf.ln(3)
            pdf.set_font("NotoSansTC", size=size)
            pdf.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            pdf.set_font("NotoSansTC", size=10)
            continue

        # Bullet points (- or *)
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            text = bullet_match.group(1)
            # Remove bold markdown markers
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
            pdf.cell(6)  # indent
            pdf.multi_cell(0, 6, f"•  {text}", new_x="LMARGIN", new_y="NEXT")
            continue

        # Regular paragraph — strip bold markers
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", stripped)
        pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")

    # Output
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def health_report_page():
    username = st.session_state.username

    st.caption("健康報告")
    st.title("孕期健康報告")
    st.markdown("AI 自動生成包含數據分析的完整孕期健康報告")

    with st.container(border=True):
        st.subheader("📄 生成報告設定")

        st.markdown("**報告涵蓋期間**")
        period = st.radio(
            "報告涵蓋期間",
            list(PERIOD_DAYS.keys()),
            index=2,
            horizontal=True,
            label_visibility="collapsed",
        )

        if st.button("📄 生成報告", type="primary", use_container_width=True):
            days = PERIOD_DAYS[period]
            logs = get_health_logs_in_range(username, days)

            if not logs:
                st.warning(f"{period}內沒有健康日誌記錄，請先記錄健康日誌。")
            else:
                summary = format_logs_summary(logs)
                with st.spinner("🤖 AI 報告生成中..."):
                    try:
                        result = generate_health_report(summary, period, username)
                        st.session_state.health_report = result
                        st.session_state.health_report_period = period
                        st.session_state.health_report_count = len(logs)
                    except Exception as e:
                        st.error(f"報告生成失敗：{e}")

    if "health_report" in st.session_state:
        st.markdown("")
        with st.container(border=True):
            st.subheader("📋 AI 健康報告")
            st.caption(
                f"期間：{st.session_state.health_report_period}　"
                f"分析筆數：{st.session_state.health_report_count}"
            )
            st.markdown(st.session_state.health_report)

            # PDF download
            pdf_bytes = _build_pdf(
                st.session_state.health_report,
                st.session_state.health_report_period,
                st.session_state.health_report_count,
            )
            today = datetime.now().strftime("%Y%m%d")
            st.download_button(
                label="📥 下載 PDF 報告",
                data=pdf_bytes,
                file_name=f"健康報告_{st.session_state.health_report_period}_{today}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
