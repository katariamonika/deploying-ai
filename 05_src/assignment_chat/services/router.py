import re
from typing import Dict, Any, Tuple

from services.guardrails import check_user_message
from services.api_service import get_current_weather
from services.semantic_service import SemanticService
from services.tool_service import calculate, web_search


def _extract_city(text: str) -> str:
    m = re.search(r"(?:weather|temperature)\s+(?:in|for)\s+(.+)$", text.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?:in|for)\s+(.+)$", text.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


def _looks_like_math(text: str) -> bool:
    t = text.strip()
    if t.lower().startswith(("calc:", "calculate:", "math:")):
        return True
    has_digit = any(ch.isdigit() for ch in t)
    has_op = any(ch in "+-*/^()" for ch in t)
    return has_digit and has_op


def _strip_math_prefix(text: str) -> str:
    return re.sub(r"^(calc:|calculate:|math:)\s*", "", text.strip(), flags=re.IGNORECASE)


def route_message(user_text: str, memory: Dict[str, Any]) -> str:
    allowed, blocked_msg = check_user_message(user_text)
    if not allowed:
        return blocked_msg

    text = user_text.strip()

    # 1) Weather (Service 1: API)
    if re.search(r"\b(weather|temperature)\b", text.lower()):
        city = _extract_city(text)
        wx = get_current_weather(city)
        if wx.get("ok"):
            return f"Nova here. {wx['summary']}"
        return f"Nova here. {wx.get('message', 'I could not fetch weather right now.')}"

    # 2) Web search (Service 3: Web Search)
    if text.lower().startswith(("search:", "web:", "lookup:")):
        q = re.sub(r"^(search:|web:|lookup:)\s*", "", text, flags=re.IGNORECASE).strip()
        out = web_search(q, k=3)
        if not out["ok"]:
            return f"Nova here. {out['message']}"
        lines = [f"- {r['title']}: {r['snippet']}" for r in out["results"]]
        return "Nova here’s what I found:\n" + "\n".join(lines)

    # 3) Calculator (extra tool feature)
    if _looks_like_math(text):
        expr = _strip_math_prefix(text)
        out = calculate(expr)
        return f"Nova here. {out['message']}"

    # 4) Semantic search (Service 2)
    sem = memory.get("semantic")
    if sem is None:
        sem = SemanticService()
        memory["semantic"] = sem

    hits = sem.query(text, k=3)["results"]
    if hits and hits[0]["score"] > 0.10:
                bullets = "\n".join([f"- {h['text']}" for h in hits])
        return (
            "Nova here. Based on your knowledge base, here are the most relevant points:\n\n"
            f"{bullets}\n\n"
            "If you want, ask me to refine it (e.g., “explain in 2 lines” or “give an example”)."
        )

    # 5) Default personality response
    return (
        "Nova here. I can help using:\n"
        "- Weather: “weather in Toronto”\n"
        "- Knowledge base Q&A: ask a concept question\n"
        "- Web search: “search: your query”\n"
        "- Calculator: “calc: (2+3)*4”\n\n"
        "What do you want to try?"
    )