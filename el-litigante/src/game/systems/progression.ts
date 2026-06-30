import type { World, SaveProfile } from '../../core/types';
import { parseLayout, generateLayout, type ParsedLevel } from './levelBuilder';

// Lógica de progresión: qué niveles tiene un mundo y cuál sigue.

export interface LevelMeta {
  id: string;
  title: string;
  lessonId: string;
  index: number;
}

export function worldLevels(world: World): LevelMeta[] {
  if (world.levels && world.levels.length) {
    return world.levels.map((l, i) => ({ id: l.id, title: l.title, lessonId: l.lessonId, index: i }));
  }
  const gen = world.generator!;
  return Array.from({ length: gen.levels }, (_, i) => ({
    id: `${world.id}_g${i}`,
    title: `Nivel ${i + 1}`,
    lessonId: world.lessonId,
    index: i,
  }));
}

export function buildParsedLevel(world: World, index: number): ParsedLevel {
  if (world.levels && world.levels[index]?.layout) {
    return parseLayout(world.levels[index].layout!);
  }
  return parseLayout(generateLayout(world.generator!, index));
}

export function isWorldUnlocked(worlds: World[], world: World, profile: SaveProfile): boolean {
  if (world.order === 1) return true;
  const prev = worlds.find((w) => w.order === world.order - 1);
  return !!prev && profile.worldsCompleted.includes(prev.id);
}

/** Próximo paso al ENTRAR a un mundo desde el mapa. */
export function entryStep(world: World, profile: SaveProfile): { isBoss: boolean; index: number } {
  const levels = worldLevels(world);
  const firstPending = levels.find((l) => !profile.levelsCompleted.includes(l.id));
  if (firstPending) return { isBoss: false, index: firstPending.index };
  if (!profile.bossesDefeated.includes(world.boss.id)) return { isBoss: true, index: levels.length };
  return { isBoss: false, index: 0 }; // mundo ya completado: rejugar desde el inicio
}
