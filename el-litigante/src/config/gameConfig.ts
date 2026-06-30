// Constantes globales del motor.
export const GAME_WIDTH = 1280;
export const GAME_HEIGHT = 720;
export const TILE = 64;
export const GRAVITY_Y = 1500;

export const BASE_MOVE_SPEED = 220;
export const RUN_MULTIPLIER = 1.6;
export const JUMP_VELOCITY = -620;

// Paletas de tema (modo claro / oscuro) para los menús.
export const THEME = {
  dark: {
    bg: 0x0b1d33,
    panel: 0x13294b,
    text: '#eaf2ff',
    textDim: '#9fb3d1',
    accent: 0xf5d547,
    accentText: '#0b1d33',
    danger: 0xc0392b,
  },
  light: {
    bg: 0xeef4fb,
    panel: 0xffffff,
    text: '#13294b',
    textDim: '#4a5b78',
    accent: 0x2d6cdf,
    accentText: '#ffffff',
    danger: 0xc0392b,
  },
};

export type ThemeName = keyof typeof THEME;
