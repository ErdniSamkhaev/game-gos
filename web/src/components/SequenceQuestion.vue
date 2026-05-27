<script setup>
import { computed, watch } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: Array, default: () => [] },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const itemMap = computed(() => {
  const m = {};
  for (const it of props.question.items || []) m[it.key] = it.text;
  return m;
});

const initialOrder = computed(() => {
  if (props.modelValue && props.modelValue.length === (props.question.items?.length || 0)) {
    return props.modelValue;
  }
  // Start with the items in their original (possibly shuffled-by-PDF) order.
  return (props.question.items || []).map((i) => i.key);
});

watch(
  () => props.modelValue,
  (v) => {
    if (!v || v.length === 0) {
      emit("update:modelValue", initialOrder.value.slice());
    }
  },
  { immediate: true },
);

function move(idx, delta) {
  if (props.locked) return;
  const next = [...(props.modelValue || initialOrder.value)];
  const j = idx + delta;
  if (j < 0 || j >= next.length) return;
  [next[idx], next[j]] = [next[j], next[idx]];
  emit("update:modelValue", next);
}

function classFor(idx, key) {
  if (!props.showFeedback) return "match-cell";
  const correctKey = props.question.answer?.[idx];
  if (correctKey === key) return "match-cell correct";
  return "match-cell wrong";
}
</script>

<template>
  <div>
    <p class="muted" style="font-size: 13px;">
      Расставьте элементы в правильном порядке (стрелками вверх/вниз)
    </p>
    <div
      v-for="(key, idx) in (modelValue || initialOrder)"
      :key="key"
      :class="classFor(idx, key)"
      style="margin-bottom: 8px;"
    >
      <div class="row between">
        <div><strong>{{ idx + 1 }}.</strong> {{ itemMap[key] || key }}</div>
        <div class="btn-row" v-if="!locked">
          <button class="btn" :disabled="idx === 0" @click="move(idx, -1)">↑</button>
          <button class="btn" :disabled="idx === (modelValue?.length || 0) - 1" @click="move(idx, 1)">↓</button>
        </div>
      </div>
      <div v-if="showFeedback && question.answer?.[idx] !== key" class="muted" style="font-size: 13px; margin-top: 4px;">
        Правильно здесь: {{ itemMap[question.answer[idx]] || question.answer[idx] }}
      </div>
    </div>
  </div>
</template>
