<script setup>
import { computed } from "vue";

const props = defineProps({
  // Сколько всего вопросов в подборке.
  total: { type: Number, required: true },
  // Индекс текущего вопроса (0-based).
  index: { type: Number, default: 0 },
  // При большом количестве точки нечитаемы — переключаемся на полосу.
  maxDots: { type: Number, default: 30 },
});

const useDots = computed(() => props.total > 0 && props.total <= props.maxDots);
const pct = computed(() =>
  props.total > 0 ? ((props.index + 1) / props.total) * 100 : 0,
);
</script>

<template>
  <div v-if="useDots" class="progress-dots" role="progressbar" :aria-valuenow="index + 1" :aria-valuemax="total">
    <span
      v-for="i in total"
      :key="i"
      :class="['dot', i - 1 < index ? 'done' : '', i - 1 === index ? 'current' : '']"
    ></span>
  </div>
  <div v-else class="bar">
    <div class="bar-fill" :style="{ width: pct + '%' }"></div>
  </div>
</template>
