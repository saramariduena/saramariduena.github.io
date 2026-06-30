import Phaser from 'phaser';

// Bus de eventos para desacoplar el HUD de la escena de nivel.
export const bus = new Phaser.Events.EventEmitter();

export interface HudState {
  lives: number;
  maxLives: number;
  shields: number;
  lex: number;
  charLevel: number;
  worldTitle: string;
  levelTitle: string;
  bossHp?: number;
  bossMaxHp?: number;
  bossName?: string;
}
