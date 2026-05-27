import { defineStore } from "pinia";

const KEY = "game-gos:progress:v1";

function loadInitial() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return {
    answeredCorrect: {},
    answeredWrong: {},
    totalCorrect: 0,
    totalWrong: 0,
    totalScore: 0,
    bestExamScore: 0,
    examHistory: [],
    streakDays: 0,
    lastActiveDay: null,
  };
}

export const useProgressStore = defineStore("progress", {
  state: () => loadInitial(),
  getters: {
    isCorrect: (s) => (id) => Boolean(s.answeredCorrect[id]),
    isWrong:   (s) => (id) => Boolean(s.answeredWrong[id]),
    mistakeIds:(s) => Object.keys(s.answeredWrong),
    knownIds:  (s) => Object.keys(s.answeredCorrect),
  },
  actions: {
    persist() {
      try {
        localStorage.setItem(KEY, JSON.stringify(this.$state));
      } catch (_) {}
    },

    bumpStreak() {
      const today = new Date().toISOString().slice(0, 10);
      if (this.lastActiveDay === today) return;
      const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      if (this.lastActiveDay === yesterday) {
        this.streakDays += 1;
      } else {
        this.streakDays = 1;
      }
      this.lastActiveDay = today;
      this.persist();
    },

    recordAnswer(questionId, correct, score = 0) {
      this.bumpStreak();
      if (correct) {
        this.answeredCorrect[questionId] = Date.now();
        delete this.answeredWrong[questionId];
        this.totalCorrect += 1;
      } else {
        this.answeredWrong[questionId] = Date.now();
        this.totalWrong += 1;
      }
      this.totalScore += score;
      this.persist();
    },

    recordExam(result) {
      this.examHistory.push({
        ts: Date.now(),
        score: result.score,
        max: result.max,
        breakdown: result.breakdown,
      });
      if (result.score > this.bestExamScore) {
        this.bestExamScore = result.score;
      }
      this.persist();
    },

    clearMistake(id) {
      delete this.answeredWrong[id];
      this.persist();
    },

    reset() {
      Object.assign(this.$state, {
        answeredCorrect: {},
        answeredWrong: {},
        totalCorrect: 0,
        totalWrong: 0,
        totalScore: 0,
        bestExamScore: 0,
        examHistory: [],
        streakDays: 0,
        lastActiveDay: null,
      });
      this.persist();
    },
  },
});
