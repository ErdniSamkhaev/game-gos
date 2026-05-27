<script setup>
import { computed, ref } from "vue";
import { useQuestionsStore } from "@/stores/questions";
import { validateQuestion, highestLevel, findDuplicates, duplicateIssue } from "@/lib/validate";

const qs = useQuestionsStore();

const selectedDiscipline = ref(null);
const selectedTypes = ref(["single", "multi", "matching", "sequence", "open"]);
const onlySuspicious = ref(false);
const onlyDuplicates = ref(false);
const search = ref("");
const expanded = ref(new Set());

const ALL_TYPES = [
  { id: "single", label: "single" },
  { id: "multi", label: "multi" },
  { id: "matching", label: "matching" },
  { id: "sequence", label: "sequence" },
  { id: "open", label: "open" },
];

const duplicateMap = computed(() => findDuplicates(qs.all));

const idConflicts = computed(() => {
  const counts = new Map();
  for (const q of qs.all) {
    if (!q.id) continue;
    counts.set(q.id, (counts.get(q.id) || 0) + 1);
  }
  const result = new Set();
  for (const [id, n] of counts) {
    if (n > 1) result.add(id);
  }
  return result;
});

const enriched = computed(() =>
  qs.all.map((q) => {
    const issues = validateQuestion(q);
    if (!q.id) {
      issues.push({
        level: "error",
        code: "missing_id",
        label: "У вопроса нет id — он не рендерится корректно",
      });
    } else if (idConflicts.value.has(q.id)) {
      issues.push({
        level: "error",
        code: "duplicate_id",
        label: `Дубликат id ${q.id}: рендер ломается, нужно переименовать`,
      });
    }
    if (q.discipline_num === undefined || q.discipline_num === null) {
      issues.push({
        level: "error",
        code: "missing_discipline",
        label: "У вопроса нет discipline_num — он не попадёт в фильтры",
      });
    }
    const dupIds = duplicateMap.value.get(q.id);
    if (dupIds) {
      const di = duplicateIssue(dupIds);
      if (di) issues.push(di);
    }
    return { q, issues, worst: highestLevel(issues), dupIds: dupIds || null };
  })
);

const filtered = computed(() => {
  let list = enriched.value;
  if (selectedDiscipline.value !== null) {
    list = list.filter((e) => e.q.discipline_num === Number(selectedDiscipline.value));
  }
  if (selectedTypes.value.length) {
    list = list.filter((e) => selectedTypes.value.includes(e.q.type));
  }
  if (onlySuspicious.value) {
    list = list.filter((e) => e.worst !== null);
  }
  if (onlyDuplicates.value) {
    list = list.filter((e) => e.dupIds !== null);
  }
  const q = search.value.trim().toLowerCase();
  if (q) {
    list = list.filter((e) => {
      const haystack = [
        e.q.statement,
        e.q.id,
        JSON.stringify(e.q.options || e.q.items || e.q.left || e.q.right || ""),
        typeof e.q.answer === "string" ? e.q.answer : JSON.stringify(e.q.answer),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }
  return list;
});

const summary = computed(() => {
  const total = enriched.value.length;
  const errors = enriched.value.filter((e) => e.worst === "error").length;
  const warns = enriched.value.filter((e) => e.worst === "warn").length;
  const infos = enriched.value.filter((e) => e.worst === "info").length;
  const ok = total - errors - warns - infos;
  const duplicates = enriched.value.filter((e) => e.dupIds !== null).length;
  return { total, errors, warns, infos, ok, duplicates };
});

const summaryByDiscipline = computed(() => {
  const map = {};
  for (const e of enriched.value) {
    const k = e.q.discipline_num;
    if (!map[k]) {
      map[k] = {
        num: k,
        name: e.q.discipline_name,
        total: 0,
        errors: 0,
        warns: 0,
        single: 0,
        multi: 0,
        matching: 0,
        sequence: 0,
        open: 0,
      };
    }
    map[k].total += 1;
    if (map[k][e.q.type] !== undefined) map[k][e.q.type] += 1;
    if (e.worst === "error") map[k].errors += 1;
    if (e.worst === "warn") map[k].warns += 1;
  }
  return Object.values(map).sort((a, b) => a.num - b.num);
});

function toggleType(t) {
  const i = selectedTypes.value.indexOf(t);
  if (i >= 0) selectedTypes.value.splice(i, 1);
  else selectedTypes.value.push(t);
}

function toggleExpand(id) {
  if (expanded.value.has(id)) expanded.value.delete(id);
  else expanded.value.add(id);
  // trigger re-render
  expanded.value = new Set(expanded.value);
}

function formatAnswer(q) {
  if (q.type === "matching") {
    return Object.entries(q.answer || {}).map(([k, v]) => `${k}-${v}`).join(", ");
  }
  if (q.type === "sequence") {
    return (q.answer || []).join(" → ");
  }
  if (q.type === "open") {
    return q.answer || "";
  }
  return (q.answer || []).join(", ");
}

function copyId(id) {
  navigator.clipboard?.writeText(id);
}

const SHORT_NAMES = {
  "Безопасность операционных систем и баз данных": "Безопасность ОС и БД",
  "Информационный менеджмент": "Информационный менеджмент",
  "Разработка web-приложений на языке JavaScript": "JavaScript",
  "Разработка серверных приложений для WEB": "Серверные приложения",
  "Реинжиниринг бизнес-процессов": "Реинжиниринг",
};

function shortDiscipline(fullName) {
  return SHORT_NAMES[fullName] || fullName;
}
</script>

<template>
  <h1>Каталог вопросов</h1>
  <p class="muted">
    Все {{ summary.total }} вопросов с фильтрами и автоматической проверкой парсинга.
    Полезно для ручной верификации.
  </p>

  <div class="card">
    <div class="row wrap" style="gap: 24px;">
      <div>
        <div class="muted" style="font-size: 13px;">Всего</div>
        <div style="font-size: 22px; font-weight: 600;">{{ summary.total }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Без замечаний</div>
        <div style="font-size: 22px; font-weight: 600; color: var(--success);">{{ summary.ok }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Подозрительных</div>
        <div style="font-size: 22px; font-weight: 600; color: var(--warning);">{{ summary.warns }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">С ошибками</div>
        <div style="font-size: 22px; font-weight: 600; color: var(--error);">{{ summary.errors }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Заметок</div>
        <div style="font-size: 22px; font-weight: 600;">{{ summary.infos }}</div>
      </div>
      <div>
        <div class="muted" style="font-size: 13px;">Дубликатов</div>
        <div style="font-size: 22px; font-weight: 600; color: var(--pill-matching);">{{ summary.duplicates }}</div>
      </div>
    </div>

    <div style="margin-top: 16px;">
      <strong style="font-size: 14px;">По дисциплинам:</strong>
      <div v-for="d in summaryByDiscipline" :key="d.num" style="margin-top: 6px; font-size: 13px;">
        <strong>{{ d.num }}.</strong> {{ d.name }} —
        {{ d.total }} вопросов
        (<span>single: {{ d.single }}</span>,
        <span>multi: {{ d.multi }}</span>,
        <span>matching: {{ d.matching }}</span>,
        <span>sequence: {{ d.sequence }}</span>,
        <span>open: {{ d.open }}</span>)
        <span v-if="d.errors > 0" style="color: var(--error);"> · {{ d.errors }} с ошибками</span>
        <span v-if="d.warns > 0" style="color: var(--warning);"> · {{ d.warns }} подозрительных</span>
      </div>
    </div>
  </div>

  <div class="card">
    <h3 style="margin-top: 0; margin-bottom: 16px;">Фильтры</h3>

    <div class="filter-group">
      <span class="filter-label">Дисциплина</span>
      <div class="tabs" style="margin-bottom: 0;">
        <span
          :class="['tab', selectedDiscipline === null ? 'active' : '']"
          @click="selectedDiscipline = null"
        >Все</span>
        <span
          v-for="d in qs.disciplines"
          :key="d.num"
          :class="['tab', selectedDiscipline === d.num ? 'active' : '']"
          @click="selectedDiscipline = d.num"
          :title="d.name"
        >{{ d.num }}. {{ shortDiscipline(d.name) }}</span>
      </div>
    </div>

    <div class="filter-group">
      <span class="filter-label">Типы заданий</span>
      <div class="tabs" style="margin-bottom: 0;">
        <span
          v-for="t in ALL_TYPES"
          :key="t.id"
          :class="['tab', selectedTypes.includes(t.id) ? 'active' : '']"
          @click="toggleType(t.id)"
        >{{ t.label }}</span>
      </div>
    </div>

    <div class="filter-group">
      <label style="display: inline-flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; margin-right: 16px;">
        <input type="checkbox" v-model="onlySuspicious" />
        Только подозрительные ({{ summary.errors + summary.warns + summary.infos }})
      </label>
      <label style="display: inline-flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px;">
        <input type="checkbox" v-model="onlyDuplicates" />
        Только дубликаты ({{ summary.duplicates }})
      </label>
    </div>

    <div class="filter-group" style="margin-bottom: 0;">
      <span class="filter-label">Поиск</span>
      <input
        class="input"
        v-model="search"
        placeholder="По тексту вопроса, ответу или ID (например, d3-multi-070)"
      />
    </div>
  </div>

  <p class="muted">Показано: <strong>{{ filtered.length }}</strong> из {{ summary.total }}</p>

  <div
    v-for="(e, idx) in filtered"
    :key="`${e.q.id || 'noid'}-${idx}`"
    class="card"
    :style="{
      borderColor:
        e.worst === 'error' ? 'var(--error)' :
        e.worst === 'warn'  ? 'var(--warning)' :
        e.worst === 'info'  ? 'var(--primary)' : 'var(--border)',
    }"
  >
    <div class="row between wrap" style="gap: 8px;">
      <div style="flex: 1; min-width: 280px;">
        <div class="row wrap" style="gap: 6px; margin-bottom: 6px;">
          <span :class="['pill', e.q.type]">{{ e.q.type }}</span>
          <span class="pill">Дисц. {{ e.q.discipline_num }}</span>
          <span class="muted" style="font-size: 12px;">{{ e.q.id }} · стр. {{ e.q.page }}</span>
        </div>
        <div style="font-weight: 500;">{{ e.q.statement }}</div>
        <div class="muted" style="font-size: 13px; margin-top: 4px;">
          Ответ: <strong>{{ formatAnswer(e.q) }}</strong>
        </div>
      </div>
      <div class="btn-row">
        <button class="btn" @click="copyId(e.q.id)" title="Скопировать ID">📋</button>
        <button class="btn" @click="toggleExpand(e.q.id)">
          {{ expanded.has(e.q.id) ? "Свернуть" : "Развернуть" }}
        </button>
      </div>
    </div>

    <div v-if="e.issues.length" style="margin-top: 10px;">
      <div
        v-for="(it, idx) in e.issues"
        :key="idx"
        :style="{
          fontSize: '13px',
          padding: '4px 8px',
          borderRadius: '6px',
          marginTop: '4px',
          background:
            it.level === 'error' ? 'var(--tint-error)' :
            it.level === 'warn'  ? 'var(--tint-warning)' :
                                    'var(--tint-primary)',
          color:
            it.level === 'error' ? 'var(--error)' :
            it.level === 'warn'  ? 'var(--warning)' :
                                    'var(--primary)',
        }"
      >
        <span v-if="it.level === 'error'">🔴</span>
        <span v-else-if="it.level === 'warn'">🟠</span>
        <span v-else>🔵</span>
        {{ it.label }}
      </div>
    </div>

    <div v-if="expanded.has(e.q.id)" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);">
      <div v-if="e.q.options" style="margin-bottom: 8px;">
        <div class="muted" style="font-size: 13px;">Варианты:</div>
        <div v-for="o in e.q.options" :key="o.key" style="margin: 2px 0;">
          <strong>{{ o.key }})</strong> {{ o.text }}
        </div>
      </div>
      <div v-if="e.q.items" style="margin-bottom: 8px;">
        <div class="muted" style="font-size: 13px;">Элементы (в порядке исходных опций):</div>
        <div v-for="o in e.q.items" :key="o.key" style="margin: 2px 0;">
          <strong>{{ o.key }})</strong> {{ o.text }}
        </div>
      </div>
      <div v-if="e.q.left" style="margin-bottom: 8px;">
        <div class="muted" style="font-size: 13px;">Слева:</div>
        <div v-for="o in e.q.left" :key="o.key" style="margin: 2px 0;">
          <strong>{{ o.key }}.</strong> {{ o.text }}
        </div>
      </div>
      <div v-if="e.q.right" style="margin-bottom: 8px;">
        <div class="muted" style="font-size: 13px;">Справа:</div>
        <div v-for="o in e.q.right" :key="o.key" style="margin: 2px 0;">
          <strong>{{ o.key }}.</strong> {{ o.text }}
        </div>
      </div>
      <div v-if="e.q.raw_answer" class="muted" style="font-size: 12px;">
        Сырой ответ из PDF: <code>{{ e.q.raw_answer }}</code>
      </div>
    </div>
  </div>

  <div v-if="filtered.length === 0" class="card">
    <p class="muted">По выбранным фильтрам ничего не найдено.</p>
  </div>
</template>
