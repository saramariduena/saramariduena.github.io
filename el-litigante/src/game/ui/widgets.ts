import Phaser from 'phaser';
import { THEME } from '../../config/gameConfig';
import { store } from '../../core/store';

// Helpers de UI reutilizables para los menús (botones, paneles, títulos) que
// respetan el tema y la escala de fuente configurados por el jugador.

export function theme() {
  const base = THEME[store.settings.theme];
  // Modo daltónico: paleta de alto contraste (azul/naranja Okabe-Ito).
  if (store.settings.colorblind) {
    return { ...base, accent: 0x0072b2, accentText: '#ffffff', danger: 0xd55e00 };
  }
  return base;
}

export function fs(size: number): string {
  return `${Math.round(size * store.settings.fontScale)}px`;
}

export interface ButtonOpts {
  width?: number;
  height?: number;
  fontSize?: number;
  primary?: boolean;
  danger?: boolean;
}

export function makeButton(
  scene: Phaser.Scene,
  x: number,
  y: number,
  label: string,
  onClick: () => void,
  opts: ButtonOpts = {}
): Phaser.GameObjects.Container {
  const t = theme();
  const w = opts.width ?? 360;
  const h = opts.height ?? 64;
  const baseColor = opts.danger ? t.danger : opts.primary ? t.accent : t.panel;
  const textColor = opts.primary && !opts.danger ? t.accentText : opts.danger ? '#ffffff' : t.text;

  const bg = scene.add.rectangle(0, 0, w, h, baseColor, 1).setStrokeStyle(2, 0x000000, 0.15);
  bg.setInteractive({ useHandCursor: true });
  const txt = scene.add
    .text(0, 0, label, {
      fontFamily: 'Segoe UI, system-ui, sans-serif',
      fontSize: fs(opts.fontSize ?? 24),
      color: textColor,
      fontStyle: 'bold',
    })
    .setOrigin(0.5);

  const container = scene.add.container(x, y, [bg, txt]);
  container.setSize(w, h);

  bg.on('pointerover', () => bg.setScale(1.04));
  bg.on('pointerout', () => bg.setScale(1));
  bg.on('pointerdown', () => bg.setScale(0.97));
  bg.on('pointerup', () => {
    bg.setScale(1.04);
    onClick();
  });
  return container;
}

export function title(scene: Phaser.Scene, x: number, y: number, text: string, size = 56) {
  return scene.add
    .text(x, y, text, {
      fontFamily: 'Georgia, serif',
      fontSize: fs(size),
      color: theme().text,
      fontStyle: 'bold',
    })
    .setOrigin(0.5);
}

export function label(scene: Phaser.Scene, x: number, y: number, text: string, size = 20, dim = false) {
  return scene.add
    .text(x, y, text, {
      fontFamily: 'Segoe UI, system-ui, sans-serif',
      fontSize: fs(size),
      color: dim ? theme().textDim : theme().text,
      align: 'center',
      wordWrap: { width: 900 },
    })
    .setOrigin(0.5);
}

export function paintBackground(scene: Phaser.Scene) {
  const t = theme();
  scene.cameras.main.setBackgroundColor(t.bg);
}

// Modal de confirmación reutilizable (Sí / No).
export function confirmDialog(
  scene: Phaser.Scene,
  message: string,
  onYes: () => void,
  yesLabel = 'Sí',
  noLabel = 'No'
) {
  const t = theme();
  const w = scene.scale.width;
  const h = scene.scale.height;
  const layer = scene.add.container(0, 0).setDepth(10000).setScrollFactor(0);
  const shade = scene.add.rectangle(w / 2, h / 2, w, h, 0x000000, 0.6).setInteractive();
  const panel = scene.add.rectangle(w / 2, h / 2, 560, 240, t.panel, 1).setStrokeStyle(3, t.accent);
  const msg = scene.add
    .text(w / 2, h / 2 - 50, message, {
      fontFamily: 'Segoe UI, sans-serif',
      fontSize: fs(26),
      color: t.text,
      align: 'center',
      wordWrap: { width: 500 },
    })
    .setOrigin(0.5);
  layer.add([shade, panel, msg]);

  const yes = makeButton(scene, w / 2 - 130, h / 2 + 50, yesLabel, () => {
    layer.destroy();
    onYes();
  }, { width: 220, height: 60, primary: true });
  const no = makeButton(scene, w / 2 + 130, h / 2 + 50, noLabel, () => layer.destroy(), {
    width: 220,
    height: 60,
  });
  layer.add([yes, no]);
  return layer;
}
