# Página web — pagina-web

Portafolio de una sola página (HTML/CSS/JS puro, sin frameworks ni build).

## Ver en local

Abre `index.html` en el navegador, o levanta un servidor simple:

```bash
cd pagina-web
python3 -m http.server 8000
```

Luego visita `http://localhost:8000`.

## Publicarla gratis en GitHub Pages

Ya incluye el workflow `.github/workflows/deploy-pagina-web.yml`, que
despliega automáticamente esta carpeta cada vez que cambia en `main`.

Solo falta activarlo una vez (es gratis, sin dominio ni cuenta externa):

1. En GitHub, entra al repositorio → **Settings** → **Pages**.
2. En **Build and deployment → Source**, selecciona **GitHub Actions**.
3. Haz merge de esta rama a `main` (o vuelve a ejecutar el workflow desde
   la pestaña **Actions**).
4. En unos segundos la página queda publicada en:
   `https://<usuario>.github.io/<repositorio>/`

## Personalizarla

Todo el contenido está en `index.html` (textos y secciones), los estilos
en `style.css` y el modo claro/oscuro + animaciones en `script.js`.
