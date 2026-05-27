<script setup>
import { computed } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { useSrsStore } from "@/stores/srs";
import { useTheme } from "@/composables/useTheme";

const srs = useSrsStore();
srs.load();

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
      <span v-if="srs.dueCount > 0" class="pill" style="margin-left: 4px;">{{ srs.dueCount }}</span>
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
