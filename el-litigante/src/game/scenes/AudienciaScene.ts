import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, theme, fs } from '../ui/widgets';
import type { LegalCase, CaseStage, CaseOption } from '../../core/types';

const NAMES: Record<string, string> = {
  tu: 'Tú (abogado/a)',
  juez: 'Juez',
  contraparte: 'Abogado contrario',
  cliente: 'Tu clienta',
  secretario: 'Secretario',
  testigo: 'Testigo',
};

const SLOTS: Record<string, Record<string, { x: number; y: number; flip: boolean; scale: number }>> = {
  oficina: {
    tu: { x: 360, y: 560, flip: false, scale: 1.4 },
    cliente: { x: 940, y: 560, flip: true, scale: 1.4 },
    secretario: { x: 940, y: 560, flip: true, scale: 1.4 },
    testigo: { x: 940, y: 560, flip: true, scale: 1.4 },
  },
  sala: {
    juez: { x: 640, y: 422, flip: false, scale: 1.15 },
    tu: { x: 280, y: 560, flip: false, scale: 1.25 },
    contraparte: { x: 1000, y: 560, flip: true, scale: 1.25 },
    testigo: { x: 640, y: 560, flip: false, scale: 1.15 },
    secretario: { x: 470, y: 560, flip: false, scale: 1.0 },
    cliente: { x: 280, y: 560, flip: false, scale: 1.25 },
  },
};

export class AudienciaScene extends Phaser.Scene {
  private caso!: LegalCase;
  private stageIndex = 0;
  private dialogIndex = 0;
  private conviccion = 50;
  private correct = 0;
  private answered = 0;
  private mode: 'dialog' | 'decision' | 'feedback' = 'dialog';

  private bg!: Phaser.GameObjects.Image;
  private chars: Record<string, Phaser.GameObjects.Sprite> = {};
  private dialogBox!: Phaser.GameObjects.Container;
  private speakerText!: Phaser.GameObjects.Text;
  private bodyText!: Phaser.GameObjects.Text;
  private hintText!: Phaser.GameObjects.Text;
  private meterFill!: Phaser.GameObjects.Rectangle;
  private meterLabel!: Phaser.GameObjects.Text;
  private decisionLayer?: Phaser.GameObjects.Container;

  constructor() {
    super('Audiencia');
  }

  init(data: { caseId: string }) {
    this.caso = store.content.cases.find((c) => c.id === data.caseId)!;
    this.stageIndex = 0;
    this.dialogIndex = 0;
    this.conviccion = 50;
    this.correct = 0;
    this.answered = 0;
    this.mode = 'dialog';
    this.chars = {};
  }

  create() {
    this.bg = this.add.image(GAME_WIDTH / 2, GAME_HEIGHT / 2, SCENE_TEX.oficina).setDepth(0);

    this.buildMeter();
    this.buildDialogBox();

    // Avanzar diálogo tocando o con tecla (solo en modo diálogo).
    this.input.on('pointerup', () => {
      if (this.mode === 'dialog') this.advanceDialog();
    });
    this.input.keyboard!.on('keydown-SPACE', () => {
      if (this.mode === 'dialog') this.advanceDialog();
    });
    this.input.keyboard!.on('keydown-ENTER', () => {
      if (this.mode === 'dialog') this.advanceDialog();
    });

    // Botón salir.
    const exit = this.add.text(GAME_WIDTH - 16, 14, '✕ Salir', { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#ffffff', fontStyle: 'bold', stroke: '#0b1d33', strokeThickness: 4 }).setOrigin(1, 0).setDepth(100).setInteractive({ useHandCursor: true });
    exit.on('pointerup', () => this.scene.start('CaseSelect'));

    this.showStage();
  }

  // ---- UI ----
  private buildMeter() {
    const w = 520;
    this.add.rectangle(GAME_WIDTH / 2, 40, w + 8, 34, 0x0b1d33, 0.85).setDepth(90);
    this.add.rectangle(GAME_WIDTH / 2 - w / 2, 40, w, 22, 0x33415c, 1).setOrigin(0, 0.5).setDepth(91);
    this.meterFill = this.add.rectangle(GAME_WIDTH / 2 - w / 2, 40, w * 0.5, 22, 0x3ad07a, 1).setOrigin(0, 0.5).setDepth(92);
    this.meterLabel = this.add.text(GAME_WIDTH / 2, 40, '', { fontFamily: 'Segoe UI', fontSize: fs(15), color: '#ffffff', fontStyle: 'bold' }).setOrigin(0.5).setDepth(93);
    this.updateMeter(false);
  }

  private updateMeter(animate = true) {
    const w = 520;
    const ratio = Phaser.Math.Clamp(this.conviccion / 100, 0, 1);
    const color = this.conviccion >= this.caso.meta ? 0x3ad07a : this.conviccion >= this.caso.meta - 15 ? 0xf5a623 : 0xe25555;
    this.meterFill.setFillStyle(color);
    this.meterLabel.setText(`Convicción del juez: ${Math.round(this.conviccion)}%  (meta ${this.caso.meta}%)`);
    if (animate) this.tweens.add({ targets: this.meterFill, width: w * ratio, duration: 400, ease: 'Sine.out' });
    else this.meterFill.width = w * ratio;
  }

  private buildDialogBox() {
    const t = theme();
    const boxY = GAME_HEIGHT - 90;
    this.dialogBox = this.add.container(0, 0).setDepth(80);
    const bg = this.add.rectangle(GAME_WIDTH / 2, boxY, GAME_WIDTH - 60, 150, 0x0b1d33, 0.92).setStrokeStyle(3, 0xf5d547);
    this.speakerText = this.add.text(60, boxY - 56, '', { fontFamily: 'Segoe UI', fontSize: fs(20), color: '#f5d547', fontStyle: 'bold' });
    this.bodyText = this.add.text(60, boxY - 26, '', { fontFamily: 'Segoe UI', fontSize: fs(19), color: '#ffffff', wordWrap: { width: GAME_WIDTH - 140 }, lineSpacing: 3 });
    this.hintText = this.add.text(GAME_WIDTH - 80, boxY + 44, '▶ toca para continuar', { fontFamily: 'Segoe UI', fontSize: fs(13), color: '#9fb3d1' }).setOrigin(1, 0.5);
    this.dialogBox.add([bg, this.speakerText, this.bodyText, this.hintText]);
  }

  // ---- Etapas ----
  private showStage() {
    const stage = this.caso.etapas[this.stageIndex];
    this.bg.setTexture(stage.lugar === 'sala' ? SCENE_TEX.sala : SCENE_TEX.oficina);
    this.placeCharacters(stage);
    this.dialogIndex = 0;
    this.mode = 'dialog';
    this.dialogBox.setVisible(true);
    this.renderDialog();
  }

  private placeCharacters(stage: CaseStage) {
    Object.values(this.chars).forEach((s) => s.destroy());
    this.chars = {};
    const present = new Set<string>(['tu']);
    stage.dialogos.forEach((d) => present.add(d.quien));
    if (stage.lugar === 'sala') present.add('juez');

    const slots = SLOTS[stage.lugar];
    present.forEach((quien) => {
      const slot = slots[quien] || slots['tu'];
      const tex = (SCENE_TEX as Record<string, string>)[quien] || SCENE_TEX.tu;
      const spr = this.add.sprite(slot.x, slot.y, tex).setOrigin(0.5, 1).setDepth(10);
      spr.setScale(slot.scale);
      spr.setFlipX(slot.flip);
      this.chars[quien] = spr;
    });
  }

  private renderDialog() {
    const stage = this.caso.etapas[this.stageIndex];
    const d = stage.dialogos[this.dialogIndex];
    if (!d) {
      // No quedan diálogos: decisión o siguiente etapa.
      if (stage.decision) this.showDecision();
      else this.nextStage();
      return;
    }
    this.speakerText.setText(`【 ${NAMES[d.quien] || d.quien} 】`);
    this.bodyText.setText(d.texto);
    this.highlightSpeaker(d.quien);
  }

  private highlightSpeaker(quien: string) {
    Object.entries(this.chars).forEach(([k, spr]) => {
      const active = k === quien;
      spr.setAlpha(active ? 1 : 0.78);
      this.tweens.killTweensOf(spr);
      const baseScale = (SLOTS[this.caso.etapas[this.stageIndex].lugar][k] || { scale: 1.2 }).scale;
      spr.setScale(active ? baseScale * 1.06 : baseScale);
      if (active) this.tweens.add({ targets: spr, y: spr.y - 8, duration: 220, yoyo: true });
    });
  }

  private advanceDialog() {
    this.dialogIndex += 1;
    this.renderDialog();
  }

  // ---- Decisión ----
  private showDecision() {
    const stage = this.caso.etapas[this.stageIndex];
    const dec = stage.decision!;
    this.mode = 'decision';
    this.dialogBox.setVisible(false);

    const t = theme();
    const layer = this.add.container(0, 0).setDepth(120);
    const panelY = GAME_HEIGHT - 210;
    layer.add(this.add.rectangle(GAME_WIDTH / 2, panelY, GAME_WIDTH - 60, 360, 0x0b1d33, 0.95).setStrokeStyle(3, 0xf5d547));
    layer.add(this.add.text(GAME_WIDTH / 2, panelY - 150, '⚖️ ' + dec.pregunta, { fontFamily: 'Segoe UI', fontSize: fs(22), color: '#ffffff', fontStyle: 'bold', align: 'center', wordWrap: { width: GAME_WIDTH - 140 } }).setOrigin(0.5));

    dec.opciones.forEach((opt, i) => {
      const btn = makeButton(this, GAME_WIDTH / 2, panelY - 90 + i * 64, opt.texto, () => this.choose(opt, dec.articulo), { width: GAME_WIDTH - 160, height: 54, fontSize: 17 });
      layer.add(btn);
    });
    this.decisionLayer = layer;
  }

  private choose(opt: CaseOption, articulo: string) {
    if (this.mode !== 'decision') return;
    this.mode = 'feedback';
    this.decisionLayer?.destroy();
    this.answered += 1;
    if (opt.conviccion > 0) this.correct += 1;
    this.conviccion = Phaser.Math.Clamp(this.conviccion + opt.conviccion, 0, 100);
    this.updateMeter(true);

    const positive = opt.conviccion > 0;
    const t = theme();
    const layer = this.add.container(0, 0).setDepth(120);
    const py = GAME_HEIGHT - 170;
    layer.add(this.add.rectangle(GAME_WIDTH / 2, py, GAME_WIDTH - 60, 260, 0x0b1d33, 0.96).setStrokeStyle(3, positive ? 0x3ad07a : 0xe25555));
    layer.add(this.add.text(GAME_WIDTH / 2, py - 95, positive ? '✅ Buena decisión' : '❌ Cuidado', { fontFamily: 'Segoe UI', fontSize: fs(22), color: positive ? '#3ad07a' : '#ff6b6b', fontStyle: 'bold' }).setOrigin(0.5));
    layer.add(this.add.text(GAME_WIDTH / 2, py - 35, opt.feedback, { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#ffffff', align: 'center', wordWrap: { width: GAME_WIDTH - 160 }, lineSpacing: 3 }).setOrigin(0.5));
    layer.add(this.add.text(GAME_WIDTH / 2, py + 35, '📜 ' + articulo, { fontFamily: 'Segoe UI', fontSize: fs(15), color: '#f5d547', align: 'center', wordWrap: { width: GAME_WIDTH - 160 } }).setOrigin(0.5));
    const cont = makeButton(this, GAME_WIDTH / 2, py + 85, 'Continuar ▶', () => {
      layer.destroy();
      this.nextStage();
    }, { width: 280, height: 50, primary: true });
    layer.add(cont);
  }

  private nextStage() {
    this.stageIndex += 1;
    if (this.stageIndex >= this.caso.etapas.length) {
      this.scene.start('Verdict', {
        caseId: this.caso.id,
        conviccion: Math.round(this.conviccion),
        correct: this.correct,
        answered: this.answered,
      });
    } else {
      this.showStage();
    }
  }
}
