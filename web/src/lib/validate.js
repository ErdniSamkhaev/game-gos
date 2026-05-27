/**
 * Heuristic validator for a parsed question.
 *
 * Returns an array of issue objects { level, code, label } so the UI (and
 * the Python report) can flag questions that look corrupt after parsing.
 *
 * Levels:
 *   - "error" — the question is unusable as-is (e.g. answer points to a
 *     letter that doesn't exist in options).
 *   - "warn"  — the question is likely fine but has a sign of broken parsing
 *     (very short statement, fewer options than usual, duplicated options).
 *   - "info"  — non-fatal observation (very long text, possibly merged with
 *     a neighbour).
 */
export function validateQuestion(q) {
  const issues = [];
  if (!q || !q.type) {
    return [{ level: "error", code: "missing_type", label: "Нет типа вопроса" }];
  }

  const statement = (q.statement || "").trim();
  if (statement.length < 20) {
    issues.push({
      level: "warn",
      code: "short_statement",
      label: `Очень короткая формулировка (${statement.length} симв.)`,
    });
  }
  if (statement.length > 800) {
    issues.push({
      level: "info",
      code: "long_statement",
      label: `Длинный statement (${statement.length} симв.) — может быть склейка`,
    });
  }

  if (q.type === "single" || q.type === "multi") {
    const opts = q.options || [];
    const keys = opts.map((o) => o.key);
    if (opts.length < 3) {
      issues.push({
        level: "warn",
        code: "low_options",
        label: `Только ${opts.length} вариант(ов) — ожидается 3–5`,
      });
    }
    const emptyOpt = opts.find((o) => !(o.text || "").trim());
    if (emptyOpt) {
      issues.push({
        level: "warn",
        code: "empty_option",
        label: `Пустой текст у варианта ${emptyOpt.key}`,
      });
    }
    const ans = q.answer || [];
    const outside = ans.filter((a) => !keys.includes(a));
    if (outside.length) {
      issues.push({
        level: "error",
        code: "answer_outside_options",
        label: `В ответе есть буквы вне вариантов: ${outside.join(", ")}`,
      });
    }
    if (!ans.length) {
      issues.push({ level: "error", code: "no_answer", label: "Нет правильного ответа" });
    }
    const dup = findDuplicateStrings(opts.map((o) => normaliseText(o.text)));
    if (dup.length) {
      issues.push({
        level: "warn",
        code: "duplicate_options",
        label: `Дублирующиеся варианты: ${dup.join("; ")}`,
      });
    }
  } else if (q.type === "sequence") {
    const items = q.items || [];
    const keys = items.map((i) => i.key);
    if (items.length < 3) {
      issues.push({
        level: "warn",
        code: "low_items",
        label: `Только ${items.length} элемент(ов) — ожидается 3–6`,
      });
    }
    const emptyItem = items.find((i) => !(i.text || "").trim());
    if (emptyItem) {
      issues.push({
        level: "warn",
        code: "empty_item",
        label: `Пустой текст у элемента ${emptyItem.key}`,
      });
    }
    const ans = q.answer || [];
    const outside = ans.filter((a) => !keys.includes(a));
    if (outside.length) {
      issues.push({
        level: "error",
        code: "answer_outside_items",
        label: `В ответе буквы вне элементов: ${outside.join(", ")}`,
      });
    }
    if (ans.length !== items.length) {
      issues.push({
        level: "warn",
        code: "answer_length_mismatch",
        label: `Длина ответа (${ans.length}) ≠ числу элементов (${items.length})`,
      });
    }
  } else if (q.type === "matching") {
    const left = q.left || [];
    const right = q.right || [];
    const leftKeys = left.map((l) => l.key);
    const rightKeys = right.map((r) => r.key);
    const ans = q.answer || {};
    const ansLeft = Object.keys(ans);
    const ansRight = Object.values(ans);
    if (left.length < 2 || right.length < 2) {
      issues.push({
        level: "warn",
        code: "low_pairs",
        label: `Мало пунктов слева/справа (${left.length}/${right.length})`,
      });
    }
    const emptyLeft = left.find((l) => !(l.text || "").trim());
    if (emptyLeft) {
      issues.push({
        level: "warn",
        code: "empty_left",
        label: `Пустой пункт слева ${emptyLeft.key}`,
      });
    }
    const emptyRight = right.find((r) => !(r.text || "").trim());
    if (emptyRight) {
      issues.push({
        level: "warn",
        code: "empty_right",
        label: `Пустой пункт справа ${emptyRight.key}`,
      });
    }
    const outsideL = ansLeft.filter((k) => !leftKeys.includes(k));
    const outsideR = ansRight.filter((v) => !rightKeys.includes(v));
    if (outsideL.length) {
      issues.push({
        level: "error",
        code: "answer_left_outside",
        label: `Левые ключи ответа вне списка: ${outsideL.join(", ")}`,
      });
    }
    if (outsideR.length) {
      issues.push({
        level: "error",
        code: "answer_right_outside",
        label: `Правые ключи ответа вне списка: ${outsideR.join(", ")}`,
      });
    }
    if (ansLeft.length !== left.length || ansRight.length !== right.length) {
      issues.push({
        level: "warn",
        code: "matching_size_mismatch",
        label: `Размеры не совпадают: left=${left.length}, right=${right.length}, ans=${ansLeft.length}`,
      });
    }
  } else if (q.type === "open") {
    const ans = (q.answer || "").trim();
    if (!ans) {
      issues.push({ level: "error", code: "no_answer", label: "Нет эталона ответа" });
    } else if (ans.length < 3) {
      issues.push({
        level: "warn",
        code: "very_short_answer",
        label: `Очень короткий эталон (${ans.length} симв.)`,
      });
    }
  }

  return issues;
}

export function highestLevel(issues) {
  if (issues.some((i) => i.level === "error")) return "error";
  if (issues.some((i) => i.level === "warn")) return "warn";
  if (issues.some((i) => i.level === "info")) return "info";
  return null;
}

/**
 * Build a Map<questionId, Array<otherDuplicateId>> for all questions whose
 * fingerprints match. The fingerprint includes the statement AND the full
 * payload (options/items/left/right/answer) so matching questions that just
 * share the prompt "Установите соответствие" but have different pair lists
 * are NOT flagged.
 */
export function findDuplicates(questions) {
  const groups = new Map();
  for (const q of questions) {
    if (!q || !q.statement) continue;
    const key = fingerprint(q);
    if (key.length < 30) continue; // short fingerprints generate false positives
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(q);
  }
  const result = new Map();
  for (const list of groups.values()) {
    if (list.length < 2) continue;
    for (const q of list) {
      result.set(
        q.id,
        list.filter((other) => other.id !== q.id).map((other) => other.id),
      );
    }
  }
  return result;
}

function fingerprint(q) {
  const parts = [normaliseText(q.statement || "")];
  if (q.type === "single" || q.type === "multi") {
    for (const o of q.options || []) parts.push(normaliseText(o.text));
  } else if (q.type === "sequence") {
    for (const i of q.items || []) parts.push(normaliseText(i.text));
  } else if (q.type === "matching") {
    for (const l of q.left || []) parts.push(normaliseText(l.text));
    for (const r of q.right || []) parts.push(normaliseText(r.text));
  } else if (q.type === "open") {
    parts.push(normaliseText(q.answer || ""));
  }
  return parts.filter(Boolean).join("|");
}

export function duplicateIssue(duplicateIds) {
  if (!duplicateIds || duplicateIds.length === 0) return null;
  return {
    level: "warn",
    code: "duplicate_statement",
    label: `Дубликат: такая же формулировка у ${duplicateIds.length} других вопрос(ов) (${duplicateIds.slice(0, 3).join(", ")}${duplicateIds.length > 3 ? "..." : ""})`,
  };
}

function normaliseText(s) {
  return (s || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function findDuplicateStrings(arr) {
  const seen = new Map();
  const dup = new Set();
  for (const v of arr) {
    if (!v) continue;
    if (seen.has(v)) dup.add(v);
    else seen.set(v, true);
  }
  return [...dup];
}
