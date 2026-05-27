<script setup>
import { computed } from "vue";
import ClosedQuestion from "@/components/ClosedQuestion.vue";
import MatchingQuestion from "@/components/MatchingQuestion.vue";
import SequenceQuestion from "@/components/SequenceQuestion.vue";
import OpenQuestion from "@/components/OpenQuestion.vue";
import { validateQuestion, highestLevel } from "@/lib/validate";

const props = defineProps({
  question: { type: Object, required: true },
  answer: { default: null },
  selfGrade: { type: Number, default: null },
  showFeedback: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
});
defineEmits(["update:answer", "update:selfGrade"]);

const issues = computed(() => validateQuestion(props.question));
const worst = computed(() => highestLevel(issues.value));
</script>

<template>
  <div>
    <div class="row" style="gap: 8px; margin-bottom: 8px;">
      <span :class="['pill', question.type]">{{ question.type }}</span>
      <span class="pill">Дисц. {{ question.discipline_num }}</span>
      <span class="muted" style="font-size: 13px;">{{ question.discipline_name }}</span>
    </div>

    <div
      v-if="worst"
      :style="{
        fontSize: '13px',
        padding: '8px 10px',
        borderRadius: '6px',
        marginBottom: '12px',
        background:
          worst === 'error' ? 'var(--tint-error)' :
          worst === 'warn'  ? 'var(--tint-warning)' :
                              'var(--tint-primary)',
        color:
          worst === 'error' ? 'var(--error)' :
          worst === 'warn'  ? 'var(--warning)' :
                              'var(--primary)',
      }"
    >
      <strong v-if="worst === 'error'">⚠ Возможна ошибка парсинга:</strong>
      <strong v-else-if="worst === 'warn'">⚠ Подозрительный вопрос:</strong>
      <strong v-else>ℹ Заметка:</strong>
      <span v-for="(it, idx) in issues" :key="idx" style="margin-left: 4px;">
        {{ it.label }}<span v-if="idx < issues.length - 1">;</span>
      </span>
    </div>

    <div class="statement">{{ question.statement }}</div>

    <ClosedQuestion
      v-if="question.type === 'single' || question.type === 'multi'"
      :question="question"
      :model-value="answer || []"
      :show-feedback="showFeedback"
      :locked="locked"
      @update:model-value="$emit('update:answer', $event)"
    />
    <MatchingQuestion
      v-else-if="question.type === 'matching'"
      :question="question"
      :model-value="answer || {}"
      :show-feedback="showFeedback"
      :locked="locked"
      @update:model-value="$emit('update:answer', $event)"
    />
    <SequenceQuestion
      v-else-if="question.type === 'sequence'"
      :question="question"
      :model-value="answer || []"
      :show-feedback="showFeedback"
      :locked="locked"
      @update:model-value="$emit('update:answer', $event)"
    />
    <OpenQuestion
      v-else-if="question.type === 'open'"
      :question="question"
      :model-value="answer || ''"
      :self-grade="selfGrade"
      :show-feedback="showFeedback"
      :locked="locked"
      @update:model-value="$emit('update:answer', $event)"
      @update:self-grade="$emit('update:selfGrade', $event)"
    />
  </div>
</template>
