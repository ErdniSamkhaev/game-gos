<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: String, default: "" },
  selfGrade: { type: Number, default: null },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "update:selfGrade"]);

const revealed = ref(false);

const showAnswer = computed(() => revealed.value || props.showFeedback || props.locked);

function setGrade(v) {
  emit("update:selfGrade", v);
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

    <div style="margin-top: 12px;">
      <button v-if="!showAnswer" class="btn" @click="revealed = true">
        Показать эталон
      </button>
      <div v-else class="card" style="background: var(--code-bg); margin-top: 8px;">
        <div class="muted" style="font-size: 13px; margin-bottom: 4px;">Эталон ответа:</div>
        <div style="white-space: pre-wrap;">{{ question.answer }}</div>
      </div>
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
