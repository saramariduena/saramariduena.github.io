import type { Content, SaveProfile, Settings, Stats } from './types';

// Repositorio de guardado. Hoy persiste en localStorage (funciona en web y en
// los empaquetados móviles/desktop). La interfaz permite cambiar a un backend
// (Express + PostgreSQL) sin tocar el resto del juego.
const PROFILES_KEY = 'el_litigante_profiles_v1';
const ACTIVE_KEY = 'el_litigante_active_v1';
const SETTINGS_KEY = 'el_litigante_settings_v1';

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export const defaultSettings = (): Settings => ({
  theme: 'dark',
  fontScale: 1,
  colorblind: false,
  music: true,
  sfx: true,
});

const emptyStats = (): Stats => ({
  enemies: 0,
  documents: 0,
  trivia: 0,
  perfectLevels: 0,
  minutes: 0,
  sessions: 0,
  bossPerfect: 0,
});

export function createProfile(name: string, difficulty: string): SaveProfile {
  return {
    id: 'p_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    name: name.trim() || 'Litigante',
    createdAt: Date.now(),
    difficulty,
    lex: 0,
    xp: 0,
    charLevel: 1,
    skills: {},
    levelsCompleted: [],
    worldsCompleted: [],
    bossesDefeated: [],
    lessonsRead: [],
    achievements: [],
    difficultyWorldsDone: [],
    stats: emptyStats(),
  };
}

class Store {
  content!: Content;
  settings: Settings = defaultSettings();
  profiles: SaveProfile[] = [];
  activeId: string | null = null;
  /** Mundo seleccionado para jugar (id). */
  selectedWorld: string | null = null;

  init(content: Content) {
    this.content = content;
    this.settings = safeParse(localStorage.getItem(SETTINGS_KEY), defaultSettings());
    this.profiles = safeParse<SaveProfile[]>(localStorage.getItem(PROFILES_KEY), []);
    this.activeId = localStorage.getItem(ACTIVE_KEY);
    // Normaliza perfiles antiguos por si cambió el esquema.
    this.profiles.forEach((p) => {
      p.stats = { ...emptyStats(), ...(p.stats || {}) };
      p.skills = p.skills || {};
      p.achievements = p.achievements || [];
    });
  }

  get active(): SaveProfile | null {
    return this.profiles.find((p) => p.id === this.activeId) || null;
  }

  addProfile(p: SaveProfile) {
    this.profiles.push(p);
    this.activeId = p.id;
    this.persistProfiles();
  }

  setActive(id: string) {
    this.activeId = id;
    localStorage.setItem(ACTIVE_KEY, id);
  }

  deleteProfile(id: string) {
    this.profiles = this.profiles.filter((p) => p.id !== id);
    if (this.activeId === id) this.activeId = this.profiles[0]?.id ?? null;
    this.persistProfiles();
  }

  persistProfiles() {
    localStorage.setItem(PROFILES_KEY, JSON.stringify(this.profiles));
    if (this.activeId) localStorage.setItem(ACTIVE_KEY, this.activeId);
  }

  saveSettings() {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
  }
}

export const store = new Store();
