document.getElementById("year").textContent = new Date().getFullYear();

const root = document.documentElement;
const toggle = document.getElementById("themeToggle");
const stored = localStorage.getItem("theme");
const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
const initial = stored || (prefersLight ? "light" : "dark");
root.setAttribute("data-theme", initial);
toggle.textContent = initial === "dark" ? "🌙" : "☀️";

toggle.addEventListener("click", () => {
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  toggle.textContent = next === "dark" ? "🌙" : "☀️";
});

const sections = document.querySelectorAll(".section");
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in-view");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 }
);
sections.forEach((section) => observer.observe(section));
