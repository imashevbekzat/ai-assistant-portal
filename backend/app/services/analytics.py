"""Аналитический слой: все числа для ответов ассистента считаются здесь,
а не в LLM. YTD, динамика к АППГ, выполнение плана — из демо-данных."""

from .data import METRICS, MONTHS, REGIONS, SOURCE, UPDATED_AT


def _quality(metric_id: str, yoy_pct: float) -> str:
    m = METRICS.get(metric_id, {})
    direction = m.get("direction", "up")
    if direction == "down":
        if yoy_pct <= -5:
            return "уверенное снижение"
        if yoy_pct <= -2:
            return "снижение"
        if yoy_pct < 2:
            return "стабильный уровень"
        if yoy_pct < 5:
            return "небольшой рост"
        return "рост"
    if yoy_pct >= 5:
        return "уверенный рост"
    if yoy_pct >= 2:
        return "умеренный рост"
    if yoy_pct > -2:
        return "стабильный уровень"
    if yoy_pct > -5:
        return "небольшое снижение"
    return "снижение"


def _fmt(v: float) -> str:
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.1f}".replace(",", " ").replace(".", ",")


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def kpi_summary(metric_id: str) -> dict | None:
    m = METRICS.get(metric_id)
    if not m:
        return None
    cur = m["months"][2026]
    prev = m["months"][2025]
    is_rate = m.get("agg") == "avg"
    # Процентные метрики (рентабельность, текучесть, конверсия) агрегируются
    # средним за период; абсолютные — суммой YTD.
    if is_rate:
        ytd = round(sum(cur) / len(cur), 1)
        ytd_prev = round(sum(prev) / len(prev), 1)
    else:
        ytd = float(sum(cur))
        ytd_prev = float(sum(prev))
    yoy_pct = round((ytd / ytd_prev - 1) * 100, 1) if ytd_prev else None
    plan_ytd = m.get("plan_ytd")
    if is_rate and plan_ytd:
        plan_pct = None  # для целевых коридоров отклонение показываем в тексте, не в %
    else:
        plan_pct = round(ytd / plan_ytd * 100, 1) if plan_ytd else None
    return {
        "metric": m["title"],
        "unit": m["unit"],
        "ytd": ytd,
        "ytd_prev": ytd_prev,
        "yoy_pct": yoy_pct,
        "plan_ytd": plan_ytd,
        "plan_pct": plan_pct,
        "quality": _quality(metric_id, yoy_pct) if yoy_pct is not None else "",
        "comment": m.get("comment", ""),
        "updated_at": UPDATED_AT,
        "source": SOURCE,
    }


def _metric_sentence(k: dict) -> str:
    period = "в среднем за период" if k["unit"] == "%" else "YTD"
    parts = [
        f"{k['metric']} {period}: {_fmt(k['ytd'])} {k['unit']}",
    ]
    if k["yoy_pct"] is not None:
        sign = "+" if k["yoy_pct"] >= 0 else "−"
        parts.append(
            f"{sign}{_fmt_pct(abs(k['yoy_pct']))}% к аналогичному периоду прошлого года ({k['quality']})"
        )
    if k["plan_pct"] is not None:
        parts.append(f"выполнение плана — {_fmt_pct(k['plan_pct'])}%")
    elif k["plan_ytd"]:
        parts.append(f"целевой коридор — до {_fmt(k['plan_ytd'])} {k['unit']}")
    return " — ".join(parts) + "."


def regions_insight() -> dict:
    rows = []
    for r in REGIONS["rows"]:
        yoy = round((r["ytd"] / r["ytd_prev"] - 1) * 100, 1) if r["ytd_prev"] else 0.0
        rows.append({"name": r["name"], "ytd": r["ytd"], "ytd_prev": r["ytd_prev"], "yoy_pct": yoy})
    rows.sort(key=lambda x: x["ytd"], reverse=True)
    total = sum(r["ytd"] for r in rows)
    total_prev = sum(r["ytd_prev"] for r in rows)
    total_yoy = round((total / total_prev - 1) * 100, 1) if total_prev else 0.0
    return {
        "title": REGIONS["title"],
        "unit": REGIONS["unit"],
        "rows": rows,
        "total_ytd": total,
        "total_yoy_pct": total_yoy,
        "comment": REGIONS["comment"],
        "updated_at": UPDATED_AT,
        "source": SOURCE,
    }


def _regions_text(data: dict) -> str:
    top = data["rows"][0]
    lines = [
        (
            f"Выручка по регионам YTD: {_fmt(data['total_ytd'])} {data['unit']} "
            f"({'+' if data['total_yoy_pct'] >= 0 else '−'}{_fmt_pct(abs(data['total_yoy_pct']))}% к АППГ)."
        ),
        (
            f"Крупнейший регион — {top['name']}: {_fmt(top['ytd'])} {data['unit']} "
            f"({'+' if top['yoy_pct'] >= 0 else '−'}{_fmt_pct(abs(top['yoy_pct']))}%)."
        ),
    ]
    for r in data["rows"]:
        lines.append(
            f"• {r['name']}: {_fmt(r['ytd'])} {data['unit']} "
            f"({'+' if r['yoy_pct'] >= 0 else '−'}{_fmt_pct(abs(r['yoy_pct']))}%)"
        )
    lines.append(data["comment"])
    return "\n".join(lines)


def build_insight_text(dashboard_id: str, metric_ids: list[str]) -> str:
    """Готовый деловой вывод по шаблону FR-2: цифры → динамика → план → интерпретация.
    Если запрошена конкретная метрика — вывод строится только по ней."""
    if dashboard_id == "regions" or "regions" in metric_ids:
        return _regions_text(regions_insight())

    ids = [m for m in metric_ids if m in METRICS] or metric_ids
    sentences: list[str] = []
    comments: list[str] = []
    for mid in ids:
        k = kpi_summary(mid)
        if not k:
            continue
        sentences.append(_metric_sentence(k))
        if k["comment"]:
            comments.append(k["comment"])
    if comments:
        sentences.append(" ".join(comments[:2]))
    return "\n".join(sentences)


def kpi_payload(metric_ids: list[str]) -> list[dict]:
    out = []
    for mid in metric_ids:
        k = kpi_summary(mid)
        if k:
            out.append(k)
    return out
