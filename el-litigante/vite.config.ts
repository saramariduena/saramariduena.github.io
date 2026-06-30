import { defineConfig } from 'vite';

// Configuración de Vite. La salida estática (carpeta `dist`) es 100% compatible
// con despliegues en Vercel, Netlify o cualquier hosting de sitios estáticos.
export default defineConfig({
  base: './',
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        // Separamos Phaser en su propio chunk para aprovechar el cache del navegador.
        manualChunks: {
          phaser: ['phaser'],
        },
      },
    },
  },
  server: {
    host: true,
    port: 5173,
  },
});
