const storageKey = "andrejglavnik-theme";
const root = document.documentElement;
const themeMeta = document.querySelector('meta[name="theme-color"]');
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

const buildThemeToggle = () => {
  const headerInner = document.querySelector(".header-inner");
  if (!headerInner) return null;
  const existingToggle = document.querySelector("[data-theme-toggle]");
  if (existingToggle) return existingToggle;

  const button = document.createElement("button");
  button.className = "theme-toggle";
  button.type = "button";
  button.title = "Toggle dark mode";
  button.setAttribute("aria-label", "Switch to dark mode");
  button.setAttribute("aria-pressed", "false");
  button.setAttribute("data-theme-toggle", "");

  const track = document.createElement("span");
  track.className = "theme-toggle-track";
  track.setAttribute("aria-hidden", "true");

  const thumb = document.createElement("span");
  thumb.className = "theme-toggle-thumb";
  track.append(thumb);
  button.append(track);

  const cta = headerInner.querySelector(".nav-cta");
  if (cta) {
    cta.before(button);
  } else {
    headerInner.append(button);
  }
  return button;
};

const themeToggle = buildThemeToggle();

const getStoredTheme = () => {
  try {
    return localStorage.getItem(storageKey);
  } catch {
    return null;
  }
};

const storeTheme = (theme) => {
  try {
    localStorage.setItem(storageKey, theme);
  } catch {
    // Local storage can be unavailable in strict privacy modes.
  }
};

const effectiveTheme = () => root.dataset.theme || (prefersDark.matches ? "dark" : "light");

const syncThemeControl = () => {
  const isDark = effectiveTheme() === "dark";
  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  }
  if (themeMeta) {
    themeMeta.setAttribute("content", isDark ? "#0e141b" : "#f7f8fb");
  }
};

const applyTheme = (theme) => {
  root.dataset.theme = theme;
  syncThemeControl();
};

applyTheme(getStoredTheme() || (prefersDark.matches ? "dark" : "light"));

themeToggle?.addEventListener("click", () => {
  const nextTheme = effectiveTheme() === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  storeTheme(nextTheme);
});

prefersDark.addEventListener("change", (event) => {
  if (!getStoredTheme()) {
    applyTheme(event.matches ? "dark" : "light");
  }
});

const yearTargets = document.querySelectorAll("[data-year]");
yearTargets.forEach((target) => {
  target.textContent = new Date().getFullYear();
});

const header = document.querySelector("[data-header]");
const setHeaderState = () => {
  if (!header) return;
  header.classList.toggle("is-scrolled", window.scrollY > 10);
};

setHeaderState();
window.addEventListener("scroll", setHeaderState, { passive: true });
