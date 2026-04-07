import pygame
import random
import math
import sys
import os

from settings import *
from sprites import make_surface_player, make_surface_enemy
from entities import Player, Enemy, Projectile, PowerUp, Particle

class Game:
    ENEMY_SPAWN_BASE = 90   # frames entre grupos de spawn
    POWERUP_SPAWN    = 600  # frames entre power-ups

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 20)
        self.font_sm  = pygame.font.SysFont("consolas", 15)

        # ── Carregar todos os sprites ──────────────────────────────────
        self.player_sprite = make_surface_player(Player.BASE_SIZE, Player.BASE_SIZE)

        self.enemy_sprites = {
            "bat": make_surface_enemy(Enemy.BASE_SIZE, Enemy.BASE_SIZE, "bat"),
            "eye": make_surface_enemy(Enemy.BASE_SIZE, Enemy.BASE_SIZE, "eye")
        }

        # ── Fundo ──────────────────────────────────────────────────────
        self._build_background()
        self.reset()

    def _build_background(self):
        """Carrega cenario.png ou gera fundo procedural sombrio como fallback."""
        for ext in ["png", "jpg", "jpeg"]:
            if os.path.exists(f"cenario.{ext}"):
                try:
                    img = pygame.image.load(f"cenario.{ext}").convert()
                    self.bg = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
                    return
                except:
                    pass

        # Fundo procedural (usado quando cenario.png nao existe)
        self.bg = pygame.Surface((SCREEN_W, SCREEN_H))
        self.bg.fill((22, 24, 28))
        for _ in range(35):
            pygame.draw.ellipse(self.bg,
                random.choice([(18,20,24),(26,28,32),(30,28,30),(20,25,25)]),
                (random.randint(-50, SCREEN_W), random.randint(-50, SCREEN_H),
                 random.randint(60, 200),       random.randint(30, 100)))
        for _ in range(25):
            x = random.randint(10, SCREEN_W-30)
            y = random.randint(10, SCREEN_H-30)
            if math.hypot(x - SCREEN_W//2, y - SCREEN_H//2) < 100:
                continue
            obj = random.choice(["tree","grave","rock","rock","bush"])
            if obj == "tree":
                pygame.draw.rect(self.bg,   (35,25,20), (x, y, 12, 25))
                pygame.draw.circle(self.bg, (25,35,25), (x+6, y-5),  22)
                pygame.draw.circle(self.bg, (20,30,20), (x+6, y-15), 16)
            elif obj == "grave":
                pygame.draw.rect(self.bg, (60,65,70), (x, y, 20, 24),
                                 border_top_left_radius=10, border_top_right_radius=10)
                pygame.draw.line(self.bg, (40,45,50), (x+10,y+6), (x+10,y+14), 2)
                pygame.draw.line(self.bg, (40,45,50), (x+6, y+9), (x+14,y+9),  2)
            elif obj == "rock":
                pygame.draw.ellipse(self.bg, (45,45,50), (x, y, 24, 16))
                pygame.draw.ellipse(self.bg, (55,55,60), (x+4, y+2, 12, 8))
            elif obj == "bush":
                pygame.draw.circle(self.bg, (15,25,20), (x,   y),   12)
                pygame.draw.circle(self.bg, (10,20,15), (x-6, y+6), 10)

    def reset(self):
        self.player      = Player(self.player_sprite)
        self.enemies     = []
        self.projectiles = []
        self.particles   = []
        self.powerups    = []
        self.score       = 0
        self.frame       = 0
        self.elapsed_s   = 0
        self.spawn_timer = 0
        self.pu_timer    = 0
        self.state       = "playing"

    def spawn_enemy(self):
        difficulty = 1.0 + self.elapsed_s / 60.0
        self.enemies.append(
            Enemy(self.player.x, self.player.y, self.enemy_sprites, difficulty))

    # ── Loop principal ─────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            if self.state == "playing":
                self._update()
            self._draw()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if self.state == "gameover" and event.key == pygame.K_r:
                    self.reset()

    def _update(self):
        self.frame += 1
        if self.frame % FPS == 0:
            self.elapsed_s += 1

        difficulty = 1.0 + self.elapsed_s / 60.0

        # Spawn de inimigos (intervalo diminui com dificuldade)
        self.spawn_timer += 1
        interval = max(20, int(self.ENEMY_SPAWN_BASE / difficulty))
        if self.spawn_timer >= interval:
            for _ in range(1 + int(difficulty * 0.4)):
                self.spawn_enemy()
            self.spawn_timer = 0

        # Spawn de power-up
        self.pu_timer += 1
        if self.pu_timer >= self.POWERUP_SPAWN:
            self.powerups.append(PowerUp(
                random.randint(60, SCREEN_W-60),
                random.randint(60, SCREEN_H-60)))
            self.pu_timer = 0

        # Atualizar jogador
        self.player.update(self.enemies, self.projectiles)
        if not self.player.alive:
            self.state = "gameover"; return

        # Atualizar projeteis
        for p in self.projectiles: p.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Atualizar inimigos
        for e in self.enemies: e.update(self.player.x, self.player.y)

        # Colisao projetil x inimigo
        for proj in self.projectiles[:]:
            for e in self.enemies[:]:
                if math.hypot(e.x-proj.x, e.y-proj.y) < e.get_radius() + proj.radius:
                    for _ in range(random.randint(6, 12)):
                        self.particles.append(Particle(e.x, e.y, (220,60,80)))
                    e.alive    = False
                    proj.alive = False
                    self.score += 1
                    break

        self.enemies     = [e for e in self.enemies     if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Colisao power-up x jogador
        for pu in self.powerups[:]:
            pu.update()
            if math.hypot(pu.x-self.player.x, pu.y-self.player.y) < pu.radius + self.player.get_radius():
                self.player.apply_powerup()
                for _ in range(16):
                    self.particles.append(Particle(pu.x, pu.y, C_GOLD))
                pu.alive = False
        self.powerups = [pu for pu in self.powerups if pu.alive]

        # Atualizar particulas
        for pt in self.particles: pt.update()
        self.particles = [pt for pt in self.particles if pt.life > 0]

    def _draw(self):
        self.screen.blit(self.bg, (0, 0))

        if self.state == "playing":
            for pu in self.powerups:    pu.draw(self.screen)
            for pt in self.particles:   pt.draw(self.screen)
            for e  in self.enemies:     e.draw(self.screen)
            for p  in self.projectiles: p.draw(self.screen)
            self.player.draw(self.screen)
            self.player.draw_hud(self.screen, self.font_big, self.font_sm,
                                 self.score, self.elapsed_s)
            self.screen.blit(
                self.font_sm.render(f"Inimigos: {len(self.enemies)}", True, C_RED),
                (16, 40))
            self._draw_legend()

        elif self.state == "gameover":
            self._draw_gameover()

        pygame.display.flip()

    def _draw_legend(self):
        """Painel de transformacoes geometricas (canto inferior direito)."""
        items = [
            ("MOVIMENTAÇÃO", "WASD", C_GREEN)
        ]
        panel_w, panel_h = 240, len(items)*18 + 10
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 120))
        self.screen.blit(s, (SCREEN_W - panel_w - 6, SCREEN_H - panel_h - 6))
        for i, (name, desc, color) in enumerate(items):
            y  = SCREEN_H - panel_h - 6 + 5 + i*18
            t1 = self.font_sm.render(f"  {name}: ", True, color)
            t2 = self.font_sm.render(desc, True, C_GRAY)
            self.screen.blit(t1, (SCREEN_W - panel_w - 2, y))
            self.screen.blit(t2, (SCREEN_W - panel_w - 2 + t1.get_width(), y))

    def _draw_gameover(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        cx = SCREEN_W // 2

        t = self.font_big.render("GAME OVER", True, C_RED)
        self.screen.blit(t, (cx - t.get_width()//2, 200))

        mins, secs = self.elapsed_s // 60, self.elapsed_s % 60
        for i, (txt, color) in enumerate([
            (f"Tempo de Sobrevivencia: {mins:02d}:{secs:02d}", C_GOLD),
            (f"Inimigos Eliminados:    {self.score}",          C_PURPLE),
        ]):
            s = self.font_med.render(txt, True, color)
            self.screen.blit(s, (cx - s.get_width()//2, 270 + i*36))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            r = self.font_med.render("Pressione  R  para jogar novamente", True, C_WHITE)
            self.screen.blit(r, (cx - r.get_width()//2, 370))

        self.screen.blit(
            self.font_sm.render("ESC = Sair", True, C_GRAY), (cx - 40, 420))

        head = self.font_sm.render("Transformacoes Geometricas Implementadas:", True, C_GRAY)
        self.screen.blit(head, (cx - head.get_width()//2, 470))
        done = self.font_sm.render("TRANSLACAO  ROTACAO  ESCALA  REFLEXAO", True, C_GREEN)
        self.screen.blit(done, (cx - done.get_width()//2, 492))
