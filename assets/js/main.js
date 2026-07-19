const root = document.documentElement;
const storageKey = "andrejglavnik-theme-v3";
const themeMeta = document.querySelector('meta[name="theme-color"]');
const themeToggle = document.querySelector("[data-theme-toggle]");
const menuButton = document.querySelector("[data-menu-button]");
const mobileNav = document.querySelector("[data-mobile-nav]");
const header = document.querySelector("[data-header]");

const readStoredTheme = () => {
  try {
    return localStorage.getItem(storageKey);
  } catch {
    return null;
  }
};

const preferredTheme = () => {
  const stored = readStoredTheme();
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

const applyTheme = (theme, persist = false) => {
  root.dataset.theme = theme;
  const dark = theme === "dark";
  themeToggle?.setAttribute("aria-pressed", String(dark));
  themeToggle?.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
  themeToggle?.setAttribute("title", dark ? "Dark mode. Switch to light" : "Light mode. Switch to dark");
  themeMeta?.setAttribute("content", dark ? "#080b10" : "#f3f6f8");
  if (persist) {
    try {
      localStorage.setItem(storageKey, theme);
    } catch {
      // The site remains functional when browser storage is unavailable.
    }
  }
};

applyTheme(preferredTheme());

themeToggle?.addEventListener("click", () => {
  applyTheme(root.dataset.theme === "dark" ? "light" : "dark", true);
});

const setMenu = (open) => {
  if (!menuButton || !mobileNav) return;
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  mobileNav.hidden = !open;
  header?.classList.toggle("menu-visible", open);
  document.body.classList.toggle("menu-open", open);
};

menuButton?.addEventListener("click", () => {
  setMenu(menuButton.getAttribute("aria-expanded") !== "true");
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || menuButton?.getAttribute("aria-expanded") !== "true") return;
  setMenu(false);
  menuButton.focus();
});

mobileNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => setMenu(false));
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 980) setMenu(false);
});

const updateHeader = () => header?.classList.toggle("is-scrolled", window.scrollY > 12);
updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

document.querySelectorAll("[data-year]").forEach((target) => {
  target.textContent = new Date().getFullYear();
});

const navLinks = [...document.querySelectorAll('.nav-links a[href^="#"]')];
const sections = navLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

if ("IntersectionObserver" in window) {
  const navObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    navLinks.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === `#${visible.target.id}`);
    });
  }, { rootMargin: "-20% 0px -65%", threshold: [0.01, 0.2, 0.5] });
  sections.forEach((section) => navObserver.observe(section));
}

const revealTargets = [...document.querySelectorAll(".reveal")];
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (reducedMotion || !("IntersectionObserver" in window)) {
  revealTargets.forEach((target) => target.classList.add("is-visible"));
} else {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -7%", threshold: 0.08 });
  revealTargets.forEach((target) => revealObserver.observe(target));
}

document.querySelectorAll("details").forEach((details) => {
  details.addEventListener("toggle", () => {
    if (!details.open) return;
    const group = details.closest(".timeline");
    if (!group) return;
    group.querySelectorAll("details[open]").forEach((other) => {
      if (other !== details) other.open = false;
    });
  });
});
