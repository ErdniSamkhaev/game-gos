<script setup>
import { computed } from "vue";
import { useExamStore } from "@/stores/exam";
import { gradeAnswer } from "@/lib/grading";
import QuestionRenderer from "@/components/QuestionRenderer.vue";

const exam = useExamStore();

const breakdown = computed(() => {
  return exam.questions.map((q) => ({
    question: q,
    grade: gradeAnswer(q, exam.answers[q.id], exam.selfGraded[q.id]),
    userAnswer: exam.answers[q.id],
    selfGrade: exam.selfGraded[q.id],
  }));
});

const totals = computed(() => {
  let score = 0;
  let max = 0;
  let correct = 0;
  for (const b of breakdown.value) {
    score += b.grade.score;
    max += b.grade.max;
    if (b.grade.correct) correct += 1;
  }
  return { score, max, correct, total: breakdown.value.length };
});

const percent = computed(() => {
  if (!totals.value.max) return 0;
  return Math.round((totals.value.score / totals.value.max) * 100);
});

const grade5 = computed(() => {
  const p = percent.value;
  if (p >= 86) return { label: "Отлично", cls: "success" };
  if (p >= 70) return { label: "Хорошо", cls: "primary" };
  if (p >= 55) return { label: "Удовлетворительно", cls: "warning" };
  return { label: "Неудовлетворительно", cls: "error" };
});

function restart() {
  exam.startExam();
  window.location.hash = "#/exam";
}
</script>

<template>
  <h1>Результаты экзамена</h1>

  <div class="card">
    <div class="score-big">{{ totals.score }} / {{ totals.max }}</div>
    <div class="row" style="justify-content: center; gap: 24px;">
      <div style="text-align: center;">
        <div class="muted" style="font-size: 13px;">Процент</div>
        <div style="font-size: 24px; font-weight: 600;">{{ percent }}%</div>
      </div>
      <div style="text-align: center;">
        <div class="muted" style="font-size: 13px;">Полностью верно</div>
        <div style="font-size: 24px; font-weight: 600;">{{ totals.correct }} / {{ totals.total }}</div>
      </div>
      <div style="text-align: center;">
        <div class="muted" style="font-size: 13px;">Оценка</div>
        <div :class="['pill', grade5.cls]" style="font-size: 18px; padding: 4px 12px;">
          {{ grade5.label }}
        </div>
      </div>
    </div>
    <div class="btn-row" style="justify-content: center; margin-top: 20px;">
      <button class="btn primary" @click="restart">Сдать ещё раз</button>
      <RouterLink to="/" class="btn">На главную</RouterLink>
      <RouterLink to="/stats" class="btn">К статистике</RouterLink>
    </div>
  </div>

  <h2>Разбор заданий</h2>
  <div v-for="(b, i) in breakdown" :key="b.question.id" class="card">
    <div class="row between">
      <div>
        <strong>Задание {{ i + 1 }}.</strong>
        <span :class="['pill', b.question.type]" style="margin-left: 8px;">{{ b.question.type }}</span>
      </div>
      <div>
        <strong v-if="b.grade.correct" class="success">+{{ b.grade.score }} / {{ b.grade.max }}</strong>
        <strong v-else-if="b.grade.score > 0" class="warning">+{{ b.grade.score }} / {{ b.grade.max }}</strong>
        <strong v-else class="error">0 / {{ b.grade.max }}</strong>
      </div>
    </div>
    <div style="margin-top: 12px;">
      <QuestionRenderer
        :question="b.question"
        :answer="b.userAnswer"
        :self-grade="b.selfGrade"
        :show-feedback="true"
        :locked="true"
      />
    </div>
  </div>
</template>
