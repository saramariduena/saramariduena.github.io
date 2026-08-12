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
const semanaEl = document.getElementById("novedades-semana");

function escaparHTML(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

function formatearRangoSemana(inicioStr, finStr) {
  const inicio = new Date(inicioStr + "T00:00:00Z");
  const fin = new Date(finStr + "T00:00:00Z");
  const opcionesDia = { day: "numeric", timeZone: "UTC" };
  const opcionesCompletas = { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" };
  const mismoMes =
    inicio.getUTCMonth() === fin.getUTCMonth() && inicio.getUTCFullYear() === fin.getUTCFullYear();
  const finTexto = fin.toLocaleDateString("es-EC", opcionesCompletas);
  const inicioTexto = mismoMes
    ? inicio.toLocaleDateString("es-EC", opcionesDia)
    : inicio.toLocaleDateString("es-EC", opcionesCompletas);
  return `Semana del ${inicioTexto} al ${finTexto}`;
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
      actualizadoEl.textContent = `Última actualización · ${fechaActualizado}`;
    }

    if (datos.semana_inicio && datos.semana_fin) {
      semanaEl.textContent = formatearRangoSemana(datos.semana_inicio, datos.semana_fin);
    }
  })
  .catch(() => {
    listaNovedades.innerHTML = '<p class="news-status">No se pudieron cargar las novedades en este momento.</p>';
  });

const FORMSPREE_ENDPOINT = "https://formspree.io/f/TU_ID_AQUI";

const modalComentario = document.getElementById("modal-comentario");
const abrirComentario = document.getElementById("abrir-comentario");
const cerrarComentario = document.getElementById("cerrar-comentario");
const formComentario = document.getElementById("form-comentario");
const comentarioStatus = document.getElementById("comentario-status");

function abrirModal() {
  modalComentario.hidden = false;
  document.body.style.overflow = "hidden";
}

function cerrarModal() {
  modalComentario.hidden = true;
  document.body.style.overflow = "";
}

if (abrirComentario) {
  abrirComentario.addEventListener("click", abrirModal);
  cerrarComentario.addEventListener("click", cerrarModal);
  modalComentario.addEventListener("click", (evento) => {
    if (evento.target === modalComentario) cerrarModal();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !modalComentario.hidden) cerrarModal();
  });

  formComentario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const boton = formComentario.querySelector("button[type=submit]");
    boton.disabled = true;
    comentarioStatus.textContent = "Enviando…";
    comentarioStatus.className = "form-status";

    try {
      const datos = new FormData(formComentario);
      datos.append("tipo", "comentario");
      const respuesta = await fetch(FORMSPREE_ENDPOINT, {
        method: "POST",
        body: datos,
        headers: { Accept: "application/json" },
      });
      if (!respuesta.ok) throw new Error("Fallo el envío");
      comentarioStatus.textContent = "¡Gracias! Tu comentario fue enviado.";
      comentarioStatus.className = "form-status exito";
      formComentario.reset();
      setTimeout(cerrarModal, 1800);
    } catch (error) {
      comentarioStatus.textContent = "No se pudo enviar. Intenta de nuevo o escríbeme por WhatsApp.";
      comentarioStatus.className = "form-status error";
    } finally {
      boton.disabled = false;
    }
  });
}
