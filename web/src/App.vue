<script setup>
import { computed } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { useSrsStore } from "@/stores/srs";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useTheme } from "@/composables/useTheme";

const srs = useSrsStore();
const qs = useQuestionsStore();
const progress = useProgressStore();
srs.load();

// Одноразовая миграция: убираем из локального стейта всё, что относится к
// открытым заданиям — их больше нет на экзамене, и держать по ним SRS-карточки
// или висящие «ошибки» бессмысленно.
srs.purgeNonExam();
progress.purgeIds((id) => qs.isExamQuestion(id));

// Бейдж в навбаре считаем по карточкам, которые реально пойдут на экзамен.
const dueExamCount = computed(
  () => srs.dueIds.filter((id) => qs.isExamQuestion(id)).length,
);

const { mode, cycle } = useTheme();

const themeIcon = computed(() => {
  if (mode.value === "dark") return "🌙";
  if (mode.value === "light") return "☀";
  return "🌓";
});
const themeLabel = computed(() => {
  if (mode.value === "dark") return "Тёмная";
  if (mode.value === "light") return "Светлая";
  return "Авто";
});
const themeTitle = computed(
  () => `Тема: ${themeLabel.value}. Клик переключит на следующую.`,
);
</script>

<template>
  <nav class="nav">
    <RouterLink to="/">Главная</RouterLink>
    <RouterLink to="/exam">Экзамен</RouterLink>
    <RouterLink to="/training">Тренировка</RouterLink>
    <RouterLink to="/srs">
      Повторения
      <span v-if="dueExamCount > 0" class="pill" style="margin-left: 4px;">{{ dueExamCount }}</span>
    </RouterLink>
    <RouterLink to="/mistakes">Ошибки</RouterLink>
    <RouterLink to="/browse">Каталог</RouterLink>
    <RouterLink to="/stats">Статистика</RouterLink>
    <button class="theme-toggle" :title="themeTitle" @click="cycle">
      <span class="icon">{{ themeIcon }}</span>
      <span>{{ themeLabel }}</span>
    </button>
  </nav>
  <main class="container">
    <RouterView />
  </main>
</template>
