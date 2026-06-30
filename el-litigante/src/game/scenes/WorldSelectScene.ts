import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { isWorldUnlocked, entryStep, worldLevels } from '../systems/progression';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

export class WorldSelectScene extends Phaser.Scene {
  constructor() {
    super('WorldSelect');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    title(this, cx, 56, 'Mapa del Litigio', 40);
    const profile = store.active!;
    label(this, cx, 96, 'Toca un mundo para JUGAR · toca 📖 para LEER la lección sin jugar.', 16, true);

    const t = theme();
    const cols = 5;
    const cardW = 220;
    const cardH = 108;
    const gapX = 18;
    const gapY = 16;
    const totalW = cols * cardW + (cols - 1) * gapX;
    const startX = (GAME_WIDTH - totalW) / 2 + cardW / 2;
    const startY = 160;

    store.content.worlds.forEach((world, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const x = startX + col * (cardW + gapX);
      const y = startY + row * (cardH + gapY);
      const unlocked = isWorldUnlocked(store.content.worlds, world, profile);
      const completed = profile.worldsCompleted.includes(world.id);

      const fill = unlocked ? Phaser.Display.Color.HexStringToColor(world.palette.sky).color : 0x2a2f3a;
      const card = this.add.rectangle(x, y, cardW, cardH, fill, 1).setStrokeStyle(3, completed ? t.accent : 0x000000, completed ? 1 : 0.2);

      this.add
        .text(x, y - 34, `Mundo ${world.order}`, { fontFamily: 'Segoe UI', fontSize: fs(13), color: '#0b1d33' })
        .setOrigin(0.5);
      this.add
        .text(x, y - 8, world.title, {
          fontFamily: 'Segoe UI',
          fontSize: fs(17),
          color: '#0b1d33',
          fontStyle: 'bold',
          align: 'center',
          wordWrap: { width: cardW - 16 },
        })
        .setOrigin(0.5);

      const levels = worldLevels(world);
      const done = levels.filter((l) => profile.levelsCompleted.includes(l.id)).length;
      const statusTxt = !unlocked
        ? '🔒 Bloqueado'
        : completed
          ? '★ Completado'
          : `${done}/${levels.length} niveles`;
      this.add
        .text(x, y + 30, statusTxt, { fontFamily: 'Segoe UI', fontSize: fs(13), color: unlocked ? '#13294b' : '#9fb3d1' })
        .setOrigin(0.5);

      if (unlocked) {
        card.setInteractive({ useHandCursor: true });
        card.on('pointerover', () => card.setScale(1.04));
        card.on('pointerout', () => card.setScale(1));
        card.on('pointerup', () => this.enterWorld(world.id));

        // Botón "leer lección" (no inicia el nivel).
        const read = this.add
          .text(x + cardW / 2 - 14, y - cardH / 2 + 12, '📖', { fontSize: fs(20) })
          .setOrigin(0.5)
          .setInteractive({ useHandCursor: true });
        read.on('pointerup', (_p: any, _lx: number, _ly: number, ev: any) => {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          this.openLesson(world.id);
        });
      }
    });

    makeButton(this, cx, GAME_HEIGHT - 44, 'Volver al menú', () => this.scene.start('Menu'), {
      width: 260,
      height: 52,
    });
  }

  private enterWorld(worldId: string) {
    const world = store.content.worlds.find((w) => w.id === worldId)!;
    const step = entryStep(world, store.active!);
    store.selectedWorld = worldId;
    this.scene.start('Level', { worldId, index: step.index, isBoss: step.isBoss });
  }

  private openLesson(worldId: string) {
    const world = store.content.worlds.find((w) => w.id === worldId)!;
    this.scene.start('Lesson', {
      lessonId: world.lessonId,
      palette: world.palette,
      unlocked: [],
      next: { action: 'worldselect' },
      readOnly: true,
    });
  }
}
