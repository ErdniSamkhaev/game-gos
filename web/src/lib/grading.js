/**
 * Grading helpers. Each grader returns `{ correct, score, max, detail? }`.
 */

const SCORES = {
  single: 10,
  multi: 10,
  matching: 20,
  sequence: 20,
  open: 10,
};

function eqUnordered(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;
  const sa = [...a].sort();
  const sb = [...b].sort();
  return sa.every((v, i) => v === sb[i]);
}

function eqOrdered(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;
  return a.every((v, i) => v === b[i]);
}

export function maxScoreFor(type) {
  return SCORES[type] || 10;
}

export function gradeAnswer(question, userAnswer, selfGrade) {
  const max = maxScoreFor(question.type);
  switch (question.type) {
    case "single": {
      const correct = Array.isArray(userAnswer)
        && userAnswer.length === 1
        && userAnswer[0] === question.answer[0];
      return { correct, score: correct ? max : 0, max };
    }
    case "multi": {
      // Safety net: if the answer is a full permutation of all option keys
      // (same length, same set of letters, length >= 3), the question is
      // really a sequence that slipped past parser classification. Compare
      // with order in that case so any rearrangement counts as a mistake.
      const opts = (question.options || []).map((o) => o.key);
      const ans = question.answer || [];
      const isSequenceInDisguise =
        Array.isArray(ans)
        && ans.length >= 3
        && opts.length === ans.length
        && new Set(ans).size === ans.length
        && opts.every((k) => ans.includes(k));
      const correct = isSequenceInDisguise
        ? eqOrdered(userAnswer || [], ans)
        : eqUnordered(userAnswer || [], ans);
      return { correct, score: correct ? max : 0, max };
    }
    case "matching": {
      const ans = question.answer || {};
      const ua = userAnswer || {};
      const total = Object.keys(ans).length || 1;
      let hit = 0;
      for (const k of Object.keys(ans)) {
        if (ua[k] && ua[k] === ans[k]) hit += 1;
      }
      const score = Math.round((hit / total) * max);
      return { correct: hit === total, score, max, detail: { hit, total } };
    }
    case "sequence": {
      const ans = question.answer || [];
      const ua = userAnswer || [];
      const total = ans.length || 1;
      let hit = 0;
      for (let i = 0; i < total; i++) {
        if (ua[i] && ua[i] === ans[i]) hit += 1;
      }
      const score = Math.round((hit / total) * max);
      return { correct: hit === total, score, max, detail: { hit, total } };
    }
    case "open": {
      // 0 = "не знал", 1 = "частично", 2 = "знал"
      const sg = Number.isFinite(selfGrade) ? selfGrade : null;
      if (sg === null) return { correct: false, score: 0, max, pending: true };
      const map = { 0: 0, 1: Math.round(max / 2), 2: max };
      const score = map[sg] ?? 0;
      return { correct: sg === 2, score, max, selfGrade: sg };
    }
    default:
      return { correct: false, score: 0, max };
  }
}
