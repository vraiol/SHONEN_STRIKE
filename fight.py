# ============================================================
#  fight.py
#  Tela de luta: renderização do cenário, HUD e loop de combate.
# ============================================================

import pygame
import math
import os
import sys

from character import Character, STATE_DEAD, CHAR_W, CHAR_H, FLOOR_Y
from combat    import CombatManager
from enemy_ai  import EnemyAI

SW, SH = 1000, 620

# Paleta HUD
C_HP_GREEN  = ( 60, 220,  80)
C_HP_YELLOW = (220, 200,  40)
C_HP_RED    = (220,  50,  50)
C_BG_HUD    = (  0,   0,   0, 160)
C_WHITE     = (255, 255, 255)
C_GRAY      = (100, 100, 120)
C_GOLD      = (255, 200,  50)
C_BLACK     = (  0,   0,   0)


def _hp_color(ratio: float) -> tuple:
    if ratio > 0.5:
        return C_HP_GREEN
    if ratio > 0.25:
        return C_HP_YELLOW
    return C_HP_RED


def _load_bg(stage_data: dict) -> pygame.Surface:
    """Carrega cenário ou gera um procedural como fallback."""
    path = stage_data.get("background", "")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, (SW, SH))
        except Exception:
            pass

    # Fallback procedural estilo Deserto
    surf = pygame.Surface((SW, SH))
    
    # Céu (gradiente)
    for y in range(SH):
        t = y / SH
        r = int(100 + (180 - 100) * t)
        g = int(180 + (220 - 180) * t)
        b = 255
        pygame.draw.line(surf, (r, g, b), (0, y), (SW, y))

    import random
    random.seed(42) # semente fixa para o mesmo cenário

    # Nuvens 
    for _ in range(12):
        cx = random.randint(0, SW)
        cy = random.randint(20, 200)
        for _ in range(5):
            pygame.draw.circle(surf, (255, 255, 255, 180),
                               (cx + random.randint(-40, 40), cy + random.randint(-20, 20)),
                               random.randint(20, 45))

    # Montanhas (brown)
    points1 = [(0, FLOOR_Y), (250, 250), (600, FLOOR_Y)]
    pygame.draw.polygon(surf, (150, 90, 45), points1)
    points2 = [(400, FLOOR_Y), (750, 280), (1100, FLOOR_Y)]
    pygame.draw.polygon(surf, (130, 75, 35), points2)
    points3 = [(-100, FLOOR_Y), (100, 350), (400, FLOOR_Y)]
    pygame.draw.polygon(surf, (160, 100, 50), points3)

    # Chão estilo deserto com rachaduras
    pygame.draw.rect(surf, (170, 110, 55), (0, FLOOR_Y, SW, SH - FLOOR_Y))
    for _ in range(40):
        x1 = random.randint(0, SW)
        y1 = random.randint(FLOOR_Y, SH)
        x2 = x1 + random.randint(-25, 25)
        y2 = y1 + random.randint(10, 25)
        if y2 > SH: y2 = SH
        pygame.draw.line(surf, (110, 60, 25), (x1, y1), (x2, y2), 2)

    # Pedras
    for _ in range(15):
        px = random.randint(0, SW)
        py = random.randint(FLOOR_Y + 5, SH - 15)
        pw = random.randint(30, 60)
        ph = random.randint(15, 25)
        pygame.draw.ellipse(surf, (140, 85, 45), (px, py, pw, ph))

    return surf


# ─────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────
class HUD:
    BAR_W  = 380
    BAR_H  = 30
    BAR_Y  = 20
    PAD    = 20

    def __init__(self):
        self.f_score = pygame.font.SysFont("impact", 26, bold=True)

    def draw(self, screen, player: Character, enemy: Character,
             phase: int, total_phases: int, timer_s: int | None = None):
        
        # Barra JOGADOR (amarela, lado esquerdo)
        p_ratio = max(0.0, player.hp / player.max_hp)
        self._draw_simple_bar(screen, self.PAD, self.BAR_Y, self.BAR_W, self.BAR_H, p_ratio, left=True)
        # Texto P1
        p1_txt = self.f_score.render("P1: 0", True, (255, 30, 30))
        screen.blit(p1_txt, (self.PAD, self.BAR_Y + self.BAR_H + 5))

        # Barra INIMIGO (amarela, lado direito)
        e_ratio = max(0.0, enemy.hp / enemy.max_hp)
        self._draw_simple_bar(screen, SW - self.PAD - self.BAR_W, self.BAR_Y, self.BAR_W, self.BAR_H, e_ratio, left=False)
        # Texto P2
        p2_txt = self.f_score.render("P2: 0", True, (255, 30, 30))
        screen.blit(p2_txt, (SW - self.PAD - self.BAR_W, self.BAR_Y + self.BAR_H + 5))

    def _draw_simple_bar(self, screen, x, y, w, h, ratio, left: bool):
        # Empty background 
        pygame.draw.rect(screen, (220, 220, 220), (x, y, w, h))
        
        fill_w = int(w * ratio)
        if fill_w > 0:
            if left:
                pygame.draw.rect(screen, (255, 255, 0), (x, y, fill_w, h))
            else:
                pygame.draw.rect(screen, (255, 255, 0), (x + w - fill_w, y, fill_w, h))


# ─────────────────────────────────────────────────────────
#  TELA DE LUTA
# ─────────────────────────────────────────────────────────
class FightScreen:

    FIGHT_TIMER = 99   # segundos por round (None = sem limite)

    def __init__(self, screen, clock):
        self.screen  = screen
        self.clock   = clock
        self.hud     = HUD()
        self.combat  = CombatManager()
        self.combat.set_font(pygame.font.SysFont("impact", 18, bold=True))

    def run(self, player_char: Character, enemy_char: Character,
            stage_data: dict, phase: int, total_phases: int) -> str:
        """
        Executa uma luta completa.
        Retorna: "player_win", "enemy_win" ou "timeout_draw"
        """
        self.combat.reset()

        bg      = _load_bg(stage_data)
        ai      = EnemyAI(enemy_char,
                          aggression   = stage_data.get("ai_aggression",  0.5),
                          attack_range = stage_data.get("ai_attack_range", 110))

        # Posicionar personagens
        player_char.x = 150.0
        player_char.y = float(FLOOR_Y)
        enemy_char.x  = SW - 150.0 - CHAR_W
        enemy_char.y  = float(FLOOR_Y)
        player_char.facing_right = True
        enemy_char.facing_right  = False

        frame       = 0
        timer_s     = self.FIGHT_TIMER
        timer_frame = 0

        # Contagem regressiva de início
        self._show_countdown(bg, player_char, enemy_char, stage_data, phase, total_phases)

        while True:
            self.clock.tick(60)

            # ── Eventos ───────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "quit"

            # ── Input do jogador ──────────────────────────
            if player_char.alive:
                self._handle_player_input(player_char)

            # ── IA do inimigo ─────────────────────────────
            if enemy_char.alive:
                ai.update(player_char, self.combat)

            # ── Update dos personagens ────────────────────
            player_char.update()
            enemy_char.update()

            # ── Lançar projétil do especial no final da animação ────
            for char in (player_char, enemy_char):
                if (char.state == "attack_special"
                        and char.state_timer == 1
                        and char.data["special"].get("projectile")):
                    self.combat.spawn_projectile(char)

            # ── Update do combate ─────────────────────────
            self.combat.update(player_char, enemy_char)

            # ── Timer ─────────────────────────────────────
            timer_frame += 1
            if timer_frame >= 60:
                timer_frame = 0
                timer_s = max(0, timer_s - 1)

            # ── Checar fim de luta ────────────────────────
            if not player_char.alive:
                self._show_ko(bg, player_char, enemy_char, stage_data, phase, total_phases, "KO!")
                return "enemy_win"
            if not enemy_char.alive:
                self._show_ko(bg, player_char, enemy_char, stage_data, phase, total_phases, "KO!")
                return "player_win"
            if timer_s == 0:
                # Timeout: quem tiver mais HP vence
                if player_char.hp >= enemy_char.hp:
                    return "player_win"
                return "enemy_win"

            # ── Renderizar ────────────────────────────────
            self.screen.blit(bg, (0, 0))
            enemy_char.draw(self.screen)
            player_char.draw(self.screen)
            self.combat.draw(self.screen)
            self.hud.draw(self.screen, player_char, enemy_char,
                          phase, total_phases, timer_s)

            pygame.display.flip()
            frame += 1

    # ─────────────────────────────────────────────────────
    #  INPUT DO JOGADOR
    # ─────────────────────────────────────────────────────
    def _handle_player_input(self, player: Character):
        keys = pygame.key.get_pressed()

        # Movimento
        moved = False
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player.move_left();  moved = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player.move_right(); moved = True
        if not moved:
            player.stop_horizontal()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            player.jump()
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player.crouch()
        else:
            player.stand_up()

        # Ataques (eventos processados no loop de eventos para evitar repetição)
        # Aqui verificamos pressionamento contínuo apenas para feedback imediato;
        # o cooldown interno do Character evita spam.
        if keys[pygame.K_j]:
            player.attack_light()
        if keys[pygame.K_k]:
            player.attack_medium()
        if keys[pygame.K_l]:
            player.attack_special()

    # ─────────────────────────────────────────────────────
    #  CONTAGEM REGRESSIVA
    # ─────────────────────────────────────────────────────
    def _show_countdown(self, bg, player, enemy, stage_data, phase, total_phases):
        f_count = pygame.font.SysFont("impact", 120, bold=True)
        f_fight = pygame.font.SysFont("impact",  80, bold=True)

        for label, frames in [("3", 40), ("2", 40), ("1", 40), ("LUTA!", 50)]:
            for _ in range(frames):
                self.clock.tick(60)
                self.screen.blit(bg, (0, 0))
                enemy.draw(self.screen)
                player.draw(self.screen)
                self.hud.draw(self.screen, player, enemy,
                              phase, total_phases, self.FIGHT_TIMER)

                # ESCALA: número da contagem pulsa ao aparecer
                # (aqui usamos tamanho fixo por simplicidade, mas
                #  a escala visual é aplicada via transform.scale abaixo)
                pulse = 1.0 + 0.02 * math.sin(_ * 0.3)
                is_fight = label == "LUTA!"
                color = (255, 60, 60) if is_fight else (255, 220, 50)
                raw   = f_fight.render(label, True, color) if is_fight \
                        else f_count.render(label, True, color)
                sw2 = int(raw.get_width()  * pulse)
                sh2 = int(raw.get_height() * pulse)
                # ESCALA aplicada via pygame.transform.scale
                scaled = pygame.transform.scale(raw, (sw2, sh2))
                self.screen.blit(scaled, (SW//2 - sw2//2, SH//2 - sh2//2))

                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()

    # ─────────────────────────────────────────────────────
    #  TELA DE KO
    # ─────────────────────────────────────────────────────
    def _show_ko(self, bg, player, enemy, stage_data, phase, total_phases, label):
        f_ko = pygame.font.SysFont("impact", 100, bold=True)
        for i in range(90):
            self.clock.tick(60)
            self.screen.blit(bg, (0, 0))
            enemy.draw(self.screen)
            player.draw(self.screen)
            self.hud.draw(self.screen, player, enemy, phase, total_phases)

            # ESCALA: "KO!" cresce ao aparecer
            scale = min(1.0, 0.3 + i * 0.025)
            raw   = f_ko.render(label, True, (255, 60, 60))
            sw2   = int(raw.get_width()  * scale)
            sh2   = int(raw.get_height() * scale)
            # ESCALA via pygame.transform.scale
            scaled = pygame.transform.scale(raw, (sw2, sh2))
            self.screen.blit(scaled, (SW//2 - sw2//2, SH//2 - sh2//2))

            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
