import { defineStore } from "pinia";
import { useQuestionsStore, EXAM_TYPES } from "@/stores/questions";

const EXAM_DURATION_S = 90 * 60;

// Состав билета по официальной справке: всего 22 задания.
// — multi: 3 или 4 (выбирается случайно каждый запуск экзамена)
// — matching/sequence: 4 из общего пула
// — single: остальные (т.е. 14 или 15 в зависимости от multi)
// — open: 0 (по новой версии экзамена открытые задания не упоминались)
export const EXAM_TICKET = {
  total: 22,
  multiMin: 3,
  multiMax: 4,
  setCount: 4,
  openCount: 0,
};

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pickProportional(pool, types, total) {
  if (total <= 0) return [];
  const filtered = pool.filter((q) => types.includes(q.type));
  const byDisc = {};
  for (const q of filtered) {
    (byDisc[q.discipline_num] ||= []).push(q);
  }
  const out = [];
  const used = new Set();
  for (const d of shuffle(Object.keys(byDisc))) {
    if (out.length >= total) break;
    const list = shuffle(byDisc[d]);
    if (list.length > 0) {
      out.push(list[0]);
      used.add(list[0].id);
    }
  }
  const remaining = filtered.filter((q) => !used.has(q.id));
  for (const q of shuffle(remaining)) {
    if (out.length >= total) break;
    out.push(q);
    used.add(q.id);
  }
  return shuffle(out);
}

/**
 * Сборка экзаменационного билета по новому формату (22 задания):
 *   — multi:            EXAM_TICKET.multiMin..multiMax (случайно)
 *   — matching+sequence: EXAM_TICKET.setCount
 *   — open:              EXAM_TICKET.openCount
 *   — single:            добивается до EXAM_TICKET.total
 * Пропорционально по дисциплинам, где возможно.
 */
export function buildExamTicket(allQuestions) {
  const t = EXAM_TICKET;
  const multiCount =
    t.multiMin + Math.floor(Math.random() * (t.multiMax - t.multiMin + 1));
  const set    = pickProportional(allQuestions, ["matching", "sequence"], t.setCount);
  const multi  = pickProportional(allQuestions, ["multi"], multiCount);
  const open   = pickProportional(allQuestions, ["open"], t.openCount);
  const singleCount = Math.max(0, t.total - set.length - multi.length - open.length);
  const single = pickProportional(allQuestions, ["single"], singleCount);
  return [...single, ...multi, ...set, ...open];
}

export const useExamStore = defineStore("exam", {
  state: () => ({
    mode: null,
    questions: [],
    answers: {},
    selfGraded: {},
    index: 0,
    startedAt: 0,
    durationS: 0,
    finished: false,
    showFeedback: true,
    sourceLabel: "",
  }),
  getters: {
    current(state) {
      return state.questions[state.index] || null;
    },
    progress(state) {
      if (!state.questions.length) return 0;
      return Math.round(((state.index) / state.questions.length) * 100);
    },
    elapsedS(state) {
      if (!state.startedAt) return 0;
      return Math.floor((Date.now() - state.startedAt) / 1000);
    },
    remainingS(state) {
      if (!state.durationS) return Infinity;
      return Math.max(0, state.durationS - this.elapsedS);
    },
    isExam: (s) => s.mode === "exam",
  },
  actions: {
    startExam() {
      const qs = useQuestionsStore();
      const ticket = buildExamTicket(qs.all);
      this.$reset();
      this.mode = "exam";
      this.questions = ticket;
      this.startedAt = Date.now();
      this.durationS = EXAM_DURATION_S;
      this.showFeedback = false;
      this.sourceLabel = `Экзамен (${ticket.length} заданий, 90 минут)`;
    },

    startTraining(disciplineNum, types) {
      const qs = useQuestionsStore();
      // Открытые задания на экзамене не встречаются — выкидываем из тренировки,
      // даже если они каким-то образом окажутся в `types`.
      const effectiveTypes = (types && types.length ? types : EXAM_TYPES)
        .filter((t) => EXAM_TYPES.includes(t));
      let pool = qs.examPool;
      if (disciplineNum) {
        pool = pool.filter((q) => q.discipline_num === Number(disciplineNum));
      }
      pool = pool.filter((q) => effectiveTypes.includes(q.type));
      this.$reset();
      this.mode = "training";
      this.questions = shuffle(pool);
      this.startedAt = Date.now();
      this.durationS = 0;
      this.showFeedback = true;
      this.sourceLabel = disciplineNum
        ? `Тренировка: ${qs.byDiscipline[disciplineNum]?.name || ""}`
        : "Тренировка: все дисциплины";
    },

    startMistakes(ids) {
      const qs = useQuestionsStore();
      const pool = ids
        .map((id) => qs.byId[id])
        .filter((q) => q && EXAM_TYPES.includes(q.type));
      this.$reset();
      this.mode = "mistakes";
      this.questions = shuffle(pool);
      this.startedAt = Date.now();
      this.showFeedback = true;
      this.sourceLabel = `Работа над ошибками (${pool.length})`;
    },

    startSrs(ids) {
      const qs = useQuestionsStore();
      const pool = ids
        .map((id) => qs.byId[id])
        .filter((q) => q && EXAM_TYPES.includes(q.type));
      this.$reset();
      this.mode = "srs";
      this.questions = shuffle(pool);
      this.startedAt = Date.now();
      this.showFeedback = true;
      this.sourceLabel = `Повторение (${pool.length})`;
    },

    setAnswer(id, value) {
      this.answers[id] = value;
    },

    setSelfGrade(id, grade) {
      this.selfGraded[id] = grade;
    },

    next() {
      if (this.index < this.questions.length - 1) {
        this.index += 1;
      } else {
        this.finished = true;
      }
    },

    prev() {
      if (this.index > 0) this.index -= 1;
    },

    goTo(i) {
      if (i >= 0 && i < this.questions.length) this.index = i;
    },

    finish() {
      this.finished = true;
    },
  },
});
