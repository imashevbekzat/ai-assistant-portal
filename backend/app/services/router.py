"""Словарный роутинг намерений — базовый механизм и fallback при недоступности LLM.

Сопоставление по словам с учётом словоформ русского языка: ключевое слово
считается совпавшим, если какое-то слово запроса начинается с его основы
(для слов от 5 символов — первые len-2 буквы, иначе слово целиком).
"""

from .catalog import DASHBOARDS

import re

_CLARIFY_PATTERNS = ["а по регионам", "по регионам", "а по филиалам", "по филиалам"]

# Точные соответствия, для которых не применяется грубый стемматчинг.
# Ключевое слово считается совпавшим, если слово запроса начинается с указанного префикса.
# «сделка» — семантически скользкое слово (сделка/сделок/сделку матчатся и на «конверсию в сделку»),
# поэтому матчим его только в составе метрик уровня дэшборда, а не как общий ключ.
_EXCEPTIONS: dict[str, str] = {}


def _normalize(text: str) -> str:
    t = text.lower().replace("ё", "е")
    t = re.sub(r"[^\w\s%&/+-]", " ", t)
    return " ".join(t.split())


def _stem(word: str) -> str:
    """Грубая основа слова для матчинга словоформ (выручка/выручку/выручкой)."""
    if len(word) >= 5:
        return word[: max(3, len(word) - 2)]
    return word


def _keyword_hits(keyword: str, words: list[str], joined: str) -> int:
    kw_n = _normalize(keyword)
    kw_words = kw_n.split()
    if len(kw_words) > 1:
        # Многословное ключевое слово — сильный сигнал (вес выше одиночных).
        return 2 * len(kw_words) + 2 if kw_n in joined else 0
    if kw_n in _EXCEPTIONS:
        prefix = _EXCEPTIONS[kw_n]
        return 2 if any(w.startswith(prefix) for w in words) else 0
    if kw_n == "сделки":
        # Матчится только по формам родительного/именительного падежа
        # (сделка/сделки/сделок), но не «сделку» — иначе «конверсия в сделку»
        # тянет на продажи.
        return 2 if any(w in ("сделка", "сделки", "сделок", "сделкам", "сделками") for w in words) else 0
    stem = _stem(kw_words[0])
    for w in words:
        if len(stem) >= 3 and w.startswith(stem):
            return 2
        if w == kw_words[0]:
            return 2
    return 0


def route(text: str) -> str | None:
    """Возвращает id дэшборда по взвешенному совпадению ключевых слов."""
    joined = _normalize(text)
    words = joined.split()
    best_id: str | None = None
    best_score = 0
    for dash in DASHBOARDS:
        score = sum(_keyword_hits(kw, words, joined) for kw in dash["keywords"])
        if score > best_score:
            best_score = score
            best_id = dash["id"]
    return best_id if best_score > 0 else None


def route_with_context(text: str, last_intent: str | None) -> str | None:
    """Учитывает контекст сессии: «а по регионам?» после вопроса о выручке."""
    t = _normalize(text)
    if last_intent and any(p in t for p in _CLARIFY_PATTERNS):
        return "regions"
    return route(text)


def route_metrics(text: str, dashboard_id: str) -> list[str]:
    """Выбирает метрики дэшборда, о которых спрашивают; по умолчанию — все."""
    dash = get_dashboard(dashboard_id)
    if not dash:
        return []
    mk = dash.get("metric_keywords") or {}
    if not mk:
        return list(dash["metrics"])
    joined = _normalize(text)
    words = joined.split()
    picked: list[str] = []
    for metric_id, keywords in mk.items():
        if any(_keyword_hits(kw, words, joined) for kw in keywords):
            picked.append(metric_id)
    return picked or list(dash["metrics"])


def get_dashboard(dashboard_id: str) -> dict | None:
    return next((d for d in DASHBOARDS if d["id"] == dashboard_id), None)


def all_dashboards() -> list[dict]:
    return [
        {
            "id": d["id"],
            "title": d["title"],
            "section": d["section"],
            "view_url": d["view_url"],
            "description": d["description"],
        }
        for d in DASHBOARDS
    ]


def catalog_for_llm() -> list[dict]:
    return [
        {
            "id": d["id"],
            "title": d["title"],
            "section": d["section"],
            "description": d["description"],
            "metrics": d["metrics"],
        }
        for d in DASHBOARDS
    ]
