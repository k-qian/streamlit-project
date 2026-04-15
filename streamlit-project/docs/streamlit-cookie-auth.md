# Streamlit Cookie 認證：問題與解決方案

## 問題

登入後重新整理頁面（F5）會遺失登入狀態，因為 `st.session_state` 只存在於單次 WebSocket 連線中，F5 會建立新連線，狀態全部清空。

## 嘗試過的方案與失敗原因

### 1. `streamlit-cookies-controller`

這個套件透過 iframe 注入 JavaScript 來操作 cookie。問題是 iframe 的載入時機與 Streamlit 的 rerun 機制有 race condition——cookie 可能在 iframe 載入完成前就被讀取，導致永遠讀不到值。

### 2. `st.query_params`

把 session token 放在 URL query string 中。問題是 `st.navigation()` 在切換頁面時會替換整個 URL，token 會被清掉。

### 3. `st.html()` + `st.rerun()`（接近成功但失敗）

使用 `st.html(unsafe_allow_javascript=True)` 在主頁面 DOM 中執行 JavaScript 設定 cookie，然後呼叫 `st.rerun()` 重新渲染頁面。

**失敗原因：React `useEffect` race condition**

Streamlit 前端使用 React。`st.html()` 元件中的 `<script>` 標籤是透過 `useEffect` hook 執行的（因為 `innerHTML` 不會執行 script 標籤，Streamlit 需要手動重新建立 script 元素）。執行順序：

1. `set_session_cookie(token)` 將 HTML delta 排入佇列
2. `st.rerun()` 拋出 `RerunException`，將所有 delta 送到瀏覽器
3. 瀏覽器收到 HTML 元件，React 開始渲染
4. **幾乎同時**，rerun 產生的新 delta 也到達（使用者已登入 → 渲染 dashboard）
5. React reconciliation：HTML 元件在 `useEffect` 觸發前就被卸載
6. `<script>` 從未執行 → cookie 從未設定

## 最終解決方案

**`st.html()` + `window.location.reload()` + `st.stop()`**

核心概念：讓 JavaScript 同時負責設定 cookie 和重新載入頁面，不依賴 Python 端的 `st.rerun()`。

### Cookie 輔助函式

```python
def set_session_cookie(token: str):
    st.html(
        f"<script>document.cookie='session_token={token}; path=/; max-age={30*86400}; SameSite=Strict'; window.location.reload();</script>",
        unsafe_allow_javascript=True,
    )

def clear_session_cookie():
    st.html(
        "<script>document.cookie='session_token=; path=/; max-age=0'; window.location.reload();</script>",
        unsafe_allow_javascript=True,
    )
```

### 為什麼這樣有效

1. **`st.stop()`** 取代 `st.rerun()`——停止 Python 腳本但不觸發新的渲染，HTML 元件保持掛載
2. React 的 `useEffect` 正常觸發，script 執行
3. `document.cookie` 設定 cookie（同步操作，立即生效）
4. `window.location.reload()` 重新載入頁面，建立新的 WebSocket 連線
5. 新連線中 `st.context.cookies` 讀到剛設定的 cookie
6. Auto-login 區塊驗證 token → 恢復登入狀態

### 兩層持久化機制

| 場景 | 機制 | 說明 |
|------|------|------|
| 頁面切換（Dashboard ↔ Settings） | `st.session_state` | 同一 WebSocket 連線內自動保持 |
| 重新整理（F5） | browser cookie → `st.context.cookies` | 新連線時從 cookie 還原 |

### Streamlit 關鍵行為

- **`st.session_state`**：在同一 WebSocket session 內跨 rerun 和頁面導航持久化。F5 會清空。
- **`st.context.cookies`**：在 WebSocket 握手時讀取一次（快取）。Rerun 不會更新。只有新連線（F5）才會拿到最新的 cookie。
- **`st.html(unsafe_allow_javascript=True)`**：直接在主頁面 DOM 中渲染（不是 iframe）。`document.cookie` 設定在主域名上。
