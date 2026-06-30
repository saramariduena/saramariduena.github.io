import Phaser from 'phaser';
import { TEX } from '../systems/assets';
import { controls } from '../systems/controls';
import { bus, type HudState } from '../systems/bus';
import { store } from '../../core/store';

export class HudScene extends Phaser.Scene {
  private heartsBox!: Phaser.GameObjects.Container;
  private lexText!: Phaser.GameObjects.Text;
  private lvlText!: Phaser.GameObjects.Text;
  private titleText!: Phaser.GameObjects.Text;
  private bossBarBg?: Phaser.GameObjects.Rectangle;
  private bossBar?: Phaser.GameObjects.Rectangle;
  private bossLabel?: Phaser.GameObjects.Text;

  constructor() {
    super('Hud');
  }

  create() {
    const w = this.scale.width;
    const fontWhite = { fontFamily: 'Segoe UI, sans-serif', color: '#ffffff', fontStyle: 'bold', stroke: '#0b1d33', strokeThickness: 4 };

    this.add.rectangle(0, 0, w, 56, 0x000000, 0.28).setOrigin(0, 0).setScrollFactor(0);
    this.heartsBox = this.add.container(16, 28).setScrollFactor(0);
    this.lexText = this.add.text(220, 16, '0 LEX', { ...fontWhite, fontSize: '22px' }).setScrollFactor(0);
    this.lvlText = this.add.text(360, 16, 'Nv 1', { ...fontWhite, fontSize: '22px' }).setScrollFactor(0);
    this.titleText = this.add.text(w / 2, 16, '', { ...fontWhite, fontSize: '20px' }).setOrigin(0.5, 0).setScrollFactor(0);

    // Botón de pausa.
    const pause = this.add.text(w - 20, 14, '⏸', { fontSize: '30px', color: '#ffffff' }).setOrigin(1, 0).setScrollFactor(0).setInteractive({ useHandCursor: true });
    pause.on('pointerup', () => bus.emit('ui:pause'));

    this.buildTouchControls();

    bus.on('hud:update', this.onUpdate, this);
    this.events.once('shutdown', () => bus.off('hud:update', this.onUpdate, this));
    // Pide a la escena de nivel el estado inicial (evita carrera de eventos).
    bus.emit('hud:request');
  }

  private buildTouchControls() {
    const showTouch = this.game.device.input.touch || this.scale.width < 820;
    const alpha = showTouch ? 0.45 : 0.18;
    const h = this.scale.height;

    const mkPad = (x: number, y: number, label: string) => {
      const c = this.add.circle(x, y, 46, 0xffffff, alpha).setScrollFactor(0).setInteractive({ useHandCursor: true });
      this.add.text(x, y, label, { fontSize: '34px', color: '#0b1d33', fontStyle: 'bold' }).setOrigin(0.5).setScrollFactor(0);
      return c;
    };

    const left = mkPad(80, h - 80, '◀');
    const right = mkPad(190, h - 80, '▶');
    const run = mkPad(this.scale.width - 200, h - 70, '»');
    const jump = mkPad(this.scale.width - 80, h - 90, '▲');

    const bind = (obj: Phaser.GameObjects.Shape, key: 'left' | 'right' | 'jump' | 'run') => {
      obj.on('pointerdown', () => (controls[key] = true));
      obj.on('pointerup', () => (controls[key] = false));
      obj.on('pointerout', () => (controls[key] = false));
    };
    bind(left, 'left');
    bind(right, 'right');
    bind(jump, 'jump');
    bind(run, 'run');
  }

  private onUpdate(s: HudState) {
    this.heartsBox.removeAll(true);
    for (let i = 0; i < s.maxLives; i++) {
      const img = this.add.image(i * 32, 0, TEX.heart).setScale(0.9);
      if (i >= s.lives) img.setAlpha(0.25).setTint(0x555555);
      this.heartsBox.add(img);
    }
    for (let i = 0; i < s.shields; i++) {
      const img = this.add.image(s.maxLives * 32 + i * 30, 0, TEX.shield).setScale(0.8);
      this.heartsBox.add(img);
    }
    this.lexText.setText(`${s.lex} LEX`);
    this.lvlText.setText(`Nv ${s.charLevel}`);
    this.titleText.setText(`${s.worldTitle} — ${s.levelTitle}`);

    if (s.bossHp !== undefined && s.bossMaxHp) {
      const w = this.scale.width;
      if (!this.bossBarBg) {
        this.bossBarBg = this.add.rectangle(w / 2, 70, 400, 22, 0x000000, 0.5).setScrollFactor(0);
        this.bossBar = this.add.rectangle(w / 2 - 198, 70, 396, 16, 0xc0392b).setOrigin(0, 0.5).setScrollFactor(0);
        this.bossLabel = this.add.text(w / 2, 92, '', { fontFamily: 'Segoe UI', fontSize: '14px', color: '#ffffff' }).setOrigin(0.5).setScrollFactor(0);
      }
      this.bossBar!.width = 396 * Math.max(0, s.bossHp / s.bossMaxHp);
      this.bossLabel!.setText(s.bossName || '');
    }
    void store;
  }
}
