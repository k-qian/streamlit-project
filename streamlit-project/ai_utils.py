import json

import streamlit as st
from google import genai
from google.genai import types

from database import create_notification


def format_logs_summary(logs, max_entries: int = 20) -> str:
    """Format health logs into a text summary for AI analysis."""
    lines = []
    for log in logs[:max_entries]:
        parts = [f"日期：{log['log_date']}", f"週數：第{log['pregnancy_week']}週"]
        if log["weight"]:
            parts.append(f"體重：{log['weight']}kg")
        if log["heart_rate"]:
            parts.append(f"心率：{log['heart_rate']}bpm")
        if log["mood"]:
            parts.append(f"心情：{log['mood']}")
        if log["sleep_quality"]:
            parts.append(f"睡眠：{log['sleep_quality']}")
        if log["exercise"]:
            parts.append(f"運動：{log['exercise']}")
        if log["symptoms"]:
            try:
                syms = json.loads(log["symptoms"])
                if syms:
                    parts.append(f"症狀：{'、'.join(syms)}")
            except json.JSONDecodeError:
                pass
        if log["notes"]:
            parts.append(f"備註：{log['notes']}")
        lines.append("｜".join(parts))
    return "\n".join(lines)


# --- Gemini function calling tool definition ---

_notification_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="send_notification",
            description="當發現中風險或高風險的健康異常時，呼叫此工具發送通知給用戶。低風險時不要呼叫。",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "title": types.Schema(type="STRING", description="通知標題，簡短描述異常類型"),
                    "message": types.Schema(type="STRING", description="通知內容，簡述異常狀況和建議行動"),
                },
                required=["title", "message"],
            ),
        )
    ]
)


def _handle_function_calls(response, username: str) -> str:
    """Process Gemini response, execute any function calls, and return text."""
    text_parts = []
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                fc = part.function_call
                if fc.name == "send_notification":
                    title = fc.args.get("title", "健康提醒")
                    message = fc.args.get("message", "")
                    create_notification(username, title, message)
            elif part.text:
                text_parts.append(part.text)
    return "\n".join(text_parts) if text_parts else ""


def _get_client() -> genai.Client:
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


# --- AI functions ---


def analyze_emotion(text: str) -> str:
    """Analyze the emotional state from user's notes using Gemini."""
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=f"""你是一位孕期心理健康分析師。請客觀分析以下孕婦的日誌文字，完成以下項目：
1. 情緒辨識：判斷主要情緒狀態（如：焦慮、愉悅、疲憊、平靜等）
2. 情緒強度：低 / 中 / 高
3. 簡要分析：用 2-3 句話客觀描述情緒成因與狀態

請用繁體中文回覆，語氣保持專業客觀。

日誌內容：
{text}""",
    )
    return response.text


def get_nutrition_advice(week: int, weight: float | None, height: float | None) -> str:
    """Get personalized nutrition advice based on pregnancy week and body stats."""
    client = _get_client()

    body_info = ""
    if weight:
        body_info += f"，體重 {weight} kg"
    if height:
        body_info += f"，身高 {height} cm"
    if weight and height:
        bmi = weight / ((height / 100) ** 2)
        body_info += f"（BMI {bmi:.1f}）"

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=f"""你是一位專業的孕期營養師。請根據以下孕婦資訊，提供個性化的飲食建議。

孕婦資訊：懷孕第 {week} 週{body_info}

請提供以下內容（使用繁體中文）：
1. 本週營養重點：該孕期階段最需要的營養素
2. 推薦食物：列出 5-8 種推薦食物
3. 應避免食物：列出需要注意或避免的食物
4. 每日飲食建議：簡要的一日三餐建議

請用條列式呈現，簡潔易讀。""",
    )
    return response.text


def analyze_health_risk(logs_summary: str, username: str) -> str:
    """Analyze potential health risks. Sends notification via function calling if risk is medium/high."""
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=f"""你是一位專業的產科健康風險分析師。請根據以下孕婦的近期健康日誌資料，進行風險評估。

請提供以下分析（使用繁體中文）：
1. 整體風險等級：低風險 / 中風險 / 高風險
2. 異常指標分析：檢視體重變化趨勢、心率是否異常、情緒狀態、睡眠品質、症狀模式等
3. 需關注事項：列出需要特別注意的健康問題
4. 建議措施：針對發現的風險給出具體建議
5. 就醫提醒：如有需要就醫的狀況請明確標示

如果整體風險為中風險或高風險，請使用 send_notification 工具通知用戶。

請保持專業客觀，用條列式呈現，簡潔易讀。

健康日誌資料：
{logs_summary}""",
        config=types.GenerateContentConfig(tools=[_notification_tool]),
    )
    return _handle_function_calls(response, username)


def generate_health_report(logs_summary: str, period: str, username: str) -> str:
    """Generate a comprehensive health report. Sends notification if abnormalities found."""
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=f"""你是一位專業的產科醫療報告撰寫者。請根據以下孕婦{period}內的健康日誌資料，撰寫一份完整的孕期健康報告。

請包含以下章節（使用繁體中文）：
1. 期間總覽：記錄筆數、孕期階段、整體健康狀況摘要
2. 體重趨勢分析：體重變化是否在正常範圍、增重速度評估
3. 心率分析：心率數據是否正常、是否有異常波動
4. 情緒與睡眠評估：情緒變化趨勢、睡眠品質統計
5. 症狀紀錄分析：常見症狀統計、是否有需要關注的症狀模式
6. 綜合建議：根據以上分析給出的具體生活與健康建議

如果發現任何需要關注的異常狀況，請使用 send_notification 工具通知用戶。

請用標題和條列式呈現，語氣專業但易於理解。

健康日誌資料：
{logs_summary}""",
        config=types.GenerateContentConfig(tools=[_notification_tool]),
    )
    return _handle_function_calls(response, username)
