import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT, GRAVITY_Y } from './config/gameConfig';
import { store } from './core/store';
import { evaluateAchievements } from './core/achievements';
import { PreloadScene } from './game/scenes/PreloadScene';
import { MenuScene } from './game/scenes/MenuScene';
import { DifficultyScene } from './game/scenes/DifficultyScene';
import { WorldSelectScene } from './game/scenes/WorldSelectScene';
import { LevelScene } from './game/scenes/LevelScene';
import { HudScene } from './game/scenes/HudScene';
import { LessonScene } from './game/scenes/LessonScene';
import { SettingsScene } from './game/scenes/SettingsScene';
import { AchievementsScene } from './game/scenes/AchievementsScene';
import { ProfileScene } from './game/scenes/ProfileScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: 'game-root',
  width: GAME_WIDTH,
  height: GAME_HEIGHT,
  backgroundColor: '#0b1d33',
  pixelArt: false,
  roundPixels: true,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  physics: {
    default: 'arcade',
    arcade: { gravity: { x: 0, y: GRAVITY_Y }, debug: false },
  },
  input: { gamepad: true },
  scene: [
    PreloadScene,
    MenuScene,
    DifficultyScene,
    WorldSelectScene,
    LevelScene,
    HudScene,
    LessonScene,
    SettingsScene,
    AchievementsScene,
    ProfileScene,
  ],
};

const game = new Phaser.Game(config);
// Acceso para depuración desde la consola del navegador.
(window as unknown as { __game: Phaser.Game }).__game = game;

// Conteo de tiempo jugado (estadística + logros) cada minuto.
setInterval(() => {
  const a = store.active;
  if (!a) return;
  a.stats.minutes += 1;
  evaluateAchievements(a, store.content);
  store.persistProfiles();
}, 60000);
