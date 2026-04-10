import pygame
import sys
import math
import os
import random

# ── Paleta de cores ──────────────────────────────────────────────────────────
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
BG_TOP      = (10, 0, 30)
BG_BOT      = (30, 0, 10)
ORANGE      = (255, 120, 0)
ORANGE_DIM  = (180, 70, 0)
YELLOW      = (255, 220, 50)
RED         = (220, 30, 30)
GRAY_DARK   = (30, 30, 40)
GRAY_LIGHT  = (180, 180, 200)
CYAN        = (0, 220, 255)

# ── Caminho da imagem de fundo ───────────────────────────────────────────────
_BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
BG_IMAGE_PATH = os.path.join(_BASE_DIR, "imagens", "menu.png")

# ── Controles exibidos na tela de controles ──────────────────────────────────
controls_info = [
    ("MOVIMENTAÇÃO",  "W / A / S / D  ou  ← ↑ ↓ →  "),
    ("ATACAR",        "J                          "),
    ("DESVIAR",       "K                          "),
    ("ESPECIAL",      "L                          "),
    ("PAUSAR",        "ESC  ou  Enter"),
]

# ── Estados internos do menu ─────────────────────────────────────────────────
STATE_MAIN     = "main"
STATE_CONTROLS = "controls"



# ── Botão genérico ────────────────────────────────────────────────────────────
class Button:
    def __init__(self, text, x, y, w=160, h=34):
        self.text    = text
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.hovered = False
        self.scale   = 1.0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, mouse_pos):
        self.hovered = self.rect().collidepoint(mouse_pos)
        target = 1.07 if self.hovered else 1.0
        self.scale += (target - self.scale) * 0.15

    def draw(self, surf, font):
        sw = int(self.w * self.scale)
        sh = int(self.h * self.scale)
        sx = self.x - int((sw - self.w) / 2)
        sy = self.y + (self.h - sh) // 2

        btn_rect = pygame.Rect(sx, sy, sw, sh)

        # sombra
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=8)
        surf.blit(shadow_surf, (sx + 3, sy + 3))

        # fundo
        btn_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        if self.hovered:
            pygame.draw.rect(btn_surf, (255, 140, 0, 100), btn_surf.get_rect(), border_radius=8)
        else:
            pygame.draw.rect(btn_surf, (0, 0, 0, 60), btn_surf.get_rect(), border_radius=8)
        surf.blit(btn_surf, (sx, sy))

        # borda
        border_color = YELLOW if self.hovered else ORANGE_DIM
        pygame.draw.rect(surf, border_color, btn_rect, width=2, border_radius=8)

        # texto
        color     = YELLOW if self.hovered else WHITE
        text_surf = font.render(self.text, True, color)
        surf.blit(text_surf, text_surf.get_rect(center=btn_rect.center))

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect().collidepoint(event.pos))


# ── Helpers de desenho ────────────────────────────────────────────────────────
def _draw_background(surf, bg_image, use_bg, width, height):
    if use_bg and bg_image:
        surf.blit(bg_image, (0, 0))
    else:
        for y in range(height):
            t = y / height
            r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (width, y))



def _draw_title(surf, tick, font_title, width):
    for offset, color in [((4, 4), RED), ((2, 2), ORANGE)]:
        shadow = font_title.render("SHONEN STRIKE", True, color)
        sr = shadow.get_rect(center=(width // 2 + offset[0], 50 + offset[1]))
        surf.blit(shadow, sr)
    title_surf = font_title.render("SHONEN STRIKE", True, YELLOW)
    surf.blit(title_surf, title_surf.get_rect(center=(width // 2, 50)))


def _draw_controls_screen(surf, tick, mouse_pos, fonts, width, height, bg_image, use_bg):
    _draw_background(surf, bg_image, use_bg, width, height)

    panel_w, panel_h = 680, 420
    panel_x = width  // 2 - panel_w // 2
    panel_y = height // 2 - panel_h // 2

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 160), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (*ORANGE_DIM, 180), panel.get_rect(), width=2, border_radius=16)
    surf.blit(panel, (panel_x, panel_y))

    font_ctrl = fonts["ctrl"]
    t = font_ctrl.render("CONTROLES", True, YELLOW)
    surf.blit(t, t.get_rect(center=(width // 2, panel_y + 28)))

    sep_y = panel_y + 54
    sep = pygame.Surface((panel_w - 60, 1), pygame.SRCALPHA)
    sep.fill((255, 255, 255, 60))
    surf.blit(sep, (panel_x + 30, sep_y))

    row_h      = 58
    start_y    = sep_y + 16
    col_action = panel_x + 40
    col_keys   = panel_x + panel_w // 2 + 10

    for i, (action, keys) in enumerate(controls_info):
        row_y = start_y + i * row_h
        if i % 2 == 0:
            row_bg = pygame.Surface((panel_w - 20, row_h - 6), pygame.SRCALPHA)
            pygame.draw.rect(row_bg, (255, 255, 255, 18), row_bg.get_rect(), border_radius=6)
            surf.blit(row_bg, (panel_x + 10, row_y))
        a_surf = font_ctrl.render(action, True, ORANGE)
        surf.blit(a_surf, a_surf.get_rect(midleft=(col_action, row_y + row_h // 2)))
        k_surf = font_ctrl.render(keys, True, WHITE)
        surf.blit(k_surf, k_surf.get_rect(midleft=(col_keys, row_y + row_h // 2)))

    back_rect = pygame.Rect(width // 2 - 90, panel_y + panel_h - 52, 180, 38)
    hov       = back_rect.collidepoint(mouse_pos)
    back_surf = pygame.Surface((180, 38), pygame.SRCALPHA)
    pygame.draw.rect(back_surf,
                     (255, 140, 0, 120) if hov else (0, 0, 0, 80),
                     back_surf.get_rect(), border_radius=8)
    surf.blit(back_surf, back_rect.topleft)
    pygame.draw.rect(surf, YELLOW if hov else ORANGE_DIM, back_rect, width=2, border_radius=8)
    back_txt = font_ctrl.render("← VOLTAR", True, YELLOW if hov else GRAY_LIGHT)
    surf.blit(back_txt, back_txt.get_rect(center=back_rect.center))
    return back_rect


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNÇÃO PRINCIPAL – chamada pelo main.py
# ═══════════════════════════════════════════════════════════════════════════════
def show_main_menu(screen, clock):
    """Exibe o menu principal e retorna 'play' ou 'quit'."""

    width, height = screen.get_size()

    # Fontes
    try:
        fonts = {
            "title": pygame.font.SysFont("Impact", 70),
            "sub":   pygame.font.SysFont("Impact", 22),
            "btn":   pygame.font.SysFont("Impact", 28),
            "ctrl":  pygame.font.SysFont("Impact", 32),
            "small": pygame.font.SysFont("Arial",  18),
        }
    except Exception:
        fonts = {
            "title": pygame.font.Font(None, 60),
            "sub":   pygame.font.Font(None, 22),
            "btn":   pygame.font.Font(None, 42),
            "ctrl":  pygame.font.Font(None, 32),
            "small": pygame.font.Font(None, 18),
        }

    # Imagem de fundo
    try:
        bg_image = pygame.image.load(BG_IMAGE_PATH).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (width, height))
        use_bg   = True
    except Exception:
        bg_image = None
        use_bg   = False

    # Botões do menu principal
    _BX  = 20
    _GAP = 50
    _BY  = height - 50
    btn_play  = Button("JOGAR",     _BX, _BY - _GAP * 2)
    btn_ctrl  = Button("CONTROLES", _BX, _BY - _GAP)
    btn_quit  = Button("SAIR",      _BX, _BY)
    main_btns = [btn_play, btn_ctrl, btn_quit]

    state = STATE_MAIN
    tick  = 0

    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()
        back_rect = None

        # ── Eventos ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if state == STATE_MAIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "quit"
                if btn_play.is_clicked(event):
                    return "play"
                if btn_ctrl.is_clicked(event):
                    state = STATE_CONTROLS
                if btn_quit.is_clicked(event):
                    return "quit"

            elif state == STATE_CONTROLS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = STATE_MAIN
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_rect and back_rect.collidepoint(event.pos):
                        state = STATE_MAIN

        # ── Render ────────────────────────────────────────────────────────────
        if state == STATE_MAIN:
            _draw_background(screen, bg_image, use_bg, width, height)
            _draw_title(screen, tick, fonts["title"], width)

            for btn in main_btns:
                btn.update(mouse_pos)
                btn.draw(screen, fonts["btn"])

            footer = fonts["small"].render("© 2025 Shonen Strike  –  v0.1", True, (80, 80, 100))
            screen.blit(footer, footer.get_rect(bottomright=(width - 20, height - 10)))

        elif state == STATE_CONTROLS:
            back_rect = _draw_controls_screen(
                screen, tick, mouse_pos, fonts, width, height, bg_image, use_bg)

        pygame.display.flip()
        clock.tick(60)


# ═══════════════════════════════════════════════════════════════════════════════
#  TELAS DE VITÓRIA / DERROTA – chamadas pelo main.py
# ═══════════════════════════════════════════════════════════════════════════════
def show_victory(screen, clock, winner_name="", phase=1, total_phases=3):
    """Tela de vitória. Retorna 'continue' ou 'menu'."""
    width, height = screen.get_size()
    try:
        font_big   = pygame.font.SysFont("Impact", 72)
        font_mid   = pygame.font.SysFont("Impact", 36)
        font_small = pygame.font.SysFont("Arial",  22)
    except Exception:
        font_big   = pygame.font.Font(None, 72)
        font_mid   = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 22)

    btn_continue = Button("CONTINUAR", width // 2 - 90, height // 2 + 60, w=180, h=42)
    btn_menu     = Button("MENU",      width // 2 - 60, height // 2 + 118, w=120, h=42)

    tick = 0
    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if btn_continue.is_clicked(event):
                return "continue"
            if btn_menu.is_clicked(event):
                return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return "continue"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        # fundo escuro semitransparente
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pulse = 1.0 + 0.04 * math.sin(tick * 0.08)
        txt   = font_big.render("VITÓRIA!", True, YELLOW)
        txt   = pygame.transform.rotozoom(txt, 0, pulse)
        screen.blit(txt, txt.get_rect(center=(width // 2, height // 2 - 80)))

        sub = font_mid.render(
            f"{winner_name}  –  Fase {phase}/{total_phases}", True, WHITE)
        screen.blit(sub, sub.get_rect(center=(width // 2, height // 2 - 10)))

        for btn in [btn_continue, btn_menu]:
            btn.update(mouse_pos)
            btn.draw(screen, font_small)

        pygame.display.flip()
        clock.tick(60)


def show_defeat(screen, clock, loser_name=""):
    """Tela de derrota. Retorna 'retry' ou 'menu'."""
    width, height = screen.get_size()
    try:
        font_big   = pygame.font.SysFont("Arial", 72)
        font_mid   = pygame.font.SysFont("Arial", 36)
        font_small = pygame.font.SysFont("Arial",  22)
    except Exception:
        font_big   = pygame.font.Font(None, 72)
        font_mid   = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 22)

    btn_retry = Button("TENTAR NOVAMENTE", width // 2 - 120, height // 2 + 60,  w=240, h=42)
    btn_menu  = Button("MENU",             width // 2 - 60,  height // 2 + 118, w=120, h=42)

    tick = 0
    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if btn_retry.is_clicked(event):
                return "retry"
            if btn_menu.is_clicked(event):
                return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return "retry"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pulse = 1.0 + 0.04 * math.sin(tick * 0.08)
        txt   = font_big.render("DERROTA!", True, RED)
        txt   = pygame.transform.rotozoom(txt, 0, pulse)
        screen.blit(txt, txt.get_rect(center=(width // 2, height // 2 - 80)))

        sub = font_mid.render(f"{loser_name} foi derrotado!", True, GRAY_LIGHT)
        screen.blit(sub, sub.get_rect(center=(width // 2, height // 2 - 10)))

        for btn in [btn_retry, btn_menu]:
            btn.update(mouse_pos)
            btn.draw(screen, font_small)

        pygame.display.flip()
        clock.tick(60)