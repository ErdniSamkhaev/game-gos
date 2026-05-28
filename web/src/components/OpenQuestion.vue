<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: String, default: "" },
  selfGrade: { type: Number, default: null },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
  // Сколько раз подряд этот вопрос был полностью провален.
  // При >= AUTO_HINT_THRESHOLD автоматически показываем первое слово.
  mistakeCount: { type: Number, default: 0 },
});
const emit = defineEmits(["update:modelValue", "update:selfGrade"]);

const AUTO_HINT_THRESHOLD = 2;

const revealed = ref(false);
// Сколько слов из эталона раскрыто как подсказка (0 — подсказка скрыта).
const hintWords = ref(0);

const showAnswer = computed(() => revealed.value || props.showFeedback || props.locked);

// Разбиваем эталон на «слова», сохраняя разделители, чтобы хинт читался
// естественно (с пробелами и переносами).
const answerTokens = computed(() => {
  const text = String(props.question.answer || "");
  // Чередующиеся блоки [слово, разделитель, слово, разделитель, ...].
  return text.split(/(\s+)/);
});

const totalWords = computed(
  () => answerTokens.value.filter((t) => t && !/^\s+$/.test(t)).length,
);

const hintText = computed(() => {
  if (hintWords.value <= 0) return "";
  let wordsLeft = hintWords.value;
  const out = [];
  for (const tok of answerTokens.value) {
    if (wordsLeft <= 0) break;
    out.push(tok);
    if (tok && !/^\s+$/.test(tok)) wordsLeft -= 1;
  }
  return out.join("").trimEnd();
});

const canExpandHint = computed(() => hintWords.value < totalWords.value);

// Автоматически раскрываем первое слово, если по вопросу серия ошибок.
// Срабатывает при смене вопроса (через ключ id) и не мешает, если эталон уже открыт.
watch(
  () => props.question?.id,
  () => {
    revealed.value = false;
    hintWords.value = props.mistakeCount >= AUTO_HINT_THRESHOLD ? 1 : 0;
  },
  { immediate: true },
);

function setGrade(v) {
  emit("update:selfGrade", v);
}

function showHint() {
  if (hintWords.value === 0) hintWords.value = 1;
  else if (canExpandHint.value) hintWords.value += 1;
}

function hideHint() {
  hintWords.value = 0;
}
</script>

<template>
  <div>
    <p class="muted" style="font-size: 13px;">
      Сформулируйте ответ своими словами, затем сравните с эталоном
    </p>
    <textarea
      class="textarea"
      :value="modelValue"
      :disabled="locked"
      placeholder="Ваш ответ..."
      @input="emit('update:modelValue', $event.target.value)"
    ></textarea>

    <div
      v-if="!showAnswer && hintWords > 0"
      class="card"
      style="background: var(--tint-warning); border-color: var(--warning); margin-top: 8px; padding: 8px 10px;"
    >
      <div class="muted" style="font-size: 12px; margin-bottom: 4px;">
        Подсказка ({{ hintWords }} {{ hintWords === 1 ? 'слово' : (hintWords < 5 ? 'слова' : 'слов') }} из {{ totalWords }})
        <span
          v-if="mistakeCount >= AUTO_HINT_THRESHOLD"
          style="margin-left: 6px;"
        >· показана автоматически: серия промахов {{ mistakeCount }}</span>
      </div>
      <div style="white-space: pre-wrap; font-weight: 500;">{{ hintText }}<span class="muted">…</span></div>
    </div>

    <div class="btn-row" style="margin-top: 12px; flex-wrap: wrap;">
      <button
        v-if="!showAnswer && canExpandHint"
        class="btn"
        @click="showHint"
      >
        {{ hintWords === 0 ? 'Подсказка: первое слово' : 'Ещё слово' }}
      </button>
      <button
        v-if="!showAnswer && hintWords > 0"
        class="btn"
        @click="hideHint"
      >
        Скрыть подсказку
      </button>
      <button v-if="!showAnswer" class="btn" @click="revealed = true">
        Показать эталон
      </button>
    </div>

    <div v-if="showAnswer" class="card" style="background: var(--code-bg); margin-top: 8px;">
      <div class="muted" style="font-size: 13px; margin-bottom: 4px;">Эталон ответа:</div>
      <div style="white-space: pre-wrap;">{{ question.answer }}</div>
    </div>

    <div v-if="showAnswer && !locked" style="margin-top: 12px;">
      <div class="muted" style="font-size: 13px; margin-bottom: 6px;">
        Оцените себя: вы знали этот ответ?
      </div>
      <div class="btn-row">
        <button :class="['btn', selfGrade === 0 ? 'error' : '']" @click="setGrade(0)">
          Не знал
        </button>
        <button :class="['btn', selfGrade === 1 ? 'warning' : '']" @click="setGrade(1)">
          Частично
        </button>
        <button :class="['btn', selfGrade === 2 ? 'success' : '']" @click="setGrade(2)">
          Знал точно
        </button>
      </div>
    </div>
  </div>
</template>
