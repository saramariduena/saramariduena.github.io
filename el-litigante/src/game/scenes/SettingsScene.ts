import Phaser from 'phaser';
import { GAME_WIDTH } from '../../config/gameConfig';
import { store } from '../../core/store';
import { makeButton, title, label, paintBackground } from '../ui/widgets';

export class SettingsScene extends Phaser.Scene {
  constructor() {
    super('Settings');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    title(this, cx, 70, 'Configuración', 44);

    const s = store.settings;
    let y = 170;
    const gap = 76;

    const row = (text: string, value: string, onClick: () => void) => {
      label(this, cx - 220, y, text, 22);
      makeButton(this, cx + 180, y, value, () => {
        onClick();
        store.saveSettings();
        this.scene.restart();
      }, { width: 320, height: 56 });
      y += gap;
    };

    row('Tema', s.theme === 'dark' ? 'Oscuro 🌙' : 'Claro ☀️', () => (s.theme = s.theme === 'dark' ? 'light' : 'dark'));
    row('Tamaño de letra', `${Math.round(s.fontScale * 100)}%`, () => {
      const steps = [0.85, 1, 1.15, 1.3];
      const idx = steps.indexOf(s.fontScale);
      s.fontScale = steps[(idx + 1) % steps.length] ?? 1;
    });
    row('Modo daltónico', s.colorblind ? 'Activado' : 'Desactivado', () => (s.colorblind = !s.colorblind));
    row('Música', s.music ? 'Activada' : 'Desactivada', () => (s.music = !s.music));
    row('Efectos de sonido', s.sfx ? 'Activados' : 'Desactivados', () => (s.sfx = !s.sfx));

    label(this, cx, y + 10, 'Controles: ◀ ▶ moverse · ↑/Espacio saltar (doble salto) · Shift correr · ESC pausa. También táctil y gamepad.', 14, true);

    makeButton(this, cx, y + 70, 'Volver al menú', () => this.scene.start('Menu'), { width: 260, height: 56, primary: true });
  }
}
