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
from character_select import draw_pause_overlay

SW, SH = 1000, 620

# Paleta HUD
C_HP_GREEN   = ( 60, 220,  80)
C_HP_YELLOW  = (220, 200,  40)
C_HP_RED     = (220,  50,  50)
C_BG_HUD     = (  0,   0,   0, 160)
C_WHITE      = (255, 255, 255)
C_GRAY       = (100, 100, 120)
C_GOLD       = (255, 200,  50)
C_BLACK      = (  0,   0,   0)
C_DARK       = ( 15,  10,  20)
C_BORDER     = (200, 160,  40)
C_LAG        = (255, 200, 100)   # cor da barra de dano atrasado
C_HP_GLOW_HI = (120, 255, 160)   # topo do gradiente (HP alto)
C_HP_GLOW_LO = (255,  60,  60)   # topo do gradiente (HP baixo)


def _hp_color(ratio: float) -> tuple:
    if ratio > 0.5:
        return C_HP_GREEN
    if ratio > 0.25:
        return C_HP_YELLOW
    return C_HP_RED


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _draw_rounded_rect(surf, color, rect, radius=6, border=0, border_color=None):
    """Desenha retângulo com cantos arredondados."""
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


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
    BAR_W   = 390
    BAR_H   = 22
    BAR_Y   = 14
    PAD     = 12
    NAME_H  = 20   # altura do bloco de nome
    TOTAL_H = 70   # altura total do painel HUD de cada lado

    def __init__(self):
        self.f_name  = pygame.font.SysFont("impact", 18, bold=True)
        self.f_timer = pygame.font.SysFont("impact", 38, bold=True)
        self.f_hp    = pygame.font.SysFont("impact", 13)
        # Dano atrasado (lag bar) — rastreia o HP anterior
        self._p_lag  = 1.0   # ratio atual da lag bar do player
        self._e_lag  = 1.0   # ratio atual da lag bar do enemy
        self._LAG_SPEED = 0.008  # velocidade de drain da lag

    def draw(self, screen, player: Character, enemy: Character,
             phase: int, total_phases: int, timer_s: int | None = None):

        p_ratio = max(0.0, player.hp / player.max_hp)
        e_ratio = max(0.0, enemy.hp  / enemy.max_hp)

        # Avançar lag bars
        if self._p_lag > p_ratio:
            self._p_lag = max(p_ratio, self._p_lag - self.LAG_SPEED)
        else:
            self._p_lag = p_ratio
        if self._e_lag > e_ratio:
            self._e_lag = max(e_ratio, self._e_lag - self.LAG_SPEED)
        else:
            self._e_lag = e_ratio

        # ── Painel esquerdo (Player) ──────────────────────
        px = self.PAD
        py = self.BAR_Y
        self._draw_panel(screen, px, py, self.BAR_W, player, p_ratio,
                         self._p_lag, left=True, label="P1")

        # ── Painel direito (Enemy) ────────────────────────
        ex = SW - self.PAD - self.BAR_W
        ey = self.BAR_Y
        self._draw_panel(screen, ex, ey, self.BAR_W, enemy, e_ratio,
                         self._e_lag, left=False, label="CPU")

        # ── Timer central ────────────────────────────────
        if timer_s is not None:
            self._draw_timer(screen, timer_s)

        # ── Fase (indicador de bolinhas) ──────────────────
        self._draw_phase(screen, phase, total_phases)

    # ------------------------------------------------------------------
    LAG_SPEED = 0.008

    def _draw_panel(self, screen, x, y, w, char, ratio, lag_ratio, left, label):
        panel_h = self.NAME_H + 6 + self.BAR_H + 2
        # Sombra / fundo escuro do painel inteiro
        shadow = pygame.Surface((w + 4, panel_h + 4), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 120))
        screen.blit(shadow, (x - 2, y - 2))

        # ── Faixa do nome ──────────────────────────────
        name_rect = pygame.Rect(x, y, w, self.NAME_H)
        # Fundo da faixa: gradiente escuro com borda dourada
        name_bg = pygame.Surface((w, self.NAME_H), pygame.SRCALPHA)
        for i in range(self.NAME_H):
            t = i / self.NAME_H
            c = _lerp_color((30, 20, 40), (15, 10, 25), t)
            pygame.draw.line(name_bg, c, (0, i), (w, i))
        screen.blit(name_bg, (x, y))
        pygame.draw.rect(screen, C_BORDER, name_rect, 1, border_radius=3)

        # Linha decorativa dourada abaixo do nome
        pygame.draw.line(screen, C_GOLD, (x, y + self.NAME_H), (x + w, y + self.NAME_H), 1)

        # Texto do nome
        char_name = char.data.get("name", label)
        # Abreviar se muito longo
        if len(char_name) > 22:
            char_name = char_name[:21] + "."
        name_surf = self.f_name.render(char_name, True, C_GOLD)
        if not left:
            # Espelhar alinhamento para o lado direito
            screen.blit(name_surf, (x + w - name_surf.get_width() - 6, y + 1))
        else:
            screen.blit(name_surf, (x + 6, y + 1))

        # Tag P1/CPU pequena no canto oposto
        tag_surf = self.f_hp.render(label, True, (180, 180, 180))
        if left:
            screen.blit(tag_surf, (x + w - tag_surf.get_width() - 5, y + 3))
        else:
            screen.blit(tag_surf, (x + 5, y + 3))

        # ── Barra de HP ─────────────────────────────────
        bar_y = y + self.NAME_H + 5
        bar_rect = pygame.Rect(x, bar_y, w, self.BAR_H)

        # Fundo da barra (preto profundo)
        pygame.draw.rect(screen, (10, 8, 15), bar_rect, border_radius=4)

        # Lag bar (laranja — dano atrasado)
        lag_w = int(w * lag_ratio)
        if lag_w > 0:
            lag_rect = (x if left else x + w - lag_w, bar_y, lag_w, self.BAR_H)
            pygame.draw.rect(screen, C_LAG, lag_rect, border_radius=4)

        # Barra de HP principal com gradiente vertical
        hp_w = int(w * ratio)
        if hp_w > 0:
            hp_color_bot = _hp_color(ratio)
            hp_color_top = _lerp_color(hp_color_bot, C_WHITE, 0.45)
            hp_surf = pygame.Surface((hp_w, self.BAR_H), pygame.SRCALPHA)
            for i in range(self.BAR_H):
                t = i / max(1, self.BAR_H - 1)
                col = _lerp_color(hp_color_top, hp_color_bot, t)
                pygame.draw.line(hp_surf, col, (0, i), (hp_w, i))
            # Reflexo brilhante no topo
            hl_h = max(2, self.BAR_H // 4)
            hl = pygame.Surface((hp_w, hl_h), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 55))
            hp_surf.blit(hl, (0, 0))
            hp_x = x if left else x + w - hp_w
            screen.blit(hp_surf, (hp_x, bar_y))

        # Borda dourada da barra
        pygame.draw.rect(screen, C_BORDER, bar_rect, 2, border_radius=4)

        # Linhas de divisão (25% e 50%)
        for frac in (0.25, 0.5, 0.75):
            div_x = x + int(w * frac)
            pygame.draw.line(screen, (60, 45, 80), (div_x, bar_y + 1), (div_x, bar_y + self.BAR_H - 2), 1)

        # HP numérico
        hp_str = f"{max(0, char.hp)} / {char.max_hp}"
        hp_txt = self.f_hp.render(hp_str, True, (200, 200, 200))
        hp_txt_x = x + 6 if left else x + w - hp_txt.get_width() - 6
        screen.blit(hp_txt, (hp_txt_x, bar_y + (self.BAR_H - hp_txt.get_height()) // 2))

    def _draw_timer(self, screen, timer_s):
        """Timer central com moldura anime."""
        cx = SW // 2
        ty = self.BAR_Y

        # Moldura do timer
        box_w, box_h = 74, 52
        box_x = cx - box_w // 2

        # Fundo escuro semi-transparente
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        for i in range(box_h):
            t = i / box_h
            c = _lerp_color((35, 20, 50), (15, 8, 25), t) + (210,)
            pygame.draw.line(box_surf, c, (0, i), (box_w, i))
        screen.blit(box_surf, (box_x, ty))

        # Borda dourada
        pygame.draw.rect(screen, C_GOLD, (box_x, ty, box_w, box_h), 2, border_radius=5)
        # Linha decorativa interior
        pygame.draw.rect(screen, C_BORDER, (box_x + 3, ty + 3, box_w - 6, box_h - 6), 1, border_radius=3)

        # Número
        urgent = timer_s <= 10
        color = (255, 60, 60) if urgent else C_WHITE
        txt = self.f_timer.render(str(timer_s), True, color)
        screen.blit(txt, txt.get_rect(center=(cx, ty + box_h // 2)))

        # Sombra de texto para legibilidade
        shadow_txt = self.f_timer.render(str(timer_s), True, (0, 0, 0))
        # (renderizado atrás — reposicionamos ambos)
        screen.blit(shadow_txt, shadow_txt.get_rect(center=(cx + 2, ty + box_h // 2 + 2)))
        screen.blit(txt, txt.get_rect(center=(cx, ty + box_h // 2)))

    def _draw_phase(self, screen, phase, total):
        """Bolinhas indicando a fase atual embaixo do timer."""
        cx = SW // 2
        dot_y = self.BAR_Y + 56
        spacing = 14
        total_w = (total - 1) * spacing
        start_x = cx - total_w // 2
        for i in range(total):
            dx = start_x + i * spacing
            filled = (i < phase)
            color = C_GOLD if filled else (60, 50, 80)
            pygame.draw.circle(screen, color, (dx, dot_y), 5)
            pygame.draw.circle(screen, C_BORDER, (dx, dot_y), 5, 1)


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
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        action = self._show_pause_menu(bg, player_char, enemy_char, phase, total_phases, timer_s)
                        if action == "quit":
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

            # ── Lançar projétil do especial no momento certo ────
            for char in (player_char, enemy_char):
                if char.state == "attack_special":
                    if not getattr(char, "_proj_spawned", False):
                        # Dispara quando chegar na metade da animação (ou quando timer cair abaixo de metade)
                        half = char.state_timer <= char.data["special"].get("cooldown", 60) // 2
                        if half and char.data["special"].get("projectile"):
                            self.combat.spawn_projectile(char)
                            char._proj_spawned = True
                else:
                    char._proj_spawned = False

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

    # ─────────────────────────────────────────────────────
    #  MENU DE PAUSA
    # ─────────────────────────────────────────────────────
    def _show_pause_menu(self, bg, player, enemy, phase, total_phases, timer_s):
        # Renderizar frame atual antes de pausar
        self.screen.blit(bg, (0, 0))
        enemy.draw(self.screen)
        player.draw(self.screen)
        self.combat.draw(self.screen)
        self.hud.draw(self.screen, player, enemy, phase, total_phases, timer_s)
        # Chamar overlay de pausa animado
        return draw_pause_overlay(self.screen, self.clock, SW, SH, None, None)
