import Phaser from 'phaser';
import { TILE, BASE_MOVE_SPEED, RUN_MULTIPLIER, JUMP_VELOCITY, GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
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
    this.physics.add.overlap(this.player, this.hazards, () => this.takeDamage(this.diff.hazardDamage));
    if (this.flag) this.physics.add.overlap(this.player, this.flag, () => this.completeLevel());

    // Entrada.
    this.cursors = this.input.keyboard!.createCursorKeys();
    this.keyA = this.input.keyboard!.addKey('A');
    this.keyD = this.input.keyboard!.addKey('D');
    this.keySpace = this.input.keyboard!.addKey('SPACE');
    this.keyShift = this.input.keyboard!.addKey('SHIFT');
    this.input.keyboard!.addKey('ESC').on('down', () => this.togglePause());

    // HUD.
    this.scene.launch('Hud');
    bus.on('ui:pause', this.togglePause, this);
    bus.on('hud:request', this.emitHud, this);
    this.emitHud();

    this.events.once('shutdown', () => {
      bus.off('ui:pause', this.togglePause, this);
      bus.off('hud:request', this.emitHud, this);
      this.scene.stop('Hud');
    });
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
    return pb.velocity.y > 0 && pb.bottom <= tb.top + 16;
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
      this.floatingText(enemy.x, enemy.y - 20, `¡${def.name} superado! +${lexGain} LEX`);
      this.emitHud();
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
    this.floatingText(this.player.x, this.player.y - 30, '📄 Expediente +' + DOC_LEX + ' LEX');
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
    // Empujón hacia atrás.
    this.player.setVelocity(this.player.flipX ? 200 : -200, -260);
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
    if (this.finished || this.paused || !this.player.body) return;
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
    if (onGround) this.jumpsLeft = 1;

    const jumpPressed = jumpDown && !this.prevJump;
    this.prevJump = jumpDown;
    if (jumpPressed) {
      const jv = JUMP_VELOCITY - skillEffect(store.active!, store.content, 'jumpPower');
      if (onGround) {
        this.player.setVelocityY(jv);
      } else if (this.jumpsLeft > 0) {
        this.player.setVelocityY(jv * 0.92);
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
