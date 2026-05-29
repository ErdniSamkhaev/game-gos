import { defineStore } from "pinia";
import { useQuestionsStore } from "@/stores/questions";

const KEY = "game-gos:srs:v1";
const DAY = 86400000;

/**
 * Simplified SM-2 spaced repetition.
 *
 * Each card stores: interval (days), efactor (ease 1.3..2.5), reps,
 * dueAt (ms timestamp).
 *
 * Quality grades used by the UI map to:
 *   0 — "не знал"     -> reset, due tomorrow
 *   3 — "частично"    -> moderate progress
 *   5 — "знал точно"  -> full progress
 *
 * For closed/matching/sequence questions an automatic answer (correct/wrong)
 * is graded as 5 / 0 respectively.
 */
function review(card, q) {
  let { interval = 0, efactor = 2.5, reps = 0 } = card || {};
  if (q < 3) {
    // Не знал — карточка остаётся на сегодня и доступна к повторению сразу
    // (как в «Работе над ошибками»). Вперёд по интервалам уйдёт только после
    // правильного ответа.
    reps = 0;
    interval = 0;
    return {
      interval,
      efactor,
      reps,
      dueAt: Date.now(),
      lastQuality: q,
      lastReviewedAt: Date.now(),
    };
  }
  if (reps === 0) interval = 1;
  else if (reps === 1) interval = 3;
  else interval = Math.round(interval * efactor);
  reps += 1;
  efactor = Math.max(1.3, efactor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));
  const dueAt = Date.now() + interval * DAY;
  return { interval, efactor, reps, dueAt, lastQuality: q, lastReviewedAt: Date.now() };
}

export const useSrsStore = defineStore("srs", {
  state: () => ({
    cards: {},
  }),
  getters: {
    dueIds: (s) => {
      const now = Date.now();
      return Object.keys(s.cards).filter((id) => (s.cards[id]?.dueAt ?? 0) <= now);
    },
    dueCount() {
      return this.dueIds.length;
    },
    totalCards: (s) => Object.keys(s.cards).length,
  },
  actions: {
    load() {
      try {
        const raw = localStorage.getItem(KEY);
        if (raw) this.cards = JSON.parse(raw).cards || {};
      } catch (_) {}
    },
    persist() {
      try {
        localStorage.setItem(KEY, JSON.stringify({ cards: this.cards }));
      } catch (_) {}
    },
    grade(questionId, quality) {
      // Открытые задания на экзамене не встречаются, не плодим по ним карточки.
      const qs = useQuestionsStore();
      if (!qs.isExamQuestion(questionId)) return;
      const card = this.cards[questionId];
      this.cards[questionId] = review(card, quality);
      this.persist();
    },
    /** Auto-grade a closed/matching/sequence answer (correct vs wrong). */
    autoGrade(questionId, correct) {
      this.grade(questionId, correct ? 5 : 0);
    },
    forget(questionId) {
      delete this.cards[questionId];
      this.persist();
    },
    /** Удалить все карточки по неэкзаменационным заданиям (старые open). */
    purgeNonExam() {
      const qs = useQuestionsStore();
      let changed = false;
      for (const id of Object.keys(this.cards)) {
        if (!qs.isExamQuestion(id)) {
          delete this.cards[id];
          changed = true;
        }
      }
      if (changed) this.persist();
    },
  },
});
