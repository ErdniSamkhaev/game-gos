<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useExamStore } from "@/stores/exam";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";
import { gradeAnswer, maxScoreFor } from "@/lib/grading";
import QuestionRenderer from "@/components/QuestionRenderer.vue";
import Timer from "@/components/Timer.vue";

const exam = useExamStore();
const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();
const router = useRouter();

const showSelfGradeModal = ref(false);

onMounted(() => {
  if (exam.mode !== "exam" || !exam.questions.length) {
    exam.startExam();
  }
});

const currentAnswer = computed({
  get: () => exam.answers[exam.current?.id],
  set: (v) => exam.setAnswer(exam.current.id, v),
});
const currentSelfGrade = computed({
  get: () => exam.selfGraded[exam.current?.id] ?? null,
  set: (v) => exam.setSelfGrade(exam.current.id, v),
});
const currentMistakeCount = computed(() =>
  exam.current ? progress.mistakeCount(exam.current.id) : 0,
);

const ticketSummary = computed(() => {
  const counts = { closed: 0, set: 0, open: 0 };
  for (const q of exam.questions) {
    if (q.type === "single" || q.type === "multi") counts.closed += 1;
    else if (q.type === "matching" || q.type === "sequence") counts.set += 1;
    else if (q.type === "open") counts.open += 1;
  }
  return counts;
});

function finish() {
  // For exam mode, all open questions need self-grading. If not yet graded,
  // ask user to grade pending ones first.
  const ungradedOpen = exam.questions.find(
    (q) => q.type === "open" && exam.selfGraded[q.id] === undefined
  );
  if (ungradedOpen) {
    showSelfGradeModal.value = true;
    return;
  }
  finalize();
}

function finalize() {
  const breakdown = exam.questions.map((q) => {
    const grade = gradeAnswer(q, exam.answers[q.id], exam.selfGraded[q.id]);
    progress.recordAnswer(q.id, grade.correct, grade.score, grade.max);
    if (q.type !== "open") {
      srs.autoGrade(q.id, grade.correct);
    } else {
      const sg = exam.selfGraded[q.id];
      const map = { 0: 0, 1: 3, 2: 5 };
      srs.grade(q.id, map[sg] ?? 0);
    }
    return { question: q, ...grade, userAnswer: exam.answers[q.id], selfGrade: exam.selfGraded[q.id] };
  });
  const total = breakdown.reduce((acc, b) => acc + b.score, 0);
  const max = breakdown.reduce((acc, b) => acc + b.max, 0);
  progress.recordExam({ score: total, max, breakdown: breakdown.map(b => ({ id: b.question.id, score: b.score, max: b.max })) });

  // Hand off result via store
  exam.$patch({ finished: true });
  router.push({ name: "result" });
}

function gradePending(id, grade) {
  exam.setSelfGrade(id, grade);
}

const pendingOpen = computed(() =>
  exam.questions.filter((q) => q.type === "open" && exam.selfGraded[q.id] === undefined)
);

function gradeAllAndFinalize() {
  for (const q of pendingOpen.value) {
    if (exam.selfGraded[q.id] === undefined) exam.setSelfGrade(q.id, 0);
  }
  showSelfGradeModal.value = false;
  finalize();
}
</script>

<template>
  <div v-if="!exam.current">
    <p>Загрузка...</p>
  </div>
  <div v-else>
    <div class="row between wrap" style="margin-bottom: 12px;">
      <div>
        <div class="muted" style="font-size: 13px;">{{ exam.sourceLabel }}</div>
        <div style="font-weight: 600;">
          Задание {{ exam.index + 1 }} из {{ exam.questions.length }}
        </div>
      </div>
      <Timer
        v-if="exam.durationS > 0"
        :duration-s="exam.durationS"
        :started-at="exam.startedAt"
        @expire="finalize"
      />
    </div>

    <div class="bar" style="margin-bottom: 16px;">
      <div class="bar-fill" :style="{ width: ((exam.index + 1) / exam.questions.length * 100) + '%' }"></div>
    </div>

    <div class="card">
      <QuestionRenderer
        :key="exam.current.id"
        :question="exam.current"
        :answer="currentAnswer"
        :self-grade="currentSelfGrade"
        :show-feedback="false"
        :mistake-count="currentMistakeCount"
        @update:answer="currentAnswer = $event"
        @update:self-grade="currentSelfGrade = $event"
      />
    </div>

    <div class="row between wrap">
      <button class="btn" :disabled="exam.index === 0" @click="exam.prev()">← Назад</button>
      <div class="muted" style="font-size: 13px;">
        Закрытых: {{ ticketSummary.closed }} ·
        Соответствие: {{ ticketSummary.set }} ·
        Открытых: {{ ticketSummary.open }}
      </div>
      <button
        v-if="exam.index < exam.questions.length - 1"
        class="btn primary"
        @click="exam.next()"
      >
        Далее →
      </button>
      <button v-else class="btn success" @click="finish">Завершить экзамен</button>
    </div>

    <div v-if="showSelfGradeModal" class="card" style="margin-top: 16px; border-color: var(--warning);">
      <h3>Оцените открытые задания</h3>
      <p class="muted">
        В реальном экзамене открытые задания оценивает комиссия. Сравните свой ответ с эталоном
        и поставьте честную оценку.
      </p>
      <div v-for="q in pendingOpen" :key="q.id" class="card" style="margin: 8px 0;">
        <div class="muted" style="font-size: 13px;">{{ q.discipline_name }}</div>
        <div style="margin: 6px 0; font-weight: 500;">{{ q.statement }}</div>
        <div class="card" style="background: var(--code-bg); padding: 10px;">
          <div class="muted" style="font-size: 13px;">Ваш ответ:</div>
          <div style="white-space: pre-wrap;">{{ exam.answers[q.id] || '—' }}</div>
          <div class="muted" style="font-size: 13px; margin-top: 6px;">Эталон:</div>
          <div style="white-space: pre-wrap;">{{ q.answer }}</div>
        </div>
        <div class="btn-row" style="margin-top: 8px;">
          <button class="btn error" @click="gradePending(q.id, 0)">Не знал</button>
          <button class="btn warning" @click="gradePending(q.id, 1)">Частично</button>
          <button class="btn success" @click="gradePending(q.id, 2)">Знал точно</button>
        </div>
      </div>
      <div class="btn-row" style="margin-top: 12px;">
        <button class="btn primary" @click="finalize" :disabled="pendingOpen.length > 0">
          Подвести итоги
        </button>
        <button class="btn" @click="gradeAllAndFinalize">
          Все оставшиеся = «Не знал»
        </button>
      </div>
    </div>
  </div>
</template>
