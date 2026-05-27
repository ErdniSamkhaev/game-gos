import { ref, computed, watch, onMounted, onUnmounted } from "vue";

/**
 * Theme manager with three modes:
 *   - "auto"  → follow system (prefers-color-scheme)
 *   - "light" → force light
 *   - "dark"  → force dark
 *
 * The applied theme is exposed via <html data-theme="dark|light"> so that
 * CSS variables in style.css (`[data-theme="dark"]` block) take effect.
 */

const KEY = "game-gos:theme";
const VALID = ["auto", "light", "dark"];

const mode = ref(loadMode());
const systemDark = ref(false);
let mediaQuery = null;

function loadMode() {
  try {
    const v = localStorage.getItem(KEY);
    if (v && VALID.includes(v)) return v;
  } catch (_) {}
  return "auto";
}

function persistMode(m) {
  try {
    localStorage.setItem(KEY, m);
  } catch (_) {}
}

/** Apply the resolved theme to <html data-theme="...">. */
function applyTheme(resolved) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", resolved);
}

function detectSystem() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Initialise theme system. Should be called once at boot, before mount. */
export function initTheme() {
  systemDark.value = detectSystem();
  applyTheme(resolve(mode.value, systemDark.value));

  if (typeof window !== "undefined" && window.matchMedia) {
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e) => {
      systemDark.value = e.matches;
      if (mode.value === "auto") {
        applyTheme(resolve("auto", systemDark.value));
      }
    };
    if (mediaQuery.addEventListener) mediaQuery.addEventListener("change", onChange);
    else if (mediaQuery.addListener) mediaQuery.addListener(onChange);
  }
}

function resolve(m, sysDark) {
  if (m === "dark") return "dark";
  if (m === "light") return "light";
  return sysDark ? "dark" : "light";
}

watch(mode, (m) => {
  persistMode(m);
  applyTheme(resolve(m, systemDark.value));
});

export function useTheme() {
  const resolved = computed(() => resolve(mode.value, systemDark.value));

  function setMode(m) {
    if (VALID.includes(m)) mode.value = m;
  }

  function cycle() {
    const i = VALID.indexOf(mode.value);
    mode.value = VALID[(i + 1) % VALID.length];
  }

  return {
    mode,
    resolved,
    setMode,
    cycle,
    isDark: computed(() => resolved.value === "dark"),
  };
}
