import Phaser from 'phaser';
import { TILE, BASE_MOVE_SPEED, RUN_MULTIPLIER, JUMP_VELOCITY, COYOTE_MS, GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { grantXp, skillEffect } from '../../core/rpg';
import { evaluateAchievements } from '../../core/achievements';
import { TEX } from '../systems/assets';
import { controls, resetControls } from '../systems/controls';
import { bus } from '../systems/bus';
import { buildParsedLevel, worldLevels } from '../systems/progression';
import type { World, EnemyDef, Difficulty } from '../../core/types';

interface LevelInit {
  worldId: string;
  index: number;
  isBoss: boolean;
}

const ENEMY_LEX = 5;
const ENEMY_XP = 12;
const COIN_LEX = 1;
const DOC_LEX = 3;
const LEVEL_XP = 60;
const BOSS_XP = 200;

export class LevelScene extends Phaser.Scene {
  private world!: World;
  private diff!: Difficulty;
  private isBoss = false;
  private levelIndex = 0;

  private player!: Phaser.Physics.Arcade.Sprite;
  private solids!: Phaser.Physics.Arcade.StaticGroup;
  private enemies!: Phaser.Physics.Arcade.Group;
  private coins!: Phaser.Physics.Arcade.Group;
  private docs!: Phaser.Physics.Arcade.Group;
  private hazards!: Phaser.Physics.Arcade.StaticGroup;
  private flag?: Phaser.Physics.Arcade.Sprite;
  private boss?: Phaser.Physics.Arcade.Sprite;

  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private keyA!: Phaser.Input.Keyboard.Key;
  private keyD!: Phaser.Input.Keyboard.Key;
  private keySpace!: Phaser.Input.Keyboard.Key;
  private keyShift!: Phaser.Input.Keyboard.Key;

  private lives = 3;
  private shields = 0;
  private jumpsLeft = 1;
  private prevJump = false;
  private invulnUntil = 0;
  private tookDamage = false;
  private finished = false;
  private startPos = { x: 0, y: 0 };
  private worldPixelH = 0;
  private bossHp = 0;
  private bossMaxHp = 0;
  private paused = false;
  private intro = false;
  private lastOnGround = 0;
  private taughtEnemies = new Set<string>();
  private docIdx = 0;
  private hazIdx = 0;

  constructor() {
    super('Level');
  }

  init(data: LevelInit) {
    this.world = store.content.worlds.find((w) => w.id === data.worldId)!;
    this.isBoss = data.isBoss;
    this.levelIndex = data.index;
    this.diff = store.content.difficulties.find((d) => d.id === store.active!.difficulty) || store.content.difficulties[0];
    this.finished = false;
    this.tookDamage = false;
    this.paused = false;
    this.intro = false;
    this.taughtEnemies = new Set();
    this.docIdx = 0;
    this.hazIdx = 0;
  }

  create() {
    resetControls();
    const p = this.world.palette;
    this.solids = this.physics.add.staticGroup();
    this.hazards = this.physics.add.staticGroup();
    this.enemies = this.physics.add.group();
    this.coins = this.physics.add.group({ allowGravity: false, immovable: true });
    this.docs = this.physics.add.group({ allowGravity: false, immovable: true });

    const cols = this.isBoss ? 26 : 0;
    if (this.isBoss) this.buildBossArena(cols);
    else this.buildFromLayout();

    // Vidas y escudo inicial (habilidad Concentración).
    this.lives = this.diff.lives;
    this.shields = skillEffect(store.active!, store.content, 'startShield');

    // Cámara y fondo.
    this.cameras.main.setBackgroundColor(p.sky);
    this.paintSky();

    // Colisiones.
    this.physics.add.collider(this.player, this.solids);
    this.physics.add.collider(this.enemies, this.solids);
    if (this.boss) this.physics.add.collider(this.boss, this.solids);
    this.physics.add.overlap(this.player, this.enemies, (pl, en) => this.onEnemy(en as Phaser.Physics.Arcade.Sprite));
    if (this.boss) this.physics.add.overlap(this.player, this.boss, () => this.onBoss());
    this.physics.add.overlap(this.player, this.coins, (_pl, c) => this.collectCoin(c as Phaser.Physics.Arcade.Sprite));
    this.physics.add.overlap(this.player, this.docs, (_pl, d) => this.collectDoc(d as Phaser.Physics.Arcade.Sprite));
    this.physics.add.overlap(this.player, this.hazards, () => this.onHazard());
    if (this.flag) this.physics.add.overlap(this.player, this.flag, () => this.completeLevel());

    // Entrada.
    this.cursors = this.input.keyboard!.createCursorKeys();
    this.keyA = this.input.keyboard!.addKey('A');
    this.keyD = this.input.keyboard!.addKey('D');
    this.keySpace = this.input.keyboard!.addKey('SPACE');
    this.keyShift = this.input.keyboard!.addKey('SHIFT');
    this.input.keyboard!.addKey('ESC').on('down', () => this.togglePause());

    // HUD.
    // Periodo de gracia inicial (sin daño) para orientarse.
    this.invulnUntil = 1600;

    this.scene.launch('Hud');
    bus.on('ui:pause', this.togglePause, this);
    bus.on('hud:request', this.emitHud, this);
    bus.on('ui:exitmap', this.exitToMap, this);
    this.emitHud();

    this.events.once('shutdown', () => {
      bus.off('ui:pause', this.togglePause, this);
      bus.off('hud:request', this.emitHud, this);
      bus.off('ui:exitmap', this.exitToMap, this);
      this.scene.stop('Hud');
    });

    // Tarjeta educativa antes de jugar: enseña aunque aún no ganes.
    this.showIntro();
  }

  // ---- Construcción del mundo ----

  private buildFromLayout() {
    const parsed = buildParsedLevel(this.world, this.levelIndex);
    this.worldPixelH = parsed.rows * TILE;
    const worldW = parsed.cols * TILE;
    this.physics.world.setBounds(0, 0, worldW, this.worldPixelH + 200);
    this.cameras.main.setBounds(0, 0, worldW, this.worldPixelH);

    parsed.ground.forEach((c) => this.addSolid(c.col, c.row, TEX.ground, TILE));
    parsed.platforms.forEach((c) => this.addSolid(c.col, c.row, TEX.platform, TILE / 2, true));
    parsed.hazards.forEach((c) => {
      const s = this.hazards.create(c.col * TILE + TILE / 2, c.row * TILE + (TILE * 3) / 4, TEX.hazard) as Phaser.Physics.Arcade.Sprite;
      s.refreshBody();
    });
    parsed.coins.forEach((c) => this.coins.create(c.col * TILE + TILE / 2, c.row * TILE + TILE / 2, TEX.lex));
    parsed.docs.forEach((c) => this.docs.create(c.col * TILE + TILE / 2, c.row * TILE + TILE / 2, TEX.doc));
    parsed.enemies.forEach((c, i) => this.spawnEnemy(c.col * TILE + TILE / 2, c.row * TILE, i));

    this.startPos = { x: parsed.player.col * TILE + TILE / 2, y: parsed.player.row * TILE };
    this.spawnPlayer();

    const fx = parsed.flag.col * TILE + TILE / 2;
    const fy = (parsed.rows - 3) * TILE - 40;
    this.flag = this.physics.add.staticSprite(fx, fy, TEX.flag);
  }

  private buildBossArena(cols: number) {
    const rows = 11;
    this.worldPixelH = rows * TILE;
    const worldW = cols * TILE;
    this.physics.world.setBounds(0, 0, worldW, this.worldPixelH + 200);
    this.cameras.main.setBounds(0, 0, worldW, this.worldPixelH);

    for (let c = 0; c < cols; c++) {
      for (let r = rows - 2; r < rows; r++) this.addSolid(c, r, TEX.ground, TILE);
    }
    // Un par de plataformas para esquivar.
    [6, 12, 18].forEach((c) => {
      this.addSolid(c, rows - 5, TEX.platform, TILE / 2, true);
      this.addSolid(c + 1, rows - 5, TEX.platform, TILE / 2, true);
    });

    this.startPos = { x: 2 * TILE, y: (rows - 3) * TILE };
    this.spawnPlayer();

    this.bossMaxHp = this.world.boss.hp;
    this.bossHp = this.bossMaxHp;
    this.boss = this.physics.add.sprite((cols - 6) * TILE, (rows - 4) * TILE, TEX.boss);
    this.boss.setCollideWorldBounds(true);
    this.boss.setBounce(1, 0);
    this.boss.setVelocityX(-120 * this.diff.enemySpeedMul);
    this.boss.setData('invuln', 0);
  }

  private addSolid(col: number, row: number, tex: string, h: number, isPlatform = false) {
    const y = isPlatform ? row * TILE + h / 2 : row * TILE + TILE / 2;
    const s = this.solids.create(col * TILE + TILE / 2, y, tex) as Phaser.Physics.Arcade.Sprite;
    s.refreshBody();
  }

  private spawnPlayer() {
    this.player = this.physics.add.sprite(this.startPos.x, this.startPos.y, TEX.player);
    this.player.setCollideWorldBounds(false);
    this.player.setMaxVelocity(600, 1100);
    this.cameras.main.startFollow(this.player, true, 0.12, 0.12);
  }

  private spawnEnemy(x: number, y: number, idx: number) {
    const defs = store.content.enemies;
    const def: EnemyDef = defs[idx % defs.length];
    const e = this.enemies.create(x, y, TEX.enemy) as Phaser.Physics.Arcade.Sprite;
    e.setTint(Phaser.Display.Color.HexStringToColor(def.color).color);
    e.setCollideWorldBounds(false);
    e.setData('def', def);
    e.setData('dir', Math.random() < 0.5 ? -1 : 1);
    e.setData('minX', x - TILE * 2.5);
    e.setData('maxX', x + TILE * 2.5);
    e.setData('jumpAt', 0);
    const speed = def.speed * this.diff.enemySpeedMul;
    e.setVelocityX(speed * e.getData('dir'));
  }

  // ---- Fondo ----
  private paintSky() {
    const cam = this.cameras.main;
    const w = cam.width;
    const h = cam.height;
    const p = this.world.palette;
    const g = this.add.graphics().setScrollFactor(0).setDepth(-100);
    const top = Phaser.Display.Color.HexStringToColor(p.sky).color;
    const bottom = Phaser.Display.Color.HexStringToColor(p.skyBottom).color;
    g.fillGradientStyle(top, top, bottom, bottom, 1);
    g.fillRect(0, 0, w, h);
    // Nubes con parallax.
    for (let i = 0; i < 5; i++) {
      const c = this.add.image(120 + i * 260, 80 + (i % 2) * 60, TEX.cloud).setScrollFactor(0.3).setDepth(-90).setAlpha(0.85);
      this.tweens.add({ targets: c, x: c.x + 60, duration: 6000 + i * 800, yoyo: true, repeat: -1, ease: 'Sine.inOut' });
    }
  }

  // ---- Colisiones / eventos ----

  private isStomp(target: Phaser.Physics.Arcade.Sprite): boolean {
    const pb = this.player.body as Phaser.Physics.Arcade.Body;
    const tb = target.body as Phaser.Physics.Arcade.Body;
    return pb.velocity.y > -40 && pb.bottom <= tb.top + 24;
  }

  private onEnemy(enemy: Phaser.Physics.Arcade.Sprite) {
    if (!enemy.active) return;
    if (this.isStomp(enemy)) {
      const def = enemy.getData('def') as EnemyDef;
      this.burst(enemy.x, enemy.y, 0xffffff);
      enemy.destroy();
      this.player.setVelocityY(-340);
      const lexGain = ENEMY_LEX + skillEffect(store.active!, store.content, 'lexBonus');
      store.active!.lex += lexGain;
      store.active!.stats.enemies += 1;
      grantXp(store.active!, ENEMY_XP * this.diff.xpMul);
      this.floatingText(enemy.x, enemy.y - 20, `+${lexGain} LEX`);
      this.emitHud();
      // Enseñanza COGEP: la primera vez que vences cada tipo de error.
      if (def.dato && !this.taughtEnemies.has(def.id) && !this.intro) {
        this.taughtEnemies.add(def.id);
        this.showDato('⚖️ Error vencido: ' + def.name, (def.concepto ? def.concepto + '\n\n' : '') + '💡 ' + def.dato, def.articulo || '');
      } else if (def.dato) {
        this.showBanner('⚖️ ' + def.name, def.dato, def.articulo || '');
      }
    } else {
      this.takeDamage(1);
    }
  }

  private onBoss() {
    if (!this.boss || this.finished) return;
    if (this.time.now < (this.boss.getData('invuln') as number)) return;
    if (this.isStomp(this.boss)) {
      this.bossHp -= 1 + skillEffect(store.active!, store.content, 'stompPower');
      this.player.setVelocityY(-380);
      this.boss.setData('invuln', this.time.now + 800);
      this.boss.setTintFill(0xffffff);
      this.time.delayedCall(120, () => this.boss?.clearTint());
      this.cameras.main.shake(120, 0.008);
      // Acelera al recibir daño.
      const dir = this.boss.body!.velocity.x >= 0 ? 1 : -1;
      this.boss.setVelocityX((140 + (this.bossMaxHp - this.bossHp) * 30) * this.diff.enemySpeedMul * dir);
      if (this.bossHp <= 0) {
        this.burst(this.boss.x, this.boss.y, 0xf5d547);
        this.boss.destroy();
        this.boss = undefined;
        this.defeatBoss();
      } else {
        this.emitHud();
      }
    } else {
      this.takeDamage(this.diff.hazardDamage);
    }
  }

  private collectCoin(coin: Phaser.Physics.Arcade.Sprite) {
    coin.destroy();
    store.active!.lex += COIN_LEX;
    this.burst(this.player.x, this.player.y, 0xf5d547);
    this.emitHud();
  }

  private collectDoc(doc: Phaser.Physics.Arcade.Sprite) {
    doc.destroy();
    store.active!.lex += DOC_LEX;
    store.active!.stats.documents += 1;
    // Cada expediente enseña un medio de prueba del COGEP.
    const pruebas = store.content.datos.pruebas;
    const d = pruebas[this.docIdx % pruebas.length];
    this.docIdx += 1;
    this.showBanner('📄 ' + d.titulo, d.texto, d.articulo);
    this.floatingText(this.player.x, this.player.y - 30, '+' + DOC_LEX + ' LEX');
    this.emitHud();
  }

  private takeDamage(amount: number) {
    if (this.finished || this.time.now < this.invulnUntil) return;
    this.invulnUntil = this.time.now + 1200;
    this.tookDamage = true;
    if (this.shields > 0) {
      this.shields -= 1;
      this.flashPlayer(0x3a8fd6);
      this.emitHud();
      return;
    }
    this.lives -= amount;
    this.flashPlayer(0xff4d4d);
    this.cameras.main.shake(150, 0.01);
    // Empujón hacia atrás (suave).
    this.player.setVelocity(this.player.flipX ? 140 : -140, -200);
    this.emitHud();
    if (this.lives <= 0) this.gameOver();
  }

  private flashPlayer(color: number) {
    this.player.setTintFill(color);
    this.time.delayedCall(140, () => this.player.clearTint());
    this.tweens.add({ targets: this.player, alpha: 0.4, duration: 120, yoyo: true, repeat: 4 });
  }

  // ---- Final ----

  private markLessonRead(lessonId: string) {
    if (!store.active!.lessonsRead.includes(lessonId)) store.active!.lessonsRead.push(lessonId);
  }

  private completeLevel() {
    if (this.finished) return;
    this.finished = true;
    const levels = worldLevels(this.world);
    const meta = levels[this.levelIndex];
    if (!store.active!.levelsCompleted.includes(meta.id)) store.active!.levelsCompleted.push(meta.id);
    if (!this.tookDamage) store.active!.stats.perfectLevels += 1;
    grantXp(store.active!, LEVEL_XP * this.diff.xpMul);
    this.markLessonRead(meta.lessonId);

    const next =
      this.levelIndex < levels.length - 1
        ? { action: 'level', worldId: this.world.id, index: this.levelIndex + 1, isBoss: false }
        : { action: 'level', worldId: this.world.id, index: levels.length, isBoss: true };

    this.finishSequence(meta.lessonId, next);
  }

  private defeatBoss() {
    if (this.finished) return;
    this.finished = true;
    const a = store.active!;
    if (!a.bossesDefeated.includes(this.world.boss.id)) a.bossesDefeated.push(this.world.boss.id);
    if (!a.worldsCompleted.includes(this.world.id)) a.worldsCompleted.push(this.world.id);
    if (!a.difficultyWorldsDone.includes(a.difficulty)) a.difficultyWorldsDone.push(a.difficulty);
    if (!this.tookDamage) a.stats.bossPerfect += 1;
    grantXp(a, BOSS_XP * this.diff.xpMul);
    this.markLessonRead(this.world.boss.lessonId);
    this.finishSequence(this.world.boss.lessonId, { action: 'worldselect' });
  }

  private finishSequence(lessonId: string, next: object) {
    const unlocked = evaluateAchievements(store.active!, store.content);
    store.persistProfiles();
    this.scene.stop('Hud');
    this.scene.start('Lesson', {
      lessonId,
      palette: this.world.palette,
      unlocked: unlocked.map((u) => u.name),
      next,
    });
  }

  private gameOver() {
    this.finished = true;
    this.physics.pause();
    store.persistProfiles();
    const overlay = this.add.container(0, 0).setScrollFactor(0).setDepth(9000);
    const { width, height } = this.scale;
    overlay.add(this.add.rectangle(width / 2, height / 2, width, height, 0x000000, 0.7));
    overlay.add(
      this.add
        .text(width / 2, height / 2 - 80, 'Litigio perdido', {
          fontFamily: 'Georgia, serif',
          fontSize: '48px',
          color: '#ff6b6b',
          fontStyle: 'bold',
        })
        .setOrigin(0.5)
    );
    const retry = this.add
      .text(width / 2, height / 2, '↻ Reintentar', { fontSize: '30px', color: '#f5d547', fontStyle: 'bold' })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });
    retry.on('pointerup', () => this.scene.restart({ worldId: this.world.id, index: this.levelIndex, isBoss: this.isBoss }));
    const menu = this.add
      .text(width / 2, height / 2 + 60, 'Volver al mapa', { fontSize: '24px', color: '#eaf2ff' })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });
    menu.on('pointerup', () => this.scene.start('WorldSelect'));
    overlay.add([retry, menu]);
  }

  private exitToMap() {
    if (this.finished) return;
    this.scene.stop('Hud');
    this.scene.start('WorldSelect');
  }

  // ---- Intro educativa ----
  private showIntro() {
    const lessonId = this.isBoss ? this.world.boss.lessonId : worldLevels(this.world)[this.levelIndex]?.lessonId;
    const lesson = store.content.lessons[lessonId] || store.content.lessons['principios'];
    this.markLessonRead(lessonId);
    evaluateAchievements(store.active!, store.content);
    store.persistProfiles();

    this.intro = true;
    this.physics.pause();
    const { width, height } = this.scale;
    const layer = this.add.container(0, 0).setScrollFactor(0).setDepth(9500).setName('introLayer');
    layer.add(this.add.rectangle(width / 2, height / 2, width, height, 0x0b1d33, 0.92));
    layer.add(this.add.rectangle(width / 2, height / 2, 880, 440, 0x13294b, 1).setStrokeStyle(3, 0xf5d547));
    layer.add(this.add.text(width / 2, height / 2 - 180, this.isBoss ? `JEFE: ${this.world.boss.name}` : `${this.world.title}`, { fontFamily: 'Georgia, serif', fontSize: '30px', color: '#f5d547', fontStyle: 'bold', align: 'center' }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 - 130, lesson.titulo, { fontFamily: 'Segoe UI', fontSize: '24px', color: '#ffffff', fontStyle: 'bold', align: 'center', wordWrap: { width: 800 } }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 - 60, lesson.explicacion, { fontFamily: 'Segoe UI', fontSize: '18px', color: '#eaf2ff', align: 'center', wordWrap: { width: 780 }, lineSpacing: 4 }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 + 50, '📜 ' + lesson.articulo, { fontFamily: 'Segoe UI', fontSize: '16px', color: '#f5d547', align: 'center', wordWrap: { width: 780 } }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 + 95, '🎯 Llega a la 🚩 meta. Salta sobre los errores (👾) para vencerlos.', { fontFamily: 'Segoe UI', fontSize: '15px', color: '#9fb3d1', align: 'center', wordWrap: { width: 780 } }).setOrigin(0.5));

    const btn = this.add.text(width / 2, height / 2 + 165, '▶  ¡JUGAR!', { fontFamily: 'Segoe UI', fontSize: '28px', color: '#0b1d33', fontStyle: 'bold', backgroundColor: '#f5d547', padding: { x: 32, y: 12 } }).setOrigin(0.5).setInteractive({ useHandCursor: true });
    layer.add(btn);
    layer.add(this.add.text(width / 2, height / 2 + 205, '(toca la pantalla o pulsa una tecla para empezar)', { fontFamily: 'Segoe UI', fontSize: '13px', color: '#9fb3d1' }).setOrigin(0.5).setScrollFactor(0));

    const start = () => {
      if (!this.intro) return;
      layer.destroy();
      this.intro = false;
      this.physics.resume();
    };
    // Empezar tocando en cualquier parte, con el botón, o con una tecla.
    this.input.once('pointerup', start);
    this.input.keyboard!.once('keydown', start);
    btn.on('pointerup', start);
  }

  private onHazard() {
    if (this.finished || this.time.now < this.invulnUntil) return;
    const pel = store.content.datos.peligros;
    const p = pel[this.hazIdx % pel.length];
    this.hazIdx += 1;
    this.showBanner('⚠️ ' + p.titulo, p.texto, p.articulo);
    this.takeDamage(this.diff.hazardDamage);
  }

  // Tarjeta educativa que pausa el juego (se cierra al tocar o pulsar).
  private showDato(title: string, body: string, articulo: string) {
    this.intro = true;
    this.physics.pause();
    const { width, height } = this.scale;
    const layer = this.add.container(0, 0).setScrollFactor(0).setDepth(9400).setName('datoLayer');
    const shade = this.add.rectangle(width / 2, height / 2, width, height, 0x0b1d33, 0.9).setInteractive();
    layer.add(shade);
    layer.add(this.add.rectangle(width / 2, height / 2, 820, 400, 0x13294b, 1).setStrokeStyle(3, 0xf5d547));
    layer.add(this.add.text(width / 2, height / 2 - 150, '📚 ¿Sabías que…?', { fontFamily: 'Segoe UI', fontSize: '18px', color: '#9fb3d1' }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 - 112, title, { fontFamily: 'Georgia, serif', fontSize: '26px', color: '#f5d547', fontStyle: 'bold', align: 'center', wordWrap: { width: 760 } }).setOrigin(0.5));
    layer.add(this.add.text(width / 2, height / 2 - 20, body, { fontFamily: 'Segoe UI', fontSize: '18px', color: '#eaf2ff', align: 'center', wordWrap: { width: 740 }, lineSpacing: 5 }).setOrigin(0.5));
    if (articulo) layer.add(this.add.text(width / 2, height / 2 + 95, '📜 ' + articulo, { fontFamily: 'Segoe UI', fontSize: '16px', color: '#f5d547', align: 'center', wordWrap: { width: 740 } }).setOrigin(0.5));
    const btn = this.add.text(width / 2, height / 2 + 150, '▶  Entendido', { fontFamily: 'Segoe UI', fontSize: '24px', color: '#0b1d33', fontStyle: 'bold', backgroundColor: '#f5d547', padding: { x: 28, y: 10 } }).setOrigin(0.5).setInteractive({ useHandCursor: true });
    layer.add(btn);

    const guard = this.time.now + 300;
    const close = () => {
      if (!this.intro || this.time.now < guard) return;
      layer.destroy();
      this.intro = false;
      this.physics.resume();
    };
    shade.on('pointerup', close);
    btn.on('pointerup', close);
    this.input.keyboard!.once('keydown-SPACE', close);
    this.input.keyboard!.once('keydown-ENTER', close);
  }

  // Banner no bloqueante en la parte superior (dura ~3.5 s).
  private showBanner(title: string, body: string, articulo: string) {
    const w = this.scale.width;
    const c = this.add.container(w / 2, 116).setScrollFactor(0).setDepth(8000);
    c.add(this.add.rectangle(0, 0, 780, 74, 0x0b1d33, 0.9).setStrokeStyle(2, 0xf5d547));
    c.add(this.add.text(0, -20, title, { fontFamily: 'Segoe UI', fontSize: '17px', color: '#f5d547', fontStyle: 'bold', align: 'center', wordWrap: { width: 740 } }).setOrigin(0.5));
    c.add(this.add.text(0, 12, body + (articulo ? '  ·  ' + articulo : ''), { fontFamily: 'Segoe UI', fontSize: '13px', color: '#eaf2ff', align: 'center', wordWrap: { width: 740 } }).setOrigin(0.5));
    c.setAlpha(0);
    this.tweens.add({ targets: c, alpha: 1, duration: 200 });
    this.time.delayedCall(3400, () => this.tweens.add({ targets: c, alpha: 0, duration: 300, onComplete: () => c.destroy() }));
  }

  // ---- Pausa ----
  private togglePause() {
    if (this.finished) return;
    this.paused = !this.paused;
    if (this.paused) {
      this.physics.pause();
      const { width, height } = this.scale;
      const layer = this.add.container(0, 0).setScrollFactor(0).setDepth(9000).setName('pauseLayer');
      layer.add(this.add.rectangle(width / 2, height / 2, width, height, 0x000000, 0.6));
      layer.add(
        this.add.text(width / 2, height / 2 - 80, 'Pausa', { fontSize: '44px', color: '#f5d547', fontStyle: 'bold' }).setOrigin(0.5)
      );
      const resume = this.add.text(width / 2, height / 2, '▶ Reanudar', { fontSize: '28px', color: '#eaf2ff' }).setOrigin(0.5).setInteractive({ useHandCursor: true });
      resume.on('pointerup', () => this.togglePause());
      const map = this.add.text(width / 2, height / 2 + 56, 'Salir al mapa', { fontSize: '22px', color: '#9fb3d1' }).setOrigin(0.5).setInteractive({ useHandCursor: true });
      map.on('pointerup', () => this.scene.start('WorldSelect'));
      layer.add([resume, map]);
    } else {
      this.physics.resume();
      this.children.getByName('pauseLayer')?.destroy();
    }
  }

  // ---- Efectos ----
  private burst(x: number, y: number, color: number) {
    const em = this.add.particles(x, y, TEX.particle, {
      speed: { min: 60, max: 180 },
      lifespan: 400,
      quantity: 10,
      scale: { start: 1, end: 0 },
      tint: color,
    });
    this.time.delayedCall(420, () => em.destroy());
  }

  private floatingText(x: number, y: number, text: string) {
    const t = this.add.text(x, y, text, { fontFamily: 'Segoe UI', fontSize: '18px', color: '#ffffff', fontStyle: 'bold', stroke: '#0b1d33', strokeThickness: 4 }).setOrigin(0.5);
    this.tweens.add({ targets: t, y: y - 40, alpha: 0, duration: 900, onComplete: () => t.destroy() });
  }

  private emitHud() {
    bus.emit('hud:update', {
      lives: Math.max(0, this.lives),
      maxLives: this.diff.lives,
      shields: this.shields,
      lex: store.active!.lex,
      charLevel: store.active!.charLevel,
      worldTitle: this.world.title,
      levelTitle: this.isBoss ? `Jefe: ${this.world.boss.name}` : worldLevels(this.world)[this.levelIndex]?.title || '',
      bossHp: this.boss ? this.bossHp : undefined,
      bossMaxHp: this.boss ? this.bossMaxHp : undefined,
      bossName: this.boss ? this.world.boss.name : undefined,
    });
  }

  // ---- Bucle ----
  update() {
    if (this.finished || this.paused || this.intro || !this.player.body) return;
    const body = this.player.body as Phaser.Physics.Arcade.Body;

    // Entrada combinada: teclado + táctil + gamepad.
    const pad = this.input.gamepad?.getPad(0);
    const padLeft = pad ? pad.leftStick.x < -0.3 || pad.left : false;
    const padRight = pad ? pad.leftStick.x > 0.3 || pad.right : false;
    const padJump = pad ? pad.A || pad.R2 > 0.3 : false;

    const left = this.cursors.left.isDown || this.keyA.isDown || controls.left || padLeft;
    const right = this.cursors.right.isDown || this.keyD.isDown || controls.right || padRight;
    const running = this.keyShift.isDown || controls.run || (pad ? pad.X : false);
    const jumpDown = this.cursors.up.isDown || this.keySpace.isDown || controls.jump || padJump;

    const speed = (BASE_MOVE_SPEED + skillEffect(store.active!, store.content, 'moveSpeed')) * (running ? RUN_MULTIPLIER : 1);

    if (left && !right) {
      this.player.setVelocityX(-speed);
      this.player.setFlipX(true);
    } else if (right && !left) {
      this.player.setVelocityX(speed);
      this.player.setFlipX(false);
    } else {
      this.player.setVelocityX(0);
    }

    const onGround = body.blocked.down || body.touching.down;
    if (onGround) {
      this.jumpsLeft = 1;
      this.lastOnGround = this.time.now;
    }
    const canGroundJump = onGround || this.time.now - this.lastOnGround <= COYOTE_MS;

    const jumpPressed = jumpDown && !this.prevJump;
    this.prevJump = jumpDown;
    if (jumpPressed) {
      const jv = JUMP_VELOCITY - skillEffect(store.active!, store.content, 'jumpPower');
      if (canGroundJump) {
        this.player.setVelocityY(jv);
        this.lastOnGround = 0;
        this.jumpsLeft = 1; // permite además un salto en el aire
      } else if (this.jumpsLeft > 0) {
        this.player.setVelocityY(jv * 0.95);
        this.jumpsLeft = 0;
        this.burst(this.player.x, this.player.y + 20, 0xbfe3ff);
      }
    }

    // Caída al vacío.
    if (this.player.y > this.worldPixelH + 120) {
      this.player.setVelocity(0, 0);
      this.player.setPosition(this.startPos.x, this.startPos.y - TILE);
      this.takeDamage(1);
    }

    this.updateEnemies();
    this.updateBoss();
  }

  private updateEnemies() {
    this.enemies.getChildren().forEach((obj) => {
      const e = obj as Phaser.Physics.Arcade.Sprite;
      if (!e.active || !e.body) return;
      const def = e.getData('def') as EnemyDef;
      const body = e.body as Phaser.Physics.Arcade.Body;
      const speed = def.speed * this.diff.enemySpeedMul;

      if (def.behavior === 'chaser') {
        const dir = this.player.x < e.x ? -1 : 1;
        if (Math.abs(this.player.x - e.x) < TILE * 7) e.setVelocityX(speed * dir);
        else e.setVelocityX(0);
      } else {
        let dir = e.getData('dir') as number;
        if (body.blocked.left || e.x <= (e.getData('minX') as number)) dir = 1;
        else if (body.blocked.right || e.x >= (e.getData('maxX') as number)) dir = -1;
        e.setData('dir', dir);
        e.setVelocityX(speed * dir);
        if (def.behavior === 'jumper' && body.blocked.down && this.time.now > (e.getData('jumpAt') as number)) {
          e.setVelocityY(-420);
          e.setData('jumpAt', this.time.now + 1500);
        }
      }
      e.setFlipX(body.velocity.x > 0);
    });
  }

  private updateBoss() {
    if (!this.boss || !this.boss.body) return;
    const body = this.boss.body as Phaser.Physics.Arcade.Body;
    if (body.blocked.down && Math.random() < 0.01) this.boss.setVelocityY(-360);
  }
}
