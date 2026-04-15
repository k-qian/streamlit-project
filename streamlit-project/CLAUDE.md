# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run the app:** `make run`
- **Install dependencies:** `make install`
- **Add a dependency:** `make add pkg=<package>`

## Architecture

「媽媽健康日誌」— 孕期健康追蹤應用，多頁 Streamlit app，cookie-based 認證，SQLite 後端。

- `app.py` — Entry point. 登入/註冊 UI、cookie session 管理、`st.navigation()` 頁面路由。
- `database.py` — SQLite 操作。六張表：`users`、`sessions`、`health_logs`、`notifications`、`childcare_centers`、`exercise_videos`。預設 admin 帳號 (`admin`/`admin123`)。
- `pages/overview.py` — 總覽（預設頁）：歡迎訊息、4 指標卡片、5 快速操作按鈕、空狀態引導。
- `pages/health_journal.py` — 健康日誌：孕期生理數據輸入表單（週數、體重、心率、心情、症狀等）。
- `pages/data_dashboard.py` — 數據儀錶板：4 指標卡片（記錄筆數、最高週數、平均體重、平均心律）+ 心情分佈圖 + 體重/心率趨勢圖。
- `pages/nutrition.py` — 營養建議：輸入週數/體重取得 AI 飲食建議（UI 骨架，AI 未接）+ 運動建議影片（從 SQLite 讀取）。
- `pages/risk_alert.py` — AI 風險預警：空狀態 + 導向健康日誌。
- `pages/health_report.py` — 健康報告：選擇期間生成報告（UI 骨架，AI 未接）。
- `pages/notifications.py` — 通知中心：顯示通知列表或空狀態。
- `pages/childcare_center.py` — 托嬰中心查找：從 SQLite 讀取，依機構類型篩選及關鍵字搜尋。
- `pages/admin/data_manage.py` — Admin 資料管理：xlsx 匯入 + CRUD（托嬰中心、運動影片）。
- `.streamlit/config.toml` — Streamlit server/theme configuration.

Pages are **not** using Streamlit's file-based routing. Each page is a function passed to `st.Page()` and wired through `st.navigation()` in `app.py`. Admin 頁面放在 `pages/admin/` 子目錄，僅 `admin` 用戶可見。

## Key Details

- Python 3.14, managed with `uv`
- SQLite database lives at `data/app.db` (auto-created on first run, WAL mode)
- Auth state flows: SQLite session token → browser cookie (`session_token`) → `st.session_state`
- Cookie 寫入使用 `st.html(unsafe_allow_javascript=True)` + `window.location.reload()`，不能用 `st.rerun()`（會造成 React `useEffect` race condition，script 來不及執行）。詳見 [`docs/streamlit-cookie-auth.md`](docs/streamlit-cookie-auth.md)
- No tests or linting configured
