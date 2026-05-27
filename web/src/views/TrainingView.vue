<script setup>
import { computed, ref } from "vue";
import { useExamStore } from "@/stores/exam";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";
import { gradeAnswer } from "@/lib/grading";
import QuestionRenderer from "@/components/QuestionRenderer.vue";

const exam = useExamStore();
const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();

const setupOpen = ref(true);
const selectedDiscipline = ref(null);
const selectedTypes = ref(["single", "multi", "matching", "sequence", "open"]);
const checked = ref(false);

const ALL_TYPES = [
  { id: "single", label: "Закрытые (один ответ)" },
  { id: "multi", label: "Закрытые (несколько)" },
  { id: "matching", label: "Соответствие" },
  { id: "sequence", label: "Последовательность" },
  { id: "open", label: "Открытые" },
];

function start() {
  exam.startTraining(selectedDiscipline.value, selectedTypes.value);
  setupOpen.value = false;
  checked.value = false;
}

function toggleType(t) {
  const i = selectedTypes.value.indexOf(t);
  if (i >= 0) selectedTypes.value.splice(i, 1);
  else selectedTypes.value.push(t);
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

function check() {
  const q = exam.current;
  if (!q) return;
  if (q.type === "open") {
    const sg = exam.selfGraded[q.id];
    if (sg === undefined || sg === null) return;
  }
  checked.value = true;
  const g = gradeAnswer(q, exam.answers[q.id], exam.selfGraded[q.id]);
  progress.recordAnswer(q.id, g.correct, g.score);
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

const totalCount = computed(() => {
  let pool = qs.all;
  if (selectedDiscipline.value) {
    pool = pool.filter(q => q.discipline_num === Number(selectedDiscipline.value));
  }
  if (selectedTypes.value.length) {
    pool = pool.filter(q => selectedTypes.value.includes(q.type));
  }
  return pool.length;
});

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
    <h1>Тренировка</h1>
    <div class="card">
      <h3>Дисциплина</h3>
      <div class="tabs">
        <span :class="['tab', selectedDiscipline === null ? 'active' : '']" @click="selectedDiscipline = null">
          Все
        </span>
        <span
          v-for="d in qs.disciplines"
          :key="d.num"
          :class="['tab', selectedDiscipline === d.num ? 'active' : '']"
          @click="selectedDiscipline = d.num"
        >
          {{ d.num }}. {{ d.name }} ({{ d.count }})
        </span>
      </div>

      <h3>Типы заданий</h3>
      <div class="tabs">
        <span
          v-for="t in ALL_TYPES"
          :key="t.id"
          :class="['tab', selectedTypes.includes(t.id) ? 'active' : '']"
          @click="toggleType(t.id)"
        >
          {{ t.label }}
        </span>
      </div>

      <p class="muted" style="margin-top: 12px;">В подборке: {{ totalCount }} вопросов</p>
      <button class="btn primary" :disabled="totalCount === 0" @click="start">Начать</button>
    </div>
  </div>

  <div v-else-if="exam.finished">
    <h1>Тренировка завершена</h1>
    <p class="muted">Все {{ exam.questions.length }} вопросов разобраны.</p>
    <div class="btn-row">
      <button class="btn primary" @click="back">К настройкам</button>
      <RouterLink to="/" class="btn">На главную</RouterLink>
    </div>
  </div>

  <div v-else-if="exam.current">
    <div class="row between wrap" style="margin-bottom: 12px;">
      <div>
        <div class="muted" style="font-size: 13px;">{{ exam.sourceLabel }}</div>
        <div style="font-weight: 600;">{{ exam.index + 1 }} из {{ exam.questions.length }}</div>
      </div>
      <button class="btn" @click="back">К настройкам</button>
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
        :show-feedback="checked"
        :locked="checked"
        @update:answer="currentAnswer = $event"
        @update:self-grade="currentSelfGrade = $event"
      />
    </div>

    <div v-if="grade" class="card" :style="{ borderColor: grade.correct ? 'var(--success)' : 'var(--error)' }">
      <strong v-if="grade.correct" class="success">✓ Правильно! +{{ grade.score }}</strong>
      <strong v-else-if="grade.detail" class="warning">
        Частично: {{ grade.detail.hit }} из {{ grade.detail.total }} (+{{ grade.score }})
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
