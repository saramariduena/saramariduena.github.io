document.getElementById("year").textContent = new Date().getFullYear();

const root = document.documentElement;
const toggle = document.getElementById("themeToggle");
const stored = localStorage.getItem("theme");
const initial = stored || "light";
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

const listaNovedades = document.getElementById("novedades-lista");
const actualizadoEl = document.getElementById("novedades-actualizado");

function escaparHTML(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

fetch("novedades.json", { cache: "no-store" })
  .then((respuesta) => {
    if (!respuesta.ok) throw new Error("No se pudo cargar novedades.json");
    return respuesta.json();
  })
  .then((datos) => {
    const noticias = datos.noticias || [];
    if (noticias.length === 0) {
      listaNovedades.innerHTML = '<p class="news-status">Aún no hay novedades cargadas. Vuelve pronto.</p>';
      return;
    }
    listaNovedades.innerHTML = noticias
      .filter((noticia) => /^https?:\/\//i.test(noticia.enlace || ""))
      .map((noticia) => {
        const fecha = noticia.fecha
          ? new Date(noticia.fecha).toLocaleDateString("es-EC", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })
          : "";
        const enlaceSeguro = encodeURI(noticia.enlace);
        return `
          <a class="news-item" href="${enlaceSeguro}" target="_blank" rel="noopener">
            <span class="news-item-title">${escaparHTML(noticia.titulo)}</span>
            <span class="news-item-meta">${escaparHTML(noticia.fuente)}${fecha ? " · " + fecha : ""}</span>
          </a>
        `;
      })
      .join("");

    if (datos.actualizado) {
      const fechaActualizado = new Date(datos.actualizado).toLocaleString("es-EC", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
      actualizadoEl.textContent = `Actualizado automáticamente · ${fechaActualizado}`;
    }
  })
  .catch(() => {
    listaNovedades.innerHTML = '<p class="news-status">No se pudieron cargar las novedades en este momento.</p>';
  });
