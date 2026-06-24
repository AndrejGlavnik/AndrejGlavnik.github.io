const storageKey = "andrejglavnik-theme-v2";
const root = document.documentElement;
const themeMeta = document.querySelector('meta[name="theme-color"]');
const themeToggle = document.querySelector("[data-theme-toggle]");
const expandExperienceTrigger = document.querySelector("[data-expand-experience]");

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
    /* localStorage may be unavailable in strict privacy modes. */
  }
};

const syncThemeControl = () => {
  const isDark = root.dataset.theme === "dark";
  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute(
      "aria-label",
      isDark ? "Theme mode: dark. Switch to light mode" : "Theme mode: light. Switch to dark mode"
    );
    themeToggle.title = isDark ? "Dark mode selected. Switch to light mode" : "Light mode selected. Switch to dark mode";
  }
  if (themeMeta) {
    themeMeta.setAttribute("content", isDark ? "#090b0f" : "#f5f5f7");
  }
};

const applyTheme = (theme) => {
  root.dataset.theme = theme;
  syncThemeControl();
};

applyTheme(getStoredTheme() || "light");

themeToggle?.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  storeTheme(nextTheme);
});

const roleDetails = [...document.querySelectorAll("#experience details")];
const summaryOpenText = "Click to minimize";
const summaryClosedText = "Open role: see tools, decisions, impact";

const syncRoleSummary = (details) => {
  const summary = details.querySelector("summary");
  if (summary) {
    summary.textContent = details.open ? summaryOpenText : summaryClosedText;
  }
};

roleDetails.forEach((details) => {
  syncRoleSummary(details);
  details.addEventListener("toggle", () => syncRoleSummary(details));
});

const openExperienceDetails = () => {
  roleDetails.forEach((details) => {
    details.open = true;
    syncRoleSummary(details);
  });
};

expandExperienceTrigger?.addEventListener("click", (event) => {
  event.preventDefault();
  const experience = document.querySelector("#experience");
  experience?.scrollIntoView({ behavior: "smooth", block: "start" });
  window.history.pushState(null, "", "#experience");
  window.setTimeout(openExperienceDetails, 1100);
});

document.querySelectorAll("[data-year]").forEach((target) => {
  target.textContent = new Date().getFullYear();
});

const header = document.querySelector("[data-header]");
const setHeaderState = () => {
  header?.classList.toggle("is-scrolled", window.scrollY > 10);
};

setHeaderState();
window.addEventListener("scroll", setHeaderState, { passive: true });

const navLinks = [...document.querySelectorAll('.nav-links a[href^="#"]')];
const navTargets = navLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

const setActiveNavLink = () => {
  const marker = window.innerWidth < 720 ? 150 : 116;
  const activeTarget = navTargets.find((target) => {
    const rect = target.getBoundingClientRect();
    return rect.top <= marker && rect.bottom > marker;
  });

  navLinks.forEach((link) => {
    const isActive = activeTarget ? link.getAttribute("href") === `#${activeTarget.id}` : false;
    link.classList.toggle("active", isActive);
  });
};

setActiveNavLink();
window.addEventListener("scroll", setActiveNavLink, { passive: true });
window.addEventListener("hashchange", setActiveNavLink);
