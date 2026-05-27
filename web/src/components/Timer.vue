<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";

const props = defineProps({
  durationS: { type: Number, required: true },
  startedAt: { type: Number, required: true },
});
const emit = defineEmits(["expire"]);

const now = ref(Date.now());
let id = null;

onMounted(() => {
  id = setInterval(() => {
    now.value = Date.now();
    if (remainingS.value <= 0) emit("expire");
  }, 1000);
});
onUnmounted(() => clearInterval(id));

const remainingS = computed(() => {
  const elapsed = Math.floor((now.value - props.startedAt) / 1000);
  return Math.max(0, props.durationS - elapsed);
});

const formatted = computed(() => {
  const s = remainingS.value;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  }
  return `${m}:${String(sec).padStart(2, "0")}`;
});

const cls = computed(() => {
  if (remainingS.value <= 60) return "timer danger";
  if (remainingS.value <= 300) return "timer warning";
  return "timer";
});
</script>

<template>
  <span :class="cls">⏱ {{ formatted }}</span>
</template>
