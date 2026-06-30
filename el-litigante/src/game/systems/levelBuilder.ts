import type { GeneratorParams } from '../../core/types';

// Construcción de niveles a partir de DATOS:
//  - Si el nivel trae `layout` (mundo 1, hecho a mano) se parsea tal cual.
//  - Si el mundo trae `generator`, se generan niveles deterministas por semilla.
// Así se pueden añadir mundos/niveles sin escribir código nuevo.

export interface Cell {
  col: number;
  row: number;
}

export interface ParsedLevel {
  cols: number;
  rows: number;
  ground: Cell[];
  platforms: Cell[];
  coins: Cell[];
  docs: Cell[];
  enemies: Cell[];
  hazards: Cell[];
  player: Cell;
  flag: Cell;
}

export function parseLayout(layout: string[]): ParsedLevel {
  const rows = layout.length;
  const cols = layout.reduce((m, r) => Math.max(m, r.length), 0);
  const out: ParsedLevel = {
    cols,
    rows,
    ground: [],
    platforms: [],
    coins: [],
    docs: [],
    enemies: [],
    hazards: [],
    player: { col: 1, row: rows - 4 },
    flag: { col: cols - 2, row: rows - 4 },
  };
  for (let r = 0; r < rows; r++) {
    const line = layout[r];
    for (let c = 0; c < line.length; c++) {
      const ch = line[c];
      const cell = { col: c, row: r };
      switch (ch) {
        case '#':
          out.ground.push(cell);
          break;
        case '=':
          out.platforms.push(cell);
          break;
        case 'c':
          out.coins.push(cell);
          break;
        case 'd':
          out.docs.push(cell);
          break;
        case 'e':
          out.enemies.push(cell);
          break;
        case '^':
          out.hazards.push(cell);
          break;
        case 'P':
          out.player = cell;
          break;
        case 'F':
          out.flag = cell;
          break;
      }
    }
  }
  return out;
}

// PRNG determinista (mulberry32).
function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function generateLayout(params: GeneratorParams, levelIndex: number): string[] {
  const rand = rng(params.seed + levelIndex * 977);
  const ROWS = 12;
  const groundTop = ROWS - 3; // filas 9,10,11 = suelo
  const entityRow = groundTop - 1; // fila 8
  const width = Math.max(24, params.width);
  const grid: string[][] = Array.from({ length: ROWS }, () => Array(width).fill(' '));

  // Suelo con pocos huecos y siempre saltables (1-2 columnas).
  let c = 0;
  while (c < width) {
    const makeGap = c > 6 && c < width - 6 && rand() < 0.06;
    if (makeGap) {
      const gap = 1 + Math.floor(rand() * 2); // 1-2 columnas
      c += gap;
    } else {
      for (let r = groundTop; r < ROWS; r++) grid[r][c] = '#';
      c++;
    }
  }

  // Inicio y meta (garantiza suelo debajo).
  for (let r = groundTop; r < ROWS; r++) {
    grid[r][1] = '#';
    grid[r][width - 2] = '#';
  }
  grid[entityRow][1] = 'P';
  grid[entityRow][width - 2] = 'F';

  // Plataformas flotantes con monedas/enemigos encima.
  for (let x = 4; x < width - 4; x += 1) {
    if (rand() < params.platformDensity / 4) {
      const len = 2 + Math.floor(rand() * 3);
      const py = 3 + Math.floor(rand() * 4); // filas 3-6
      for (let k = 0; k < len && x + k < width - 3; k++) {
        grid[py][x + k] = '=';
        if (rand() < params.coinDensity * 2) grid[py - 1][x + k] = 'c';
      }
      if (rand() < params.enemyDensity * 2) grid[py - 1][x] = 'e';
      if (rand() < 0.15) grid[py - 1][x + len - 1] = 'd';
      x += len;
    }
  }

  // Enemigos y peligros en el suelo.
  for (let x = 5; x < width - 4; x++) {
    const hasGround = grid[groundTop][x] === '#';
    if (!hasGround) continue;
    if (grid[entityRow][x] !== ' ') continue;
    // Densidades reducidas para que sea más accesible.
    if (rand() < params.enemyDensity * 0.6) grid[entityRow][x] = 'e';
    else if (rand() < params.hazardDensity * 0.5) grid[entityRow][x] = '^';
    else if (rand() < params.coinDensity) grid[entityRow][x] = 'c';
  }

  return grid.map((row) => row.join(''));
}
