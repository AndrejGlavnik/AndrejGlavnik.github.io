const yearTarget = document.querySelector('[data-year]');
if (yearTarget) yearTarget.textContent = new Date().getFullYear();

const header = document.querySelector('[data-header]');
const updateHeader = () => {
  if (!header) return;
  header.classList.toggle('scrolled', window.scrollY > 18);
};
updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });

const reveals = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });
reveals.forEach((element) => observer.observe(element));

const printButton = document.querySelector('[data-print]');
if (printButton) {
  printButton.addEventListener('click', () => window.print());
}
