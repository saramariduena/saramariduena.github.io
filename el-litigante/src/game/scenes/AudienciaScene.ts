import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, theme, fs } from '../ui/widgets';
import { rankIndex, prepPoints, convictionBonus } from '../../core/ranks';
import type { LegalCase, CaseStage, CaseOption, Instancia } from '../../core/types';

const NAMES: Record<string, string> = {
  juez: 'Juez',
  contraparte: 'Abogado contrario',
  cliente: 'Tu clienta',
  secretario: 'Secretario',
  testigo: 'Testigo',
  mediador: 'Mediador/a',
};

// Tintes de ambiente para dar variedad de color a cada caso.
const AMBIENTS = [0xffffff, 0xffe6c8, 0xd6e6ff, 0xe2ffd9, 0xf2d9ff, 0xffd9d9, 0xfff2c8, 0xd2fff0, 0xffe0ef, 0xdfe0ff];
const INSTANCIA_TINT: Record<Instancia, number> = { primera: 0, apelacion: 0xc8d4ff, casacion: 0xc0c4e8 };

const SLOTS: Record<string, Record<string, { x: number; y: number; flip: boolean; scale: number }>> = {
  oficina: {
    tu: { x: 320, y: 560, flip: false, scale: 1.4 },
    cliente: { x: 960, y: 560, flip: true, scale: 1.4 },
    secretario: { x: 960, y: 560, flip: true, scale: 1.4 },
    testigo: { x: 960, y: 560, flip: true, scale: 1.4 },
    mediador: { x: 640, y: 545, flip: false, scale: 1.45 },
  },
  sala: {
    juez: { x: 640, y: 422, flip: false, scale: 1.15 },
    tu: { x: 280, y: 560, flip: false, scale: 1.25 },
    contraparte: { x: 1000, y: 560, flip: true, scale: 1.25 },
    testigo: { x: 640, y: 560, flip: false, scale: 1.15 },
    secretario: { x: 470, y: 560, flip: false, scale: 1.0 },
    cliente: { x: 150, y: 560, flip: false, scale: 1.15 },
    mediador: { x: 640, y: 545, flip: false, scale: 1.3 },
  },
};

export class AudienciaScene extends Phaser.Scene {
  private caso!: LegalCase;
  private etapas: CaseStage[] = [];
  private instancia: Instancia = 'primera';
  private ambient = 0xffffff;
  private stageIndex = 0;
  private dialogIndex = 0;
  private conviccion = 50;
  private correct = 0;
  private answered = 0;
  private pp = 2;
  private ppText!: Phaser.GameObjects.Text;
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

  init(data: { caseId: string; instancia?: Instancia }) {
    this.caso = store.content.cases.find((c) => c.id === data.caseId)!;
    this.instancia = data.instancia || 'primera';
    this.etapas = this.instancia === 'primera' ? this.caso.etapas : store.content.instancias[this.instancia];
    const idx = store.content.cases.findIndex((c) => c.id === this.caso.id);
    this.ambient = AMBIENTS[idx % AMBIENTS.length];
    if (this.instancia !== 'primera' && INSTANCIA_TINT[this.instancia]) this.ambient = INSTANCIA_TINT[this.instancia];
    this.stageIndex = 0;
    this.dialogIndex = 0;
    const tier = store.active ? rankIndex(store.content.ranks, store.active) : 0;
    const base = this.instancia === 'primera' ? 50 : this.instancia === 'apelacion' ? 44 : 42;
    this.conviccion = Math.min(70, base + (this.instancia === 'primera' ? convictionBonus(tier) : 0));
    this.pp = prepPoints(tier);
    this.correct = 0;
    this.answered = 0;
    this.mode = 'dialog';
    this.chars = {};
  }

  private displayName(quien: string): string {
    if (quien === 'tu') return store.active?.gender === 'f' ? 'Tú (abogada)' : 'Tú (abogado)';
    return NAMES[quien] || quien;
  }

  create() {
    this.bg = this.add.image(GAME_WIDTH / 2, GAME_HEIGHT / 2, SCENE_TEX.oficina).setDepth(0);

    this.buildMeter();
    this.buildDialogBox();

    const instLabel = this.instancia === 'primera' ? '1ª instancia' : this.instancia === 'apelacion' ? 'Apelación · 2ª instancia' : 'Casación';
    this.add.text(16, 66, `${this.caso.titulo}  ·  ${instLabel}`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#ffffff', fontStyle: 'bold', stroke: '#0b1d33', strokeThickness: 4 }).setDepth(95);
    this.ppText = this.add.text(16, 90, '', { fontFamily: 'Segoe UI', fontSize: fs(15), color: '#ffe066', fontStyle: 'bold', stroke: '#0b1d33', strokeThickness: 4 }).setDepth(95);
    this.updatePp();

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
    const quienConvence = this.caso.tipo === 'mediacion' ? 'Acuerdo' : 'Convicción';
    this.meterLabel.setText(`${quienConvence}: ${Math.round(this.conviccion)}%  (meta ${this.caso.meta}%)`);
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
    const stage = this.etapas[this.stageIndex];
    this.bg.setTexture(stage.lugar === 'sala' ? SCENE_TEX.sala : SCENE_TEX.oficina);
    if (this.ambient && this.ambient !== 0xffffff) this.bg.setTint(this.ambient);
    else this.bg.clearTint();
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
      const tex =
        quien === 'tu'
          ? store.active?.gender === 'f'
            ? SCENE_TEX.tu_f
            : SCENE_TEX.tu
          : (SCENE_TEX as Record<string, string>)[quien] || SCENE_TEX.tu;
      const spr = this.add.sprite(slot.x, slot.y, tex).setOrigin(0.5, 1).setDepth(10);
      spr.setScale(slot.scale);
      spr.setFlipX(slot.flip);
      this.chars[quien] = spr;
    });
  }

  private renderDialog() {
    const stage = this.etapas[this.stageIndex];
    const d = stage.dialogos[this.dialogIndex];
    if (!d) {
      // No quedan diálogos: decisión o siguiente etapa.
      if (stage.decision) this.showDecision();
      else this.nextStage();
      return;
    }
    this.speakerText.setText(`【 ${this.displayName(d.quien)} 】`);
    this.bodyText.setText(d.texto);
    this.highlightSpeaker(d.quien);
  }

  private highlightSpeaker(quien: string) {
    Object.entries(this.chars).forEach(([k, spr]) => {
      const active = k === quien;
      spr.setAlpha(active ? 1 : 0.78);
      this.tweens.killTweensOf(spr);
      const baseScale = (SLOTS[this.etapas[this.stageIndex].lugar][k] || { scale: 1.2 }).scale;
      spr.setScale(active ? baseScale * 1.06 : baseScale);
      if (active) this.tweens.add({ targets: spr, y: spr.y - 8, duration: 220, yoyo: true });
    });
  }

  private advanceDialog() {
    this.dialogIndex += 1;
    this.renderDialog();
  }

  // ---- Decisión ----
  private optionEntries: { btn: Phaser.GameObjects.Container; opt: CaseOption; eliminated: boolean }[] = [];
  private investBtn?: Phaser.GameObjects.Container;

  private updatePp() {
    this.ppText.setText(`💡 Preparación: ${this.pp}`);
  }

  private showDecision() {
    const stage = this.etapas[this.stageIndex];
    const dec = stage.decision!;
    this.mode = 'decision';
    this.dialogBox.setVisible(false);

    const layer = this.add.container(0, 0).setDepth(120);
    const panelY = GAME_HEIGHT - 210;
    layer.add(this.add.rectangle(GAME_WIDTH / 2, panelY, GAME_WIDTH - 60, 360, 0x0b1d33, 0.95).setStrokeStyle(3, 0xf5d547));
    layer.add(this.add.text(GAME_WIDTH / 2, panelY - 152, '⚖️ ' + dec.pregunta, { fontFamily: 'Segoe UI', fontSize: fs(21), color: '#ffffff', fontStyle: 'bold', align: 'center', wordWrap: { width: GAME_WIDTH - 140 } }).setOrigin(0.5));

    this.optionEntries = [];
    dec.opciones.forEach((opt, i) => {
      const btn = makeButton(this, GAME_WIDTH / 2, panelY - 92 + i * 60, opt.texto, () => this.choose(opt, dec.articulo), { width: GAME_WIDTH - 160, height: 50, fontSize: 16 });
      layer.add(btn);
      this.optionEntries.push({ btn, opt, eliminated: false });
    });

    // Recurso: "Investigar" descarta una opción incorrecta (cuesta 1 Preparación).
    this.investBtn = makeButton(this, GAME_WIDTH / 2, panelY + 130, '💡 Investigar — descarta una opción mala (1 PP)', () => this.investigate(), { width: 520, height: 44, fontSize: 15 });
    layer.add(this.investBtn);
    this.refreshInvest();
    this.decisionLayer = layer;
  }

  private investigate() {
    if (this.pp <= 0) return;
    const cand = this.optionEntries.filter((e) => !e.eliminated && e.opt.conviccion <= 0);
    if (!cand.length) return;
    const target = cand[0];
    target.eliminated = true;
    (target.btn.list[0] as Phaser.GameObjects.Rectangle).disableInteractive();
    target.btn.setAlpha(0.3);
    this.add.tween({ targets: target.btn, scale: 0.96, duration: 150 });
    this.pp -= 1;
    this.updatePp();
    this.refreshInvest();
  }

  private refreshInvest() {
    if (!this.investBtn) return;
    const wrongLeft = this.optionEntries.some((e) => !e.eliminated && e.opt.conviccion <= 0);
    const usable = this.pp > 0 && wrongLeft;
    this.investBtn.setAlpha(usable ? 1 : 0.4);
    const bg = this.investBtn.list[0] as Phaser.GameObjects.Rectangle;
    if (usable) bg.setInteractive({ useHandCursor: true });
    else bg.disableInteractive();
  }

  private choose(opt: CaseOption, articulo: string) {
    if (this.mode !== 'decision') return;
    // Una opción descartada no se puede elegir.
    if (this.optionEntries.find((e) => e.opt === opt)?.eliminated) return;
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
    if (this.stageIndex >= this.etapas.length) {
      this.scene.start('Verdict', {
        caseId: this.caso.id,
        instancia: this.instancia,
        conviccion: Math.round(this.conviccion),
        correct: this.correct,
        answered: this.answered,
      });
    } else {
      this.showStage();
    }
  }
}
