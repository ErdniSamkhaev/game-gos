<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  // Сколько раз подряд этот вопрос был полностью провален.
  // При >= AUTO_HINT_THRESHOLD первый шаг подсказки раскрывается автоматически.
  mistakeCount: { type: Number, default: 0 },
  // Когда ответ уже проверен/показан — подсказка не нужна.
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
  // В режиме экзамена подсказки выключены, чтобы не нарушать симуляцию.
  enabled: { type: Boolean, default: true },
});

const AUTO_HINT_THRESHOLD = 2;

// Сколько шагов подсказки раскрыто (0 — скрыта).
const steps = ref(0);

const answerDisabled = computed(
  () => !props.enabled || props.showFeedback || props.locked,
);

const itemMap = computed(() => {
  const m = {};
  for (const it of props.question.items || []) m[it.key] = it.text;
  return m;
});

// Список шагов подсказки. Каждый шаг — короткая строка, раскрывающая
// чуть больше правильного ответа, не показывая его целиком сразу.
const hintSteps = computed(() => {
  const q = props.question;
  switch (q.type) {
    case "open": {
      // Каждое слово эталона — отдельный шаг.
      const tokens = String(q.answer || "").split(/\s+/).filter(Boolean);
      return tokens;
    }
    case "single": {
      // Постепенно отсекаем неверные варианты.
      const correct = new Set(q.answer || []);
      const wrong = (q.options || []).map((o) => o.key).filter((k) => !correct.has(k));
      return wrong.map((k) => `Это точно не вариант «${k}»`);
    }
    case "multi": {
      const correct = q.answer || [];
      const head = `Правильных вариантов всего: ${correct.length}`;
      return [head, ...correct.map((k) => `Один из правильных — «${k}»`)];
    }
    case "matching": {
      const ans = q.answer || {};
      return Object.keys(ans).map((k) => `${k} → ${ans[k]}`);
    }
    case "sequence": {
      const ans = q.answer || [];
      return ans.map((key, i) => `Позиция ${i + 1}: ${itemMap.value[key] || key}`);
    }
    default:
      return [];
  }
});

const totalSteps = computed(() => hintSteps.value.length);
const canExpand = computed(() => steps.value < totalSteps.value);
const isOpenType = computed(() => props.question.type === "open");

// Для открытых склеиваем раскрытые слова в естественную строку,
// для остальных — показываем список раскрытых шагов.
const revealedList = computed(() => hintSteps.value.slice(0, steps.value));
const openText = computed(() => revealedList.value.join(" "));

const intro = computed(() => {
  switch (props.question.type) {
    case "open":     return "Первые слова эталона:";
    case "single":   return "Сужаем варианты:";
    case "multi":    return "Про правильные варианты:";
    case "matching": return "Часть верных соответствий:";
    case "sequence": return "Часть верных позиций:";
    default:         return "Подсказка:";
  }
});

// Автораскрытие первого шага при серии промахов. Срабатывает при смене
// вопроса и не мешает, когда ответ уже показан.
watch(
  () => props.question?.id,
  () => {
    steps.value =
      props.mistakeCount >= AUTO_HINT_THRESHOLD && !answerDisabled.value ? 1 : 0;
  },
  { immediate: true },
);

function showMore() {
  if (canExpand.value) steps.value += 1;
}

function hide() {
  steps.value = 0;
}
</script>

<template>
  <div v-if="!answerDisabled && totalSteps > 0" style="margin-bottom: 12px;">
    <div
      v-if="steps > 0"
      class="card"
      style="background: var(--tint-warning); border-color: var(--warning); padding: 8px 10px; margin: 0 0 8px;"
    >
      <div class="muted" style="font-size: 12px; margin-bottom: 4px;">
        {{ intro }} ({{ steps }} из {{ totalSteps }})
        <span v-if="mistakeCount >= AUTO_HINT_THRESHOLD" style="margin-left: 6px;">
          · показана автоматически: серия промахов {{ mistakeCount }}
        </span>
      </div>
      <div v-if="isOpenType" style="white-space: pre-wrap; font-weight: 500;">
        {{ openText }}<span class="muted">…</span>
      </div>
      <ul v-else style="margin: 4px 0 0; padding-left: 18px;">
        <li v-for="(line, i) in revealedList" :key="i" style="font-weight: 500;">{{ line }}</li>
      </ul>
    </div>

    <div class="btn-row" style="flex-wrap: wrap;">
      <button v-if="canExpand" class="btn" @click="showMore">
        {{ steps === 0 ? "Подсказка" : "Ещё подсказку" }}
      </button>
      <button v-if="steps > 0" class="btn" @click="hide">Скрыть подсказку</button>
    </div>
  </div>
</template>
