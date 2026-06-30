import Phaser from 'phaser';
import { GAME_WIDTH } from '../../config/gameConfig';
import { store, createProfile } from '../../core/store';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

export class ProfileSetupScene extends Phaser.Scene {
  private gender: 'f' | 'm' = 'm';
  private nameDom!: Phaser.GameObjects.DOMElement;
  private chips: { rect: Phaser.GameObjects.Rectangle; txt: Phaser.GameObjects.Text; val: 'f' | 'm' }[] = [];
  private avatar!: Phaser.GameObjects.Image;

  constructor() {
    super('ProfileSetup');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    const t = theme();
    const existing = store.active;
    this.gender = existing?.gender || 'm';

    title(this, cx, 70, existing ? 'Editar tu perfil' : 'Crea tu perfil', 42);
    label(this, cx, 118, 'Escribe tu nombre y elige tu rol. Tu personaje y cómo te nombra el juez cambian.', 16, true);

    // Campo de texto REAL dentro del juego (reemplaza la ventanita que fallaba).
    label(this, cx, 178, 'Tu nombre:', 18);
    const style =
      'width:460px;height:48px;font-size:22px;text-align:center;border-radius:10px;border:3px solid #f5d547;background:#13294b;color:#ffffff;outline:none;font-family:Segoe UI,sans-serif;';
    this.nameDom = this.add.dom(cx, 220, 'input', style);
    const node = this.nameDom.node as HTMLInputElement;
    node.setAttribute('placeholder', 'Escribe aquí tu nombre');
    node.setAttribute('maxlength', '24');
    node.value = existing && existing.name !== 'Litigante' ? existing.name : '';
    setTimeout(() => node.focus(), 100);

    // Chips de rol.
    label(this, cx, 300, 'Soy:', 18);
    this.makeChip(cx - 170, 348, '👩‍⚖️ Abogada', 'f');
    this.makeChip(cx + 170, 348, '👨‍⚖️ Abogado', 'm');
    this.refreshChips();

    // Vista previa de tu personaje (a un lado, sin tapar los controles).
    this.add.text(1090, 250, 'Tu personaje', { fontFamily: 'Segoe UI', fontSize: fs(15), color: t.textDim }).setOrigin(0.5);
    this.avatar = this.add.image(1090, 470, this.gender === 'f' ? SCENE_TEX.tu_f : SCENE_TEX.tu).setScale(1.5);

    makeButton(this, cx, 470, existing ? 'Guardar ✓' : 'Comenzar ⚖️', () => this.confirm(), { width: 360, height: 64, primary: true, fontSize: 24 });
    makeButton(this, cx, 548, 'Volver al menú', () => this.scene.start('Menu'), { width: 240, height: 50 });
  }

  private makeChip(x: number, y: number, labelText: string, val: 'f' | 'm') {
    const t = theme();
    const rect = this.add.rectangle(x, y, 300, 56, t.panel, 1).setStrokeStyle(3, t.accent).setInteractive({ useHandCursor: true });
    const txt = this.add.text(x, y, labelText, { fontFamily: 'Segoe UI', fontSize: fs(20), color: t.text, fontStyle: 'bold' }).setOrigin(0.5);
    rect.on('pointerup', () => {
      this.gender = val;
      this.avatar.setTexture(val === 'f' ? SCENE_TEX.tu_f : SCENE_TEX.tu);
      this.refreshChips();
    });
    this.chips.push({ rect, txt, val });
  }

  private refreshChips() {
    const t = theme();
    this.chips.forEach((c) => {
      const sel = this.gender === c.val;
      c.rect.setFillStyle(sel ? t.accent : t.panel, 1);
      c.txt.setColor(sel ? t.accentText : t.text);
    });
  }

  private confirm() {
    const node = this.nameDom.node as HTMLInputElement;
    const name = (node.value || '').trim() || 'Litigante';
    if (store.active) {
      store.active.name = name;
      store.active.gender = this.gender;
      store.persistProfiles();
    } else {
      const p = createProfile(name, 'estudiante', this.gender);
      store.addProfile(p);
    }
    this.scene.start('CaseSelect');
  }
}
