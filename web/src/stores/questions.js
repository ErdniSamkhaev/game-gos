import { defineStore } from "pinia";
import questionsRaw from "@data/questions.json";

export const useQuestionsStore = defineStore("questions", {
  state: () => ({
    all: questionsRaw,
  }),
  getters: {
    byId: (s) => Object.fromEntries(s.all.map((q) => [q.id, q])),

    byType: (s) => {
      const out = { single: [], multi: [], matching: [], sequence: [], open: [] };
      for (const q of s.all) {
        if (out[q.type]) out[q.type].push(q);
      }
      return out;
    },

    byDiscipline: (s) => {
      const out = {};
      for (const q of s.all) {
        const k = q.discipline_num;
        if (!out[k]) {
          out[k] = { num: k, name: q.discipline_name, questions: [] };
        }
        out[k].questions.push(q);
      }
      return out;
    },

    disciplines: (s) => {
      const map = {};
      for (const q of s.all) {
        if (!map[q.discipline_num]) {
          map[q.discipline_num] = { num: q.discipline_num, name: q.discipline_name, count: 0 };
        }
        map[q.discipline_num].count++;
      }
      return Object.values(map).sort((a, b) => a.num - b.num);
    },
  },
});
