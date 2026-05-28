<script setup>
import { computed } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: Array, default: () => [] },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const isMulti = computed(() => props.question.type === "multi");
const correctSet = computed(() => new Set(props.question.answer || []));

function toggle(key) {
  if (props.locked) return;
  if (isMulti.value) {
    const arr = props.modelValue ? [...props.modelValue] : [];
    const i = arr.indexOf(key);
    if (i >= 0) arr.splice(i, 1);
    else arr.push(key);
    emit("update:modelValue", arr);
  } else {
    emit("update:modelValue", [key]);
  }
}

function classFor(key) {
  const selected = props.modelValue?.includes(key);
  if (props.showFeedback) {
    const isCorrect = correctSet.value.has(key);
    if (isCorrect) return "option correct";
    if (selected && !isCorrect) return "option wrong";
    return "option";
  }
  return selected ? "option selected" : "option";
}
</script>

<template>
  <div>
    <p v-if="isMulti" class="muted" style="font-size: 13px;">Можно выбрать несколько вариантов</p>
    <div
      v-for="opt in question.options"
      :key="opt.key"
      :class="classFor(opt.key)"
      @click="toggle(opt.key)"
    >
      <span class="option-key">{{ opt.key }}</span>
      <span class="option-text">{{ opt.text }}</span>
    </div>
  </div>
</template>
