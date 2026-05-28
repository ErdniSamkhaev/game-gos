<script setup>
import { computed, ref } from "vue";
import { useExamStore } from "@/stores/exam";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";
import { gradeAnswer } from "@/lib/grading";
import QuestionRenderer from "@/components/QuestionRenderer.vue";
import ProgressDots from "@/components/ProgressDots.vue";

const exam = useExamStore();
const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();

const setupOpen = ref(true);
const checked = ref(false);

// SRS-карточки, оставшиеся в localStorage от старых открытых заданий,
// больше не нужны (их нет на экзамене). Фильтруем их и здесь, и при старте.
const dueExamIds = computed(() =>
  srs.dueIds.filter((id) => qs.isExamQuestion(id)),
);
const totalExamCards = computed(
  () => Object.keys(srs.cards).filter((id) => qs.isExamQuestion(id)).length,
);

function start() {
  if (dueExamIds.value.length === 0) return;
  exam.startSrs(dueExamIds.value);
  setupOpen.value = false;
  checked.value = false;
}

const currentAnswer = computed({
  get: () => exam.answers[exam.current?.id],
  set: (v) => exam.setAnswer(exam.current.id, v),
});
const currentSelfGrade = computed({
  get: () => exam.selfGraded[exam.current?.id] ?? null,
  set: (v) => exam.setSelfGrade(exam.current.id, v),
});
const grade = computed(() => {
  if (!checked.value || !exam.current) return null;
  return gradeAnswer(exam.current, exam.answers[exam.current.id], exam.selfGraded[exam.current.id]);
});

const currentMistakeCount = computed(() =>
  exam.current ? progress.mistakeCount(exam.current.id) : 0,
);

function check() {
  const q = exam.current;
  if (!q) return;
  if (q.type === "open" && (exam.selfGraded[q.id] === undefined || exam.selfGraded[q.id] === null)) return;
  checked.value = true;
  const g = gradeAnswer(q, exam.answers[q.id], exam.selfGraded[q.id]);
  progress.recordAnswer(q.id, g.correct, g.score, g.max);
  if (q.type === "open") {
    const map = { 0: 0, 1: 3, 2: 5 };
    srs.grade(q.id, map[exam.selfGraded[q.id]] ?? 0);
  } else {
    srs.autoGrade(q.id, g.correct);
  }
}

function next() {
  checked.value = false;
  exam.next();
}

function back() {
  setupOpen.value = true;
  exam.$reset();
}

function formatCorrect(q) {
  if (q.type === "single") return q.answer.join("");
  if (q.type === "multi") return q.answer.join(", ");
  if (q.type === "matching") {
    return Object.entries(q.answer).map(([k, v]) => `${k}-${v}`).join(", ");
  }
  if (q.type === "sequence") return q.answer.join(" → ");
  return q.answer;
}
</script>

<template>
  <div v-if="setupOpen">
    <h1>Интервальное повторение</h1>
    <p class="muted">
      После каждого вопроса вы ставите оценку «не знал / частично / знал точно».
      По алгоритму SM-2 вопрос вернётся через 1, 3, 7, 14, 30+ дней — это самый
      эффективный способ запомнить материал к экзамену.
    </p>
    <div class="card">
      <div class="row between wrap">
        <div>
          <div class="muted" style="font-size: 13px;">К повторению сегодня</div>
          <div style="font-size: 40px; font-weight: 700;">{{ dueExamIds.length }}</div>
        </div>
        <div>
          <div class="muted" style="font-size: 13px;">Всего карточек в SRS</div>
          <div style="font-size: 40px; font-weight: 700;">{{ totalExamCards }}</div>
        </div>
      </div>
      <button class="btn primary" :disabled="dueExamIds.length === 0" @click="start">
        {{ dueExamIds.length === 0 ? 'Сегодня всё повторено' : 'Начать повторение' }}
      </button>
      <p v-if="totalExamCards === 0" class="muted" style="margin-top: 12px;">
        Карточки появятся после первых ответов в любом режиме.
      </p>
    </div>
  </div>

  <div v-else-if="exam.finished">
    <h1>Сессия завершена</h1>
    <p>Все карточки на сегодня повторены. Возвращайтесь завтра!</p>
    <div class="btn-row">
      <button class="btn primary" @click="back">К SRS</button>
      <RouterLink to="/" class="btn">На главную</RouterLink>
    </div>
  </div>

  <div v-else-if="exam.current">
    <div class="row between wrap" style="margin-bottom: 12px;">
      <div>
        <div class="muted" style="font-size: 13px;">{{ exam.sourceLabel }}</div>
        <div style="font-weight: 600;">{{ exam.index + 1 }} из {{ exam.questions.length }}</div>
      </div>
      <button class="btn" @click="back">Закрыть</button>
    </div>

    <ProgressDots :total="exam.questions.length" :index="exam.index" style="margin-bottom: 16px;" />

    <div class="card">
      <QuestionRenderer
        :key="exam.current.id"
        :question="exam.current"
        :answer="currentAnswer"
        :self-grade="currentSelfGrade"
        :show-feedback="checked"
        :locked="checked"
        :mistake-count="currentMistakeCount"
        @update:answer="currentAnswer = $event"
        @update:self-grade="currentSelfGrade = $event"
      />
    </div>

    <div v-if="grade" class="card" :style="{ borderColor: grade.correct ? 'var(--success)' : 'var(--error)' }">
      <strong v-if="grade.correct" class="success">✓ Правильно! +{{ grade.score }}</strong>
      <strong v-else-if="grade.detail" class="warning">
        Частично: {{ grade.detail.hit }} из {{ grade.detail.total }}
      </strong>
      <strong v-else class="error">✗ Неправильно</strong>
      <div v-if="exam.current.type !== 'open'" class="muted" style="margin-top: 4px; font-size: 13px;">
        Правильный ответ: {{ formatCorrect(exam.current) }}
      </div>
    </div>

    <div class="row between" style="margin-top: 12px;">
      <button v-if="!checked" class="btn primary" @click="check">Проверить</button>
      <button v-else class="btn primary" @click="next">
        {{ exam.index < exam.questions.length - 1 ? 'Следующий →' : 'Завершить' }}
      </button>
    </div>
  </div>
</template>
