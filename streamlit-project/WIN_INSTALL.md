# Windows 安裝指南

## 前置需求

### 1. 安裝 uv（Python 套件管理器）

開啟 PowerShell，執行：

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

安裝完成後重新開啟終端機，確認安裝成功：

```powershell
uv --version
```

### 2. 安裝 Python 3.14

```powershell
uv python install 3.14
```

## 安裝與執行

### 安裝依賴

```powershell
uv sync
```

### 啟動應用

```powershell
uv run streamlit run app.py
```

啟動後瀏覽器會自動開啟 `http://localhost:8501`。

### 新增套件

```powershell
uv add <package>
```

## 注意事項

- 本專案使用 `Makefile` 作為 macOS/Linux 的快捷指令，Windows 不支援 `make`，請直接使用上述 `uv` 指令。
- 若 Python 3.14 下某些套件（如 `bcrypt`）安裝失敗，可嘗試將 `pyproject.toml` 中的 `requires-python` 改為 `">=3.12"`，並執行 `uv sync` 重試。
- SQLite 為 Python 內建模組，無需額外安裝。
- 資料庫檔案 `data/app.db` 會在首次執行時自動建立。
