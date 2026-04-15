import streamlit as st

from database import (
    get_notifications,
    get_notifications_by_status,
    get_unread_notification_count,
    mark_single_notification_read,
    delete_notification,
)


def _render_notification(n, tab_prefix: str, show_mark_read: bool = False):
    with st.container(border=True):
        col_info, col_actions = st.columns([5, 1])
        with col_info:
            if n["is_read"]:
                st.markdown(f"**{n['title']}**")
            else:
                st.markdown(f"🔴 **{n['title']}**")
            st.markdown(n["message"])
            st.caption(n["created_at"])
        with col_actions:
            if show_mark_read and not n["is_read"]:
                if st.button("✅", key=f"{tab_prefix}_read_{n['id']}", help="標記已讀"):
                    mark_single_notification_read(n["id"])
                    st.rerun()
            if st.button("🗑️", key=f"{tab_prefix}_del_{n['id']}", help="刪除"):
                delete_notification(n["id"])
                st.rerun()


def _render_empty():
    st.markdown(
        "<div style='text-align:center; padding: 4rem 1rem;'>"
        "<p style='font-size:3rem;'>🔔</p>"
        "<h3>暫無通知</h3>"
        "<p style='color:gray;'>當 AI 檢測到健康異常時，通知將在此顯示</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def notifications_page():
    username = st.session_state.username

    unread = get_unread_notification_count(username)

    st.caption("系統通知")
    st.title("通知中心")
    if unread > 0:
        st.markdown(f"有 **{unread}** 則未讀通知")
    else:
        st.markdown("所有通知已讀")

    tab_all, tab_unread, tab_read = st.tabs([
        f"全部",
        f"未讀 ({unread})" if unread > 0 else "未讀",
        "已讀",
    ])

    with tab_all:
        notifications = get_notifications(username)
        if not notifications:
            _render_empty()
        else:
            for n in notifications:
                _render_notification(n, "all", show_mark_read=True)

    with tab_unread:
        unread_list = get_notifications_by_status(username, 0)
        if not unread_list:
            st.info("沒有未讀通知")
        else:
            for n in unread_list:
                _render_notification(n, "unread", show_mark_read=True)

    with tab_read:
        read_list = get_notifications_by_status(username, 1)
        if not read_list:
            st.info("沒有已讀通知")
        else:
            for n in read_list:
                _render_notification(n, "read")
