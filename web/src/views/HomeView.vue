<script setup>
import { computed } from "vue";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";

const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();

const totalQ = computed(() => qs.all.length);
const examTotal = computed(() => qs.examPool.length);
const knownPct = computed(() => {
  if (!examTotal.value) return 0;
  const knownExam = Object.keys(progress.answeredCorrect)
    .filter((id) => qs.isExamQuestion(id)).length;
  return Math.round((knownExam / examTotal.value) * 100);
});
const dueExamCount = computed(
  () => srs.dueIds.filter((id) => qs.isExamQuestion(id)).length,
);
const examMistakesCount = computed(
  () => progress.mistakeIds.filter((id) => qs.isExamQuestion(id)).length,
);
</script>

<template>
  <div class="card hero">
    <span class="hero-badge">Подготовка к госэкзамену</span>
    <h1 class="hero-title">Тренажёр ГОСов</h1>
    <p class="hero-sub">
      Направление подготовки: <strong>09.03.02 Информационные системы и технологии</strong>
    </p>
    <p class="hero-desc">
      Тренажёр для подготовки к государственному экзамену. Программа случайным
      образом собирает <strong>22 вопроса</strong> из пяти основных дисциплин.
    </p>

    <div class="feature-list">
      <div class="feature">
        <span class="feature-ico">✨</span>
        <span class="feature-txt"><b>22 случайных вопроса</b> без открытых заданий, без повторов внутри билета</span>
      </div>
      <div class="feature">
        <span class="feature-ico">✅</span>
        <span class="feature-txt"><b>Таймер 90 минут</b> и итог с разбором — как на реальном экзамене</span>
      </div>
      <div class="feature">
        <span class="feature-ico">🔁</span>
        <span class="feature-txt"><b>Работа над ошибками и SM-2</b> — повторяете слабые места, пока не закрепите</span>
      </div>
      <div class="feature">
        <span class="feature-ico">💾</span>
        <span class="feature-txt"><b>Прогресс сохраняется</b> в браузере — можно продолжить в любой момент</span>
      </div>
    </div>

    <div class="btn-row" style="justify-content: center;">
      <RouterLink to="/exam" class="btn primary lg">▶ Начать экзамен</RouterLink>
      <RouterLink to="/training" class="btn lg">Тренировка</RouterLink>
      <RouterLink to="/browse" class="btn lg">Шпаргалка</RouterLink>
    </div>
  </div>

  <div class="card">
    <div class="stat-grid">
      <div class="stat-tile">
        <div class="label">Заданий для экзамена</div>
        <div class="value">{{ examTotal }}</div>
      </div>
      <div class="stat-tile">
        <div class="label">Освоено</div>
        <div class="value">{{ knownPct }}%</div>
      </div>
      <div class="stat-tile">
        <div class="label">К повторению</div>
        <div class="value">{{ dueExamCount }}</div>
      </div>
      <div class="stat-tile">
        <div class="label">Серия дней</div>
        <div class="value">{{ progress.streakDays }}</div>
      </div>
      <div class="stat-tile">
        <div class="label">Лучший экзамен</div>
        <div class="value">{{ progress.bestExamScore }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Режимы</h2>

    <RouterLink to="/exam" class="mode-card">
      <span class="mode-ico">📝</span>
      <span class="mode-body">
        <span class="mode-title">Экзамен</span>
        <span class="mode-desc">22 задания, таймер 90 минут, итог и разбор в конце</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>

    <RouterLink to="/training" class="mode-card">
      <span class="mode-ico">🎯</span>
      <span class="mode-body">
        <span class="mode-title">Тренировка</span>
        <span class="mode-desc">По дисциплинам, без таймера, с мгновенной проверкой и подсказками</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>

    <RouterLink to="/srs" class="mode-card">
      <span class="mode-ico">🔁</span>
      <span class="mode-body">
        <span class="mode-title">
          Повторения
          <span v-if="dueExamCount > 0" class="pill matching">{{ dueExamCount }}</span>
        </span>
        <span class="mode-desc">Интервальное повторение (SM-2) — лучший способ удержать в памяти</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>

    <RouterLink to="/mistakes" class="mode-card">
      <span class="mode-ico">🛠️</span>
      <span class="mode-body">
        <span class="mode-title">
          Работа над ошибками
          <span v-if="examMistakesCount" class="pill error">{{ examMistakesCount }}</span>
        </span>
        <span class="mode-desc">Только те вопросы, в которых вы ошибались</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>

    <RouterLink to="/browse" class="mode-card">
      <span class="mode-ico">📚</span>
      <span class="mode-body">
        <span class="mode-title">Каталог (шпаргалка)</span>
        <span class="mode-desc">Все {{ totalQ }} вопросов с фильтрами и поиском</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>

    <RouterLink to="/stats" class="mode-card">
      <span class="mode-ico">📊</span>
      <span class="mode-body">
        <span class="mode-title">Статистика</span>
        <span class="mode-desc">Прогресс по дисциплинам и история экзаменов</span>
      </span>
      <span class="mode-arrow">→</span>
    </RouterLink>
  </div>

  <div class="card">
    <h2>Дисциплины</h2>
    <p class="muted" style="font-size: 13px; margin-top: 0;">
      Количество — задания, которые могут попасться на экзамене (открытые исключены).
    </p>
    <ol style="padding-left: 20px;">
      <li v-for="d in qs.examDisciplines" :key="d.num" style="margin: 4px 0;">
        <strong>{{ d.name }}</strong>
        <span class="muted" style="font-size: 13px;"> · {{ d.count }} заданий</span>
      </li>
    </ol>
  </div>
</template>
