import math
import json
import re
from typing import Dict, Any, List, Optional
from urllib.request import urlopen
from urllib.parse import urlencode


_ALLOWED_NAMES = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def calculate(expression: str) -> Dict[str, Any]:
    expr = expression.strip()

    for ch in expr:
        if not (ch.isdigit() or ch.isspace() or ch in "+-*/().,^" or ch.isalpha()):
            return {"ok": False, "result": None, "message": "That expression contains unsupported characters."}

    expr = expr.replace("^", "**")

    try:
        val = eval(expr, {"__builtins__": {}}, _ALLOWED_NAMES)
    except Exception:
        return {"ok": False, "result": None, "message": "I couldn't evaluate that. Try: (2+3)*4 or sqrt(16)."}
    return {"ok": True, "result": val, "message": f"The result is {val}."}


def web_search(query: str, k: int = 3) -> Dict[str, Any]:
    """
    Lightweight web search (DuckDuckGo HTML endpoint).
    Returns rephrased/snippet-based results.
    """
    q = query.strip()
    if not q:
        return {"ok": False, "results": [], "message": "Give me a search query after 'search:'."}

    url = "https://duckduckgo.com/html/?" + urlencode({"q": q})
    try:
        html = urlopen(url).read().decode("utf-8", errors="ignore")
    except Exception:
        return {"ok": False, "results": [], "message": "I couldn't reach the search service right now."}

    # Extract titles + snippets from the HTML
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</div>', html)

    cleaned_titles: List[str] = []
    for t in titles:
        t = re.sub(r"<.*?>", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            cleaned_titles.append(t)

    cleaned_snips: List[str] = []
    for a, b in snippets:
        s = a or b
        s = re.sub(r"<.*?>", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            cleaned_snips.append(s)

    results = []
    for i in range(min(k, len(cleaned_titles), len(cleaned_snips))):
        results.append({"title": cleaned_titles[i], "snippet": cleaned_snips[i]})

    if not results:
        return {"ok": False, "results": [], "message": "I didn’t find clean results. Try a shorter query."}

    return {"ok": True, "results": results, "message": "ok"}