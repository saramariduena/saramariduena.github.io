// Tipos del dominio. Mantienen separada la lógica del juego del contenido
// jurídico, que vive en archivos JSON (ver /public/data). Así el COGEP puede
// actualizarse sin tocar el código del motor.

export interface Trivia {
  pregunta: string;
  opciones: string[];
  correcta: number;
}

export interface Lesson {
  titulo: string;
  explicacion: string;
  articulo: string;
  resumen: string;
  ejemplo: string;
  consejo: string;
  trivia: Trivia;
}

export interface Palette {
  sky: string;
  skyBottom: string;
  ground: string;
  groundDark: string;
  platform: string;
  accent: string;
}

export interface Boss {
  id: string;
  name: string;
  title: string;
  lessonId: string;
  hp: number;
}

export interface GeneratorParams {
  levels: number;
  width: number;
  platformDensity: number;
  enemyDensity: number;
  coinDensity: number;
  hazardDensity: number;
  seed: number;
}

export interface LevelDef {
  id: string;
  title: string;
  lessonId: string;
  layout?: string[];
}

export interface World {
  id: string;
  order: number;
  title: string;
  subtitle: string;
  cogepArea: string;
  lessonId: string;
  palette: Palette;
  boss: Boss;
  levels?: LevelDef[];
  generator?: GeneratorParams;
}

export interface EnemyDef {
  id: string;
  name: string;
  color: string;
  behavior: 'patrol' | 'jumper' | 'chaser';
  speed: number;
  /** Contenido educativo del error procesal (se muestra al vencerlo). */
  concepto?: string;
  articulo?: string;
  dato?: string;
}

export interface Skill {
  id: string;
  name: string;
  desc: string;
  maxLevel: number;
  cost: number;
  effect: string;
  perLevel: number;
}

export interface Difficulty {
  id: string;
  name: string;
  desc: string;
  lives: number;
  enemySpeedMul: number;
  hazardDamage: number;
  triviaTime: number;
  xpMul: number;
}

export interface Achievement {
  id: string;
  name: string;
  desc: string;
  condition: { type: string; value: any };
}

export interface Npc {
  id: string;
  name: string;
  role: string;
  lines: string[];
}

export interface Dato {
  titulo: string;
  texto: string;
  articulo: string;
}

export interface Content {
  worlds: World[];
  lessons: Record<string, Lesson>;
  enemies: EnemyDef[];
  skills: Skill[];
  difficulties: Difficulty[];
  achievements: Achievement[];
  npcs: Npc[];
  datos: { pruebas: Dato[]; peligros: Dato[] };
}

export interface Stats {
  enemies: number;
  documents: number;
  trivia: number;
  perfectLevels: number;
  minutes: number;
  sessions: number;
  bossPerfect: number;
}

export interface SaveProfile {
  id: string;
  name: string;
  createdAt: number;
  difficulty: string;
  lex: number;
  xp: number;
  charLevel: number;
  skills: Record<string, number>;
  levelsCompleted: string[];
  worldsCompleted: string[];
  bossesDefeated: string[];
  lessonsRead: string[];
  achievements: string[];
  difficultyWorldsDone: string[];
  stats: Stats;
}

export interface Settings {
  theme: 'dark' | 'light';
  fontScale: number;
  colorblind: boolean;
  music: boolean;
  sfx: boolean;
}
