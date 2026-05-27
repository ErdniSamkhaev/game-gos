<script setup>
import { computed } from "vue";
import { useQuestionsStore } from "@/stores/questions";
import { useProgressStore } from "@/stores/progress";
import { useSrsStore } from "@/stores/srs";

const qs = useQuestionsStore();
const progress = useProgressStore();
const srs = useSrsStore();

const totalQ = computed(() => qs.all.length);
const knownPct = computed(() => {
  if (!totalQ.value) return 0;
  return Math.round((Object.keys(progress.answeredCorrect).length / totalQ.value) * 100);
});
</script>

<template>
  <h1>Тренажёр ГОСов · 09.03.02</h1>
  <p class="muted">
    Разработка, сопровождение и обеспечение безопасности информационных систем
  </p>

  <div class="card">
    <div class="row between wrap">
      <div>
        <div class="muted" style="font-size: 13px;">Всего вопросов в базе</div>
        <div style="font-size: 28px; font-weight: 600;">{{ totalQ }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Освоено</div>
        <div style="font-size: 28px; font-weight: 600;">{{ knownPct }}%</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">К повторению сегодня</div>
        <div style="font-size: 28px; font-weight: 600;">{{ srs.dueCount }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Серия дней</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.streakDays }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Лучший экзамен</div>
        <div style="font-size: 28px; font-weight: 600;">{{ progress.bestExamScore }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Режимы</h2>

    <div style="margin-bottom: 12px;">
      <h3>Экзамен</h3>
      <p class="muted" style="margin: 4px 0 8px;">
        14 заданий: 5 закрытых + 5 на соответствие/последовательность + 4 открытых.
        Пропорционально по 5 дисциплинам. Таймер 90 минут. Результат в конце.
      </p>
      <RouterLink to="/exam" class="btn primary">Начать экзамен</RouterLink>
    </div>

    <div style="margin-bottom: 12px;">
      <h3>Тренировка</h3>
      <p class="muted" style="margin: 4px 0 8px;">
        Учите по дисциплинам без таймера, с мгновенной проверкой и подсказками.
      </p>
      <RouterLink to="/training" class="btn">Открыть тренировку</RouterLink>
    </div>

    <div style="margin-bottom: 12px;">
      <h3>Повторения <span v-if="srs.dueCount > 0" class="pill matching">{{ srs.dueCount }}</span></h3>
      <p class="muted" style="margin: 4px 0 8px;">
        Карточки с интервальным повторением (SM-2). Лучший способ удержать в памяти.
      </p>
      <RouterLink to="/srs" class="btn">К повторению</RouterLink>
    </div>

    <div style="margin-bottom: 12px;">
      <h3>Работа над ошибками <span class="pill error" v-if="progress.mistakeIds.length">{{ progress.mistakeIds.length }}</span></h3>
      <p class="muted" style="margin: 4px 0 8px;">
        Только те вопросы, в которых вы ошибались.
      </p>
      <RouterLink to="/mistakes" class="btn">Разобрать ошибки</RouterLink>
    </div>

    <div>
      <h3>Каталог вопросов</h3>
      <p class="muted" style="margin: 4px 0 8px;">
        Просмотр всех {{ totalQ }} вопросов с фильтрами и автоматической подсветкой подозрительных
        — для ручной верификации после парсинга.
      </p>
      <RouterLink to="/browse" class="btn">Открыть каталог</RouterLink>
    </div>
  </div>

  <div class="card">
    <h2>Дисциплины</h2>
    <ol style="padding-left: 20px;">
      <li v-for="d in qs.disciplines" :key="d.num">
        <strong>{{ d.name }}</strong>
        <span class="muted" style="font-size: 13px;"> · {{ d.count }} вопросов</span>
      </li>
    </ol>
  </div>
</template>
