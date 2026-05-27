"""Validate data/questions.json and produce a human-readable HTML report.

Usage:
    python validate.py            # writes parser/report.html
    python validate.py --open     # writes report and opens it in browser

The heuristics mirror web/src/lib/validate.js so both UI and report agree.
"""

from __future__ import annotations

import html
import json
import sys
import webbrowser
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"
REPORT_FILE = Path(__file__).resolve().parent / "report.html"


def validate(q):
    issues = []
    if not q or not q.get("type"):
        return [("error", "missing_type", "Нет типа вопроса")]

    statement = (q.get("statement") or "").strip()
    if len(statement) < 20:
        issues.append(("warn", "short_statement", f"Очень короткая формулировка ({len(statement)} симв.)"))
    if len(statement) > 800:
        issues.append(("info", "long_statement", f"Длинный statement ({len(statement)} симв.) — возможна склейка"))

    t = q["type"]
    if t in ("single", "multi"):
        opts = q.get("options") or []
        keys = [o["key"] for o in opts]
        if len(opts) < 3:
            issues.append(("warn", "low_options", f"Только {len(opts)} вариант(ов) — ожидается 3–5"))
        empty = [o["key"] for o in opts if not (o.get("text") or "").strip()]
        if empty:
            issues.append(("warn", "empty_option", f"Пустой текст у варианта(ов) {', '.join(empty)}"))
        ans = q.get("answer") or []
        outside = [a for a in ans if a not in keys]
        if outside:
            issues.append(("error", "answer_outside_options", f"В ответе буквы вне вариантов: {', '.join(outside)}"))
        if not ans:
            issues.append(("error", "no_answer", "Нет правильного ответа"))
        seen = {}
        dup_texts = []
        for o in opts:
            key = (o.get("text") or "").strip().lower()
            if not key:
                continue
            if key in seen:
                dup_texts.append(key)
            seen[key] = True
        if dup_texts:
            issues.append(("warn", "duplicate_options", f"Дублирующиеся варианты: {'; '.join(dup_texts[:3])}"))

    elif t == "sequence":
        items = q.get("items") or []
        keys = [i["key"] for i in items]
        if len(items) < 3:
            issues.append(("warn", "low_items", f"Только {len(items)} элемент(ов) — ожидается 3–6"))
        empty = [i["key"] for i in items if not (i.get("text") or "").strip()]
        if empty:
            issues.append(("warn", "empty_item", f"Пустой текст у элемента(ов) {', '.join(empty)}"))
        ans = q.get("answer") or []
        outside = [a for a in ans if a not in keys]
        if outside:
            issues.append(("error", "answer_outside_items", f"В ответе буквы вне элементов: {', '.join(outside)}"))
        if len(ans) != len(items):
            issues.append(("warn", "answer_length_mismatch", f"Длина ответа ({len(ans)}) ≠ числу элементов ({len(items)})"))

    elif t == "matching":
        left = q.get("left") or []
        right = q.get("right") or []
        ans = q.get("answer") or {}
        left_keys = [l["key"] for l in left]
        right_keys = [r["key"] for r in right]
        if len(left) < 2 or len(right) < 2:
            issues.append(("warn", "low_pairs", f"Мало пунктов слева/справа ({len(left)}/{len(right)})"))
        empty_l = [l["key"] for l in left if not (l.get("text") or "").strip()]
        if empty_l:
            issues.append(("warn", "empty_left", f"Пустые пункты слева: {', '.join(empty_l)}"))
        empty_r = [r["key"] for r in right if not (r.get("text") or "").strip()]
        if empty_r:
            issues.append(("warn", "empty_right", f"Пустые пункты справа: {', '.join(empty_r)}"))
        outside_l = [k for k in ans.keys() if k not in left_keys]
        outside_r = [v for v in ans.values() if v not in right_keys]
        if outside_l:
            issues.append(("error", "answer_left_outside", f"Левые ключи ответа вне списка: {', '.join(outside_l)}"))
        if outside_r:
            issues.append(("error", "answer_right_outside", f"Правые ключи ответа вне списка: {', '.join(outside_r)}"))
        if len(ans) != len(left) or len(ans) != len(right):
            issues.append((
                "warn",
                "matching_size_mismatch",
                f"Размеры не совпадают: left={len(left)}, right={len(right)}, ans={len(ans)}",
            ))

    elif t == "open":
        ans = (q.get("answer") or "").strip()
        if not ans:
            issues.append(("error", "no_answer", "Нет эталона ответа"))
        elif len(ans) < 3:
            issues.append(("warn", "very_short_answer", f"Очень короткий эталон ({len(ans)} симв.)"))

    return issues


def worst_level(issues):
    levels = [lvl for lvl, *_ in issues]
    if "error" in levels:
        return "error"
    if "warn" in levels:
        return "warn"
    if "info" in levels:
        return "info"
    return None


import re as _re


def _normalise(text):
    return _re.sub(r"\s+", " ", (text or "")).strip().lower()


def _fingerprint(q):
    parts = [_normalise(q.get("statement"))]
    t = q.get("type")
    if t in ("single", "multi"):
        for o in q.get("options") or []:
            parts.append(_normalise(o.get("text")))
    elif t == "sequence":
        for i in q.get("items") or []:
            parts.append(_normalise(i.get("text")))
    elif t == "matching":
        for l in q.get("left") or []:
            parts.append(_normalise(l.get("text")))
        for r in q.get("right") or []:
            parts.append(_normalise(r.get("text")))
    elif t == "open":
        parts.append(_normalise(q.get("answer")))
    return "|".join(p for p in parts if p)


def find_duplicates(questions):
    """Return dict: question_id -> [other_id, ...] for duplicate fingerprints."""
    groups = {}
    for q in questions:
        fp = _fingerprint(q)
        if len(fp) < 30:
            continue
        groups.setdefault(fp, []).append(q["id"])
    result = {}
    for ids in groups.values():
        if len(ids) < 2:
            continue
        for qid in ids:
            result[qid] = [other for other in ids if other != qid]
    return result


HTML_TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<title>Отчёт валидатора · ГОСы 09.03.02</title>
<style>
  :root {{
    --bg: #f5f5f7; --surface: #fff; --border: #d1d1d6; --text: #1c1c1e;
    --muted: #6e6e73; --primary: #0a84ff; --success: #34c759;
    --error: #ff3b30; --warning: #ff9500;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; background: var(--bg); color: var(--text);
          font: 15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }}
  .container {{ max-width: 1080px; margin: 0 auto; }}
  h1 {{ margin: 0 0 8px; }}
  h2 {{ margin: 24px 0 8px; font-size: 19px; }}
  .muted {{ color: var(--muted); }}
  .card {{ background: var(--surface); border: 1px solid var(--border);
           border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
  .row {{ display: flex; gap: 24px; flex-wrap: wrap; }}
  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
           font-size: 12px; background: #e5e5ea; color: var(--muted);
           margin-right: 4px; }}
  .pill.single   {{ background: rgba(10,132,255,0.15);  color: var(--primary); }}
  .pill.multi    {{ background: rgba(255,149,0,0.15);   color: var(--warning); }}
  .pill.matching {{ background: rgba(175,82,222,0.15);  color: #af52de; }}
  .pill.sequence {{ background: rgba(50,173,230,0.15);  color: var(--primary); }}
  .pill.open     {{ background: rgba(52,199,89,0.15);   color: var(--success); }}
  .issue {{ font-size: 13px; padding: 4px 8px; border-radius: 6px; margin-top: 4px; }}
  .issue.error {{ background: rgba(255,59,48,0.10); color: var(--error); }}
  .issue.warn  {{ background: rgba(255,149,0,0.10); color: var(--warning); }}
  .issue.info  {{ background: rgba(10,132,255,0.10); color: var(--primary); }}
  .item.error {{ border-color: var(--error); }}
  .item.warn  {{ border-color: var(--warning); }}
  .item.info  {{ border-color: var(--primary); }}
  .stat {{ font-size: 26px; font-weight: 700; }}
  .stat-label {{ font-size: 13px; color: var(--muted); }}
  details {{ margin-top: 8px; }}
  code {{ background: #f1f1f3; padding: 1px 6px; border-radius: 4px; font-size: 13px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  th {{ font-size: 13px; color: var(--muted); font-weight: 600; }}
</style>
</head>
<body>
<div class="container">
  <h1>Отчёт валидатора</h1>
  <p class="muted">Файл: <code>data/questions.json</code>. Всего вопросов: <strong>{total}</strong>.</p>

  <div class="card">
    <div class="row">
      <div><div class="stat-label">Без замечаний</div><div class="stat" style="color: var(--success);">{ok}</div></div>
      <div><div class="stat-label">С ошибками</div><div class="stat" style="color: var(--error);">{errors}</div></div>
      <div><div class="stat-label">Подозрительных</div><div class="stat" style="color: var(--warning);">{warns}</div></div>
      <div><div class="stat-label">Заметки</div><div class="stat" style="color: var(--primary);">{infos}</div></div>
      <div><div class="stat-label">Дубликатов</div><div class="stat" style="color: #af52de;">{duplicates}</div></div>
    </div>
  </div>

  <h2>По дисциплинам</h2>
  <div class="card">
    <table>
      <tr><th>№</th><th>Дисциплина</th><th>Вопросов</th><th>single</th><th>multi</th><th>matching</th><th>sequence</th><th>open</th><th>Ошибок</th><th>Подозр.</th></tr>
      {discipline_rows}
    </table>
  </div>

  <h2>Все проблемные вопросы ({problem_count})</h2>
  <p class="muted">Сортировано: errors → warns → infos. ID вопроса можно поискать в <code>data/questions.json</code>.</p>
  {problem_items}

  <h2 style="margin-top: 32px;">Все вопросы ({total})</h2>
  <details>
    <summary>Раскрыть полный список</summary>
    {all_items}
  </details>
</div>
</body>
</html>
"""


def render_item(q, issues, level=None):
    cls = level or ""
    parts = [f'<div class="card item {cls}">']
    parts.append('<div class="row" style="justify-content: space-between; gap: 8px;">')
    parts.append("<div>")
    parts.append(f'<span class="pill {q["type"]}">{q["type"]}</span>')
    parts.append(f'<span class="pill">Дисц. {q["discipline_num"]}</span>')
    parts.append(f'<span class="muted">{html.escape(q["id"])} · стр. {q.get("page")}</span>')
    parts.append("</div>")
    parts.append("</div>")
    parts.append(f'<div style="margin-top: 6px; font-weight: 500;">{html.escape(q.get("statement", ""))}</div>')

    for lvl, code, label in issues:
        parts.append(f'<div class="issue {lvl}">{html.escape(label)}</div>')

    # answer
    ans = q.get("answer")
    if isinstance(ans, list):
        ans_str = " → ".join(ans) if q.get("type") == "sequence" else ", ".join(ans)
    elif isinstance(ans, dict):
        ans_str = ", ".join(f"{k}-{v}" for k, v in ans.items())
    else:
        ans_str = str(ans or "")
    parts.append(f'<div class="muted" style="margin-top: 6px; font-size: 13px;">Ответ: <strong>{html.escape(ans_str)}</strong></div>')

    if q.get("raw_answer"):
        parts.append(f'<div class="muted" style="font-size: 12px;">raw_answer: <code>{html.escape(str(q["raw_answer"]))}</code></div>')

    # body
    body_parts = []
    if q.get("options"):
        body_parts.append("<div class='muted' style='font-size: 13px; margin-top: 8px;'>Варианты:</div>")
        for o in q["options"]:
            body_parts.append(f'<div><strong>{o["key"]})</strong> {html.escape(o.get("text", ""))}</div>')
    if q.get("items"):
        body_parts.append("<div class='muted' style='font-size: 13px; margin-top: 8px;'>Элементы:</div>")
        for o in q["items"]:
            body_parts.append(f'<div><strong>{o["key"]})</strong> {html.escape(o.get("text", ""))}</div>')
    if q.get("left"):
        body_parts.append("<div class='muted' style='font-size: 13px; margin-top: 8px;'>Слева:</div>")
        for o in q["left"]:
            body_parts.append(f'<div><strong>{o["key"]}.</strong> {html.escape(o.get("text", ""))}</div>')
    if q.get("right"):
        body_parts.append("<div class='muted' style='font-size: 13px; margin-top: 8px;'>Справа:</div>")
        for o in q["right"]:
            body_parts.append(f'<div><strong>{o["key"]}.</strong> {html.escape(o.get("text", ""))}</div>')

    if body_parts:
        parts.append("<details><summary class='muted' style='cursor: pointer; font-size: 13px;'>Развернуть содержимое</summary>")
        parts.extend(body_parts)
        parts.append("</details>")

    parts.append("</div>")
    return "".join(parts)


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} questions from {DATA_FILE}")

    annotated = []
    by_disc = {}
    counters = Counter()
    duplicates_map = find_duplicates(data)
    duplicates_count = 0

    # Detect duplicate ids — these are CRITICAL (Vue can't render with non-unique :key)
    id_counter = Counter(q.get("id") for q in data)
    duplicate_id_set = {i for i, n in id_counter.items() if i and n > 1}
    missing_id_count = sum(1 for q in data if not q.get("id"))

    for q in data:
        issues = validate(q)
        qid = q.get("id")
        if not qid:
            issues.append((
                "error",
                "missing_id",
                "У вопроса отсутствует поле id — он не отрендерится в каталоге/тренировке",
            ))
        elif qid in duplicate_id_set:
            other_count = id_counter[qid] - 1
            issues.append((
                "error",
                "duplicate_id",
                f"Дубликат id {qid}: используется ещё {other_count} раз — Vue ломает рендер",
            ))
        if q.get("discipline_num") is None:
            issues.append((
                "error",
                "missing_discipline",
                "У вопроса нет discipline_num — он не попадёт в фильтр по дисциплинам",
            ))
        dup_ids = duplicates_map.get(qid)
        if dup_ids:
            preview = ", ".join(dup_ids[:3]) + ("..." if len(dup_ids) > 3 else "")
            issues.append((
                "warn",
                "duplicate_statement",
                f"Дубликат: такая же формулировка у {len(dup_ids)} других вопрос(ов) ({preview})",
            ))
            duplicates_count += 1
        level = worst_level(issues)
        annotated.append((q, issues, level))

        d = q["discipline_num"]
        info = by_disc.setdefault(
            d,
            {
                "num": d,
                "name": q["discipline_name"],
                "total": 0,
                "errors": 0,
                "warns": 0,
                "single": 0, "multi": 0, "matching": 0, "sequence": 0, "open": 0,
            },
        )
        info["total"] += 1
        info[q["type"]] += 1
        if level == "error":
            info["errors"] += 1
        elif level == "warn":
            info["warns"] += 1

        counters[level or "ok"] += 1

    total = len(data)
    errors = counters["error"]
    warns = counters["warn"]
    infos = counters["info"]
    ok = counters["ok"]

    print(f"  ok: {ok}, warn: {warns}, error: {errors}, info: {infos}, duplicates: {duplicates_count}")
    if duplicate_id_set:
        print(f"  [WARN] {len(duplicate_id_set)} duplicate id(s): {sorted(duplicate_id_set)[:5]}")
    if missing_id_count:
        print(f"  [WARN] {missing_id_count} question(s) without id")

    problems = [(q, issues, lvl) for q, issues, lvl in annotated if lvl is not None]
    # sort: error first, then warn, then info; inside group preserve order
    order = {"error": 0, "warn": 1, "info": 2}
    problems.sort(key=lambda x: order[x[2]])

    discipline_rows = "".join(
        f"<tr>"
        f"<td>{d['num']}</td>"
        f"<td>{html.escape(d['name'])}</td>"
        f"<td>{d['total']}</td>"
        f"<td>{d['single']}</td>"
        f"<td>{d['multi']}</td>"
        f"<td>{d['matching']}</td>"
        f"<td>{d['sequence']}</td>"
        f"<td>{d['open']}</td>"
        f"<td style='color: var(--error);'>{d['errors']}</td>"
        f"<td style='color: var(--warning);'>{d['warns']}</td>"
        f"</tr>"
        for d in sorted(by_disc.values(), key=lambda x: x["num"])
    )

    problem_items = "".join(render_item(q, issues, lvl) for q, issues, lvl in problems)
    all_items = "".join(render_item(q, issues, lvl) for q, issues, lvl in annotated)

    report = HTML_TEMPLATE.format(
        total=total, ok=ok, errors=errors, warns=warns, infos=infos,
        duplicates=duplicates_count,
        discipline_rows=discipline_rows,
        problem_count=len(problems),
        problem_items=problem_items or "<p class='muted'>Проблем не найдено 🎉</p>",
        all_items=all_items,
    )
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_FILE}")

    if "--open" in sys.argv:
        webbrowser.open(REPORT_FILE.as_uri())


if __name__ == "__main__":
    main()
