import { defineStore } from "pinia";
import questionsRaw from "@data/questions.json";

// На реальном экзамене открытых заданий точно не будет, поэтому из всех
// режимов практики (Тренировка, SRS, Работа над ошибками) они исключены.
// Сами данные мы храним и показываем в Каталоге — но в учёбу не тянем.
export const EXAM_TYPES = ["single", "multi", "matching", "sequence"];

export const useQuestionsStore = defineStore("questions", {
  state: () => ({
    all: questionsRaw,
  }),
  getters: {
    byId: (s) => Object.fromEntries(s.all.map((q) => [q.id, q])),

    // Всё, что реально может попасться на экзамене (без open).
    examPool: (s) => s.all.filter((q) => EXAM_TYPES.includes(q.type)),

    isExamQuestion() {
      return (id) => {
        const q = this.byId[id];
        return Boolean(q && EXAM_TYPES.includes(q.type));
      };
    },

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

    // То же, что disciplines, но считает только экзаменационные задания
    // (без open). Используется на главной и в тренировке, где open не нужны.
    examDisciplines() {
      const map = {};
      for (const q of this.examPool) {
        if (!map[q.discipline_num]) {
          map[q.discipline_num] = { num: q.discipline_num, name: q.discipline_name, count: 0 };
        }
        map[q.discipline_num].count++;
      }
      return Object.values(map).sort((a, b) => a.num - b.num);
    },
  },
});
