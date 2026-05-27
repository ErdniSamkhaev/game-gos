<script setup>
import { computed } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: Object, default: () => ({}) },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const value = computed(() => props.modelValue || {});
const right = computed(() => props.question.right || []);
const usedLetters = computed(() =>
  new Set(Object.values(value.value).filter(Boolean))
);

function setLetter(leftKey, letter) {
  if (props.locked) return;
  const next = { ...value.value };
  if (letter === "") {
    delete next[leftKey];
  } else {
    for (const k of Object.keys(next)) {
      if (next[k] === letter) delete next[k];
    }
    next[leftKey] = letter;
  }
  emit("update:modelValue", next);
}

function classFor(leftKey) {
  if (!props.showFeedback) return "match-cell";
  const correct = props.question.answer?.[leftKey];
  const got = value.value[leftKey];
  if (got && got === correct) return "match-cell correct";
  if (got && got !== correct) return "match-cell wrong";
  return "match-cell";
}
</script>

<template>
  <div>
    <p class="muted" style="font-size: 13px;">
      Подберите к каждому пункту слева подходящую букву справа
    </p>
    <div class="card" style="background: var(--code-bg); padding: 12px;">
      <div style="margin-bottom: 6px; font-weight: 600;">Варианты справа:</div>
      <div v-for="r in right" :key="r.key" style="margin-bottom: 4px;">
        <strong>{{ r.key }})</strong> {{ r.text }}
      </div>
    </div>
    <div v-for="l in question.left" :key="l.key" :class="classFor(l.key)" style="margin-bottom: 8px;">
      <div class="row between">
        <div><strong>{{ l.key }}.</strong> {{ l.text }}</div>
        <select
          class="input"
          style="width: auto; min-width: 80px;"
          :value="value[l.key] || ''"
          :disabled="locked"
          @change="setLetter(l.key, $event.target.value)"
        >
          <option value="">—</option>
          <option v-for="r in right" :key="r.key" :value="r.key">{{ r.key }}</option>
        </select>
      </div>
      <div v-if="showFeedback && question.answer?.[l.key]" class="muted" style="font-size: 13px; margin-top: 4px;">
        Правильно: {{ question.answer[l.key] }}
      </div>
    </div>
  </div>
</template>
