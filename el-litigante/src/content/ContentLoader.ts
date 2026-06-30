import type {
  Content,
  World,
  Lesson,
  EnemyDef,
  Skill,
  Difficulty,
  Achievement,
  Npc,
  Dato,
  LegalCase,
  CaseStage,
  Rank,
} from '../core/types';

// Carga todo el contenido jurídico/de juego desde archivos JSON estáticos.
// Vite sirve la carpeta `public` en la raíz; usamos rutas relativas para que
// funcione bajo cualquier `base` (incluida la de Vercel).
async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`No se pudo cargar ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export async function loadContent(): Promise<Content> {
  const base = import.meta.env.BASE_URL || '/';
  const p = (f: string) => `${base}data/${f}`.replace(/\/+/g, '/');

  const [worlds, lessons, enemies, skills, difficulties, achievements, npcs, datos, cases, instancias, ranks] =
    await Promise.all([
      getJson<World[]>(p('worlds.json')),
      getJson<Record<string, Lesson>>(p('lessons.json')),
      getJson<EnemyDef[]>(p('enemies.json')),
      getJson<Skill[]>(p('skills.json')),
      getJson<Difficulty[]>(p('difficulties.json')),
      getJson<Achievement[]>(p('achievements.json')),
      getJson<Npc[]>(p('npcs.json')),
      getJson<{ pruebas: Dato[]; peligros: Dato[] }>(p('datos.json')),
      getJson<LegalCase[]>(p('cases.json')),
      getJson<{ apelacion: CaseStage[]; casacion: CaseStage[] }>(p('instancias.json')),
      getJson<Rank[]>(p('ranks.json')),
    ]);

  worlds.sort((a, b) => a.order - b.order);
  return { worlds, lessons, enemies, skills, difficulties, achievements, npcs, datos, cases, instancias, ranks };
}
