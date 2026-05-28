<script setup>
import { computed } from "vue";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";

const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();

const perDiscipline = computed(() => {
  const map = {};
  // Считаем только по тем заданиям, которые реально будут на экзамене.
  for (const q of qs.examPool) {
    const k = q.discipline_num;
    if (!map[k]) {
      map[k] = { num: k, name: q.discipline_name, total: 0, correct: 0, wrong: 0 };
    }
    map[k].total += 1;
    if (progress.answeredCorrect[q.id]) map[k].correct += 1;
    if (progress.answeredWrong[q.id]) map[k].wrong += 1;
  }
  return Object.values(map).sort((a, b) => a.num - b.num);
});

const examHistory = computed(() =>
  [...progress.examHistory].sort((a, b) => b.ts - a.ts).slice(0, 10)
);

function fmtDate(ts) {
  return new Date(ts).toLocaleString("ru-RU");
}

function reset() {
  if (!confirm("Сбросить весь прогресс и SRS? Это действие нельзя отменить.")) return;
  progress.reset();
  for (const id of Object.keys(srs.cards)) srs.forget(id);
}
</script>

<template>
  <h1>Статистика</h1>

  <div class="card">
    <h2>Общие показатели</h2>
    <div class="row wrap" style="gap: 32px;">
      <div>
        <div class="muted" style="font-size: 13px;">Правильных ответов</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.totalCorrect }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Ошибок</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.totalWrong }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Очки</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.totalScore }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Лучший экзамен</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.bestExamScore }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Серия дней</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.streakDays }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>По дисциплинам</h2>
    <div v-for="d in perDiscipline" :key="d.num" style="margin-bottom: 12px;">
      <div class="row between">
        <div>
          <strong>{{ d.num }}. {{ d.name }}</strong>
          <span class="muted" style="font-size: 13px;">
            · {{ d.correct }}/{{ d.total }} освоено
            <span v-if="d.wrong > 0">· {{ d.wrong }} ошибок</span>
          </span>
        </div>
        <div>{{ Math.round((d.correct / d.total) * 100) }}%</div>
      </div>
      <div class="bar" style="margin-top: 4px;">
        <div class="bar-fill" :style="{ width: (d.correct / d.total * 100) + '%' }"></div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Последние экзамены</h2>
    <div v-if="examHistory.length === 0" class="muted">Пока нет завершённых экзаменов.</div>
    <table v-else style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="text-align: left; border-bottom: 1px solid var(--border);">
          <th style="padding: 6px 0;">Дата</th>
          <th>Результат</th>
          <th>%</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(e, i) in examHistory" :key="i" style="border-bottom: 1px solid var(--border);">
          <td style="padding: 6px 0;">{{ fmtDate(e.ts) }}</td>
          <td>{{ e.score }} / {{ e.max }}</td>
          <td>{{ Math.round((e.score / e.max) * 100) }}%</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Сброс</h2>
    <p class="muted">Удалит весь локальный прогресс, SRS-карточки и историю экзаменов.</p>
    <button class="btn error" @click="reset">Сбросить всё</button>
  </div>
</template>
