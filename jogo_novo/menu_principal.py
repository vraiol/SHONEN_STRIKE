import pygame
import sys
import math
import os
import random

# ── Paleta de cores ──────────────────────────────────────────────────────────
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
BG_TOP      = (5, 0, 18)
BG_BOT      = (25, 0, 8)
ORANGE      = (255, 130, 0)
ORANGE_DIM  = (180, 70, 0)
YELLOW      = (255, 215, 50)
GOLD        = (255, 195, 30)
RED         = (220, 30, 30)
RED_BRIGHT  = (255, 60, 60)
GRAY_DARK   = (30, 30, 40)
GRAY_LIGHT  = (180, 180, 200)
CYAN        = (0, 220, 255)
PURPLE      = (140, 0, 220)
BLUE_D      = (20, 10, 50)

# ── Caminho da imagem de fundo ───────────────────────────────────────────────
_BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
BG_IMAGE_PATH = os.path.join(_BASE_DIR, "imagens", "foto menu.png")

# ── Controles exibidos na tela de controles ──────────────────────────────────
controls_info = [
    ("MOVIMENTAÇÃO",  "W / A / S / D  ou  ← ↑ ↓ →"),
    ("ATAQUE LEVE",   "J"),
    ("ATAQUE MÉDIO",  "K"),
    ("ESPECIAL",      "L"),
    ("PAUSAR",        "ESC  ou  Enter"),
]

STATE_MAIN     = "main"
STATE_CONTROLS = "controls"

SW, SH = 1000, 620


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS VISUAIS
# ─────────────────────────────────────────────────────────────────────────────
def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _draw_glow_circle(surf, x, y, r, color, alpha=60):
    gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(gs, (*color, alpha), (r, r), r)
    surf.blit(gs, (x - r, y - r))

def _draw_gradient_rect(surf, rect, color_top, color_bot, alpha=255, radius=8):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    for i in range(rect.height):
        t = i / max(1, rect.height - 1)
        c = _lerp_color(color_top, color_bot, t)
        pygame.draw.line(s, (*c, alpha), (0, i), (rect.width, i))
    pygame.draw.rect(s, (0,0,0,0), s.get_rect(), border_radius=radius)  # clip
    # re-draw with radius mask
    mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255,255), mask.get_rect(), border_radius=radius)
    s2 = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s2.blit(s, (0,0))
    s2.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(s2, rect.topleft)


# ─────────────────────────────────────────────────────────────────────────────
#  PARTÍCULAS DE ENERGIA
# ─────────────────────────────────────────────────────────────────────────────
class EnergyParticle:
    def __init__(self, w, h):
        self.reset(w, h)

    def reset(self, w, h):
        self.x  = random.uniform(0, w)
        self.y  = random.uniform(0, h)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-1.2, -0.3)
        self.life    = random.randint(60, 160)
        self.max_life= self.life
        color_choice = random.choice([ORANGE, YELLOW, RED_BRIGHT, (255,80,0), GOLD])
        self.color   = color_choice
        self.r       = random.uniform(1.5, 4.0)
        self.w, self.h = w, h

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0 or self.y < -10:
            self.reset(self.w, self.h)
            self.y = self.h + 5

    def draw(self, surf):
        alpha = int(220 * self.life / self.max_life)
        r = max(1, int(self.r * self.life / self.max_life))
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        # glow
        pygame.draw.circle(s, (*self.color, alpha//3), (r+1, r+1), r+1)
        pygame.draw.circle(s, (*self.color, alpha),    (r+1, r+1), r)
        surf.blit(s, (int(self.x)-r-1, int(self.y)-r-1))


# ─────────────────────────────────────────────────────────────────────────────
#  BOTÃO ANIME PREMIUM
# ─────────────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, text, x, y, w=200, h=46):
        self.text    = text
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.hovered = False
        self.scale   = 1.0
        self._pulse  = 0.0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, mouse_pos):
        self.hovered = self.rect().collidepoint(mouse_pos)
        target = 1.06 if self.hovered else 1.0
        self.scale  += (target - self.scale) * 0.18
        self._pulse += 0.1

    def draw(self, surf, font):
        sw = int(self.w * self.scale)
        sh = int(self.h * self.scale)
        sx = self.x - (sw - self.w) // 2
        sy = self.y + (self.h - sh) // 2
        r  = pygame.Rect(sx, sy, sw, sh)

        # Sombra
        shad = pygame.Surface((sw+4, sh+4), pygame.SRCALPHA)
        pygame.draw.rect(shad, (0,0,0,100), shad.get_rect(), border_radius=10)
        surf.blit(shad, (sx+3, sy+4))

        # Fundo gradiente
        if self.hovered:
            top = (80, 40, 0)
            bot = (40, 10, 0)
            border_col = GOLD
            border_w   = 2
        else:
            top = (20, 12, 30)
            bot = (10,  5, 20)
            border_col = (120, 80, 20)
            border_w   = 1

        bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for i in range(sh):
            t = i / max(1, sh-1)
            c = _lerp_color(top, bot, t)
            alpha = 200 if self.hovered else 160
            pygame.draw.line(bg, (*c, alpha), (0,i), (sw,i))
        # mask rounded
        mask = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255,255,255,255), mask.get_rect(), border_radius=10)
        bg.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(bg, (sx, sy))

        # Borda com brilho pulsante se hovered
        if self.hovered:
            glow_alpha = int(120 + 60 * math.sin(self._pulse))
            glow_surf  = pygame.Surface((sw+6, sh+6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GOLD, glow_alpha),
                             glow_surf.get_rect(), 2, border_radius=12)
            surf.blit(glow_surf, (sx-3, sy-3))

        pygame.draw.rect(surf, border_col, r, border_w, border_radius=10)

        # Detalhe: linha interna horizontal (estilo katana)
        pygame.draw.line(surf, (*border_col, 80),
                         (sx+12, sy+sh-6), (sx+sw-12, sy+sh-6), 1)

        # Triângulo decorativo esquerdo
        tri_color = GOLD if self.hovered else (80, 60, 20)
        pts = [(sx+4, sy+sh//2), (sx+10, sy+sh//2-5), (sx+10, sy+sh//2+5)]
        pygame.draw.polygon(surf, tri_color, pts)

        # Texto
        color = YELLOW if self.hovered else (200, 180, 140)
        text_surf = font.render(self.text, True, color)
        if self.hovered:
            # sombra brilhante
            sh_surf = font.render(self.text, True, (255, 100, 0))
            surf.blit(sh_surf, sh_surf.get_rect(center=(r.centerx+2, r.centery+2)))
        surf.blit(text_surf, text_surf.get_rect(center=r.center))

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect().collidepoint(event.pos))


# ─────────────────────────────────────────────────────────────────────────────
#  FUNDO ANIMADO
# ─────────────────────────────────────────────────────────────────────────────
def _draw_background(surf, bg_image, use_bg, width, height, tick=0):
    if use_bg and bg_image:
        surf.blit(bg_image, (0, 0))
        # Overlay escuro sobre a imagem para destacar o HUD
        ov = pygame.Surface((width, height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 90))
        surf.blit(ov, (0,0))
    else:
        # Gradiente escuro
        for y in range(height):
            t = y / height
            c = _lerp_color(BG_TOP, BG_BOT, t)
            pygame.draw.line(surf, c, (0, y), (width, y))

    # Linhas diagonais de energia sutis
    line_alpha = int(18 + 8 * math.sin(tick * 0.03))
    for i in range(0, width + height, 60):
        x1 = i
        y1 = 0
        x2 = i - height
        y2 = height
        ls = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.line(ls, (*ORANGE, line_alpha), (x1,y1), (x2,y2), 1)
        surf.blit(ls, (0,0))

    # Grade de pontos
    dot_alpha = 25
    dot_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for gx in range(0, width, 50):
        for gy in range(0, height, 50):
            pygame.draw.circle(dot_surf, (*ORANGE_DIM, dot_alpha), (gx, gy), 1)
    surf.blit(dot_surf, (0,0))


# ─────────────────────────────────────────────────────────────────────────────
#  TÍTULO ANIME COM GLOW
# ─────────────────────────────────────────────────────────────────────────────
def _draw_title(surf, tick, font_title, font_sub, width):
    cy    = 110
    pulse = 1.0 + 0.015 * math.sin(tick * 0.06)
    title_text = "SHONEN STRIKE"

    # Glow vermelho profundo atrás
    for offset, color, alpha in [
        ((0,0), (200,0,0),   30),
        ((0,0), (255,80,0),  18),
    ]:
        glow_s = font_title.render(title_text, True, color)
        gw = int(glow_s.get_width() * pulse * 1.04)
        gh = int(glow_s.get_height() * pulse * 1.04)
        glow_s = pygame.transform.scale(glow_s, (gw, gh))
        glow_r = glow_s.get_rect(center=(width//2 + offset[0], cy + offset[1]))
        glow_copy = glow_s.copy()
        glow_copy.set_alpha(alpha)
        surf.blit(glow_copy, glow_r)

    # Sombras deslocadas (efeito de profundidade)
    for dx, dy, color in [(5,5,RED), (3,3,ORANGE), (1,1,(255,160,0))]:
        sh = font_title.render(title_text, True, color)
        sw2 = int(sh.get_width() * pulse)
        sh2 = int(sh.get_height() * pulse)
        sh_s = pygame.transform.scale(sh, (sw2, sh2))
        surf.blit(sh_s, sh_s.get_rect(center=(width//2+dx, cy+dy)))

    # Texto principal dourado
    main_s = font_title.render(title_text, True, YELLOW)
    mw = int(main_s.get_width() * pulse)
    mh_val = int(main_s.get_height() * pulse)
    main_s = pygame.transform.scale(main_s, (mw, mh_val))
    surf.blit(main_s, main_s.get_rect(center=(width//2, cy)))

    # Linha decorativa ondulante embaixo do título
    line_y = cy + mh_val // 2 + 6
    lw_half = int(160 + 40 * math.sin(tick * 0.05))
    # Linha dourada central
    pygame.draw.line(surf, GOLD, (width//2 - lw_half, line_y),
                     (width//2 + lw_half, line_y), 2)
    # Pontos nas extremidades
    pygame.draw.circle(surf, ORANGE, (width//2 - lw_half, line_y), 4)
    pygame.draw.circle(surf, ORANGE, (width//2 + lw_half, line_y), 4)

    # Subtítulo
    sub_y  = line_y + 14
    chars  = "— O Jogo de Luta Anime —"
    sub_s  = font_sub.render(chars, True, (200, 160, 80))
    surf.blit(sub_s, sub_s.get_rect(center=(width//2, sub_y)))


# ─────────────────────────────────────────────────────────────────────────────
#  TELA DE CONTROLES
# ─────────────────────────────────────────────────────────────────────────────
def _draw_controls_screen(surf, tick, mouse_pos, fonts, width, height, bg_image, use_bg):
    _draw_background(surf, bg_image, use_bg, width, height, tick)

    panel_w, panel_h = 700, 440
    panel_x = width  // 2 - panel_w // 2
    panel_y = height // 2 - panel_h // 2

    # Fundo do painel com gradiente
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    for i in range(panel_h):
        t = i / panel_h
        c = _lerp_color((20, 10, 35), (10, 5, 20), t)
        pygame.draw.line(panel, (*c, 220), (0, i), (panel_w, i))
    # mask
    mask = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255,255), mask.get_rect(), border_radius=14)
    panel.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(panel, (panel_x, panel_y))

    # Borda dourada dupla
    pygame.draw.rect(surf, GOLD,       (panel_x, panel_y, panel_w, panel_h), 2, border_radius=14)
    pygame.draw.rect(surf, ORANGE_DIM, (panel_x+4, panel_y+4, panel_w-8, panel_h-8), 1, border_radius=11)

    # Cabeçalho da tela
    head_surf = pygame.Surface((panel_w, 46), pygame.SRCALPHA)
    for i in range(46):
        t = i / 46
        c = _lerp_color((80, 30, 0), (40, 10, 0), t)
        pygame.draw.line(head_surf, (*c, 200), (0, i), (panel_w, i))
    surf.blit(head_surf, (panel_x, panel_y))

    font_ctrl = fonts["ctrl"]
    t_title = font_ctrl.render("CONTROLES", True, GOLD)
    surf.blit(t_title, t_title.get_rect(center=(width // 2, panel_y + 23)))

    # Linha separadora decorativa
    sep_y = panel_y + 48
    pygame.draw.line(surf, GOLD,       (panel_x + 6,  sep_y), (panel_x + panel_w - 6,  sep_y), 1)
    pygame.draw.line(surf, ORANGE_DIM, (panel_x + 20, sep_y+2), (panel_x + panel_w - 20, sep_y+2), 1)

    row_h   = 62
    start_y = sep_y + 12
    col_a   = panel_x + 44
    col_k   = panel_x + panel_w // 2 + 20

    for i, (action, keys) in enumerate(controls_info):
        row_y = start_y + i * row_h
        # Linha de fundo alternada
        if i % 2 == 0:
            row_bg = pygame.Surface((panel_w - 24, row_h - 8), pygame.SRCALPHA)
            pygame.draw.rect(row_bg, (255, 200, 100, 14), row_bg.get_rect(), border_radius=6)
            surf.blit(row_bg, (panel_x + 12, row_y + 2))

        # Ícone quadrado à esquerda
        icon_rect = pygame.Rect(col_a - 22, row_y + row_h//2 - 6, 12, 12)
        pygame.draw.rect(surf, ORANGE, icon_rect, border_radius=2)

        a_surf = font_ctrl.render(action, True, ORANGE)
        surf.blit(a_surf, a_surf.get_rect(midleft=(col_a, row_y + row_h // 2)))

        # Chave com moldura
        k_bg = pygame.Surface((200, 28), pygame.SRCALPHA)
        pygame.draw.rect(k_bg, (255,255,255,18), k_bg.get_rect(), border_radius=5)
        pygame.draw.rect(k_bg, (100,80,20,120), k_bg.get_rect(), 1, border_radius=5)
        surf.blit(k_bg, (col_k - 4, row_y + row_h // 2 - 14))
        k_surf = font_ctrl.render(keys, True, WHITE)
        surf.blit(k_surf, k_surf.get_rect(midleft=(col_k + 6, row_y + row_h // 2)))

    # Botão voltar
    back_rect = pygame.Rect(width // 2 - 100, panel_y + panel_h - 54, 200, 40)
    hov       = back_rect.collidepoint(mouse_pos)
    back_bg   = pygame.Surface((200, 40), pygame.SRCALPHA)
    top_c     = (80,40,0) if hov else (20,12,30)
    bot_c     = (40,10,0) if hov else (10,5,20)
    for i in range(40):
        t = i/40; c = _lerp_color(top_c, bot_c, t)
        pygame.draw.line(back_bg, (*c, 200), (0,i), (200,i))
    mask2 = pygame.Surface((200,40), pygame.SRCALPHA)
    pygame.draw.rect(mask2, (255,255,255,255), mask2.get_rect(), border_radius=8)
    back_bg.blit(mask2, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(back_bg, back_rect.topleft)
    pygame.draw.rect(surf, GOLD if hov else ORANGE_DIM, back_rect, 2, border_radius=8)
    back_txt = font_ctrl.render("← VOLTAR", True, YELLOW if hov else GRAY_LIGHT)
    surf.blit(back_txt, back_txt.get_rect(center=back_rect.center))
    return back_rect


# ═════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════
def show_main_menu(screen, clock):
    width, height = screen.get_size()

    try:
        fonts = {
            "title": pygame.font.SysFont("Impact", 82),
            "sub":   pygame.font.SysFont("Impact", 22),
            "btn":   pygame.font.SysFont("Impact", 30),
            "ctrl":  pygame.font.SysFont("Impact", 28),
            "small": pygame.font.SysFont("Arial",  16),
        }
    except Exception:
        fonts = {
            "title": pygame.font.Font(None, 82),
            "sub":   pygame.font.Font(None, 22),
            "btn":   pygame.font.Font(None, 30),
            "ctrl":  pygame.font.Font(None, 28),
            "small": pygame.font.Font(None, 16),
        }

    try:
        bg_image = pygame.image.load(BG_IMAGE_PATH).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (width, height))
        use_bg   = True
    except Exception:
        bg_image = None
        use_bg   = False

    # Partículas de energia
    particles = [EnergyParticle(width, height) for _ in range(55)]

    # Botões — lado esquerdo inferior
    BX  = 38
    BY  = height - 62
    GAP = 58
    btn_play  = Button("▶  JOGAR",      BX, BY - GAP * 2, w=220, h=46)
    btn_ctrl  = Button("   CONTROLES",  BX, BY - GAP,     w=220, h=46)
    btn_quit  = Button("   SAIR",       BX, BY,            w=220, h=46)
    main_btns = [btn_play, btn_ctrl, btn_quit]

    state = STATE_MAIN
    tick  = 0

    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()
        back_rect = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if state == STATE_MAIN:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "quit"
                if btn_play.is_clicked(event):  return "play"
                if btn_ctrl.is_clicked(event):  state = STATE_CONTROLS
                if btn_quit.is_clicked(event):  return "quit"
            elif state == STATE_CONTROLS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = STATE_MAIN
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_rect and back_rect.collidepoint(event.pos):
                        state = STATE_MAIN

        # ── Render ───────────────────────────────────────────────────────────
        if state == STATE_MAIN:
            _draw_background(screen, bg_image, use_bg, width, height, tick)

            # Partículas
            for p in particles:
                p.update()
                p.draw(screen)

            # Vinheta (escurecer bordas)
            vig = pygame.Surface((width, height), pygame.SRCALPHA)
            for i in range(180):
                t = i / 180
                a = int(160 * (1 - t))
                pygame.draw.rect(vig, (0,0,0,a), (i, i, width-i*2, height-i*2), 1)
            screen.blit(vig, (0,0))

            # Faixa lateral esquerda (onde ficam os botões)
            side_bar = pygame.Surface((270, height), pygame.SRCALPHA)
            for i in range(270):
                t = i / 270
                a = int(180 * (1 - t * 0.7))
                pygame.draw.line(side_bar, (0,0,0,a), (i,0), (i,height))
            screen.blit(side_bar, (0,0))

            _draw_title(screen, tick, fonts["title"], fonts["sub"], width)

            for btn in main_btns:
                btn.update(mouse_pos)
                btn.draw(screen, fonts["btn"])

            # Linha decorativa vertical ao lado dos botões
            line_x = BX + 230
            lg_len = int(90 + 30 * math.sin(tick * 0.04))
            for bi, btn in enumerate(main_btns):
                cy = btn.y + btn.h // 2
                pygame.draw.line(screen, (*GOLD, 80),
                                 (line_x, cy - lg_len//2),
                                 (line_x, cy + lg_len//2), 1)
                pygame.draw.circle(screen, GOLD, (line_x, cy), 3)

            footer = fonts["small"].render("© 2025 Shonen Strike  –  v0.2", True, (70, 65, 90))
            screen.blit(footer, footer.get_rect(bottomright=(width - 14, height - 8)))

        elif state == STATE_CONTROLS:
            back_rect = _draw_controls_screen(
                screen, tick, mouse_pos, fonts, width, height, bg_image, use_bg)

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════════════════════════
#  VITÓRIA
# ═════════════════════════════════════════════════════════════════════════════
def show_victory(screen, clock, winner_name="", phase=1, total_phases=3):
    width, height = screen.get_size()
    try:
        font_big   = pygame.font.SysFont("Impact", 80)
        font_mid   = pygame.font.SysFont("Impact", 34)
        font_small = pygame.font.SysFont("Impact", 24)
    except Exception:
        font_big   = pygame.font.Font(None, 80)
        font_mid   = pygame.font.Font(None, 34)
        font_small = pygame.font.Font(None, 24)

    btn_continue = Button("PRÓXIMA FASE ▶", width//2 - 120, height//2 + 70, w=240, h=48)
    btn_menu     = Button("MENU",           width//2 - 70,  height//2 + 132, w=140, h=44)

    particles = []
    tick = 0

    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:       return "menu"
            if btn_continue.is_clicked(event):  return "continue"
            if btn_menu.is_clicked(event):      return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  return "continue"
                if event.key == pygame.K_ESCAPE:  return "menu"

        # Overlay gradiente dourado
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(height):
            t = i / height
            c = _lerp_color((60, 30, 0), (10, 5, 0), t)
            pygame.draw.line(overlay, (*c, 200), (0,i), (width,i))
        screen.blit(overlay, (0,0))

        # Linhas de energia horizontais
        for i in range(6):
            ly = height//2 - 180 + i * 70
            la = int(30 + 20 * math.sin(tick * 0.05 + i))
            ls = pygame.Surface((width, 1), pygame.SRCALPHA)
            ls.fill((*GOLD, la))
            screen.blit(ls, (0, ly))

        # Partículas douradas
        if tick % 4 == 0:
            for _ in range(3):
                particles.append({
                    "x": random.uniform(0, width), "y": height + 5,
                    "vx": random.uniform(-1,1), "vy": random.uniform(-3,-1),
                    "life": random.randint(60,120), "max": 120,
                    "color": random.choice([GOLD, YELLOW, ORANGE]),
                    "r": random.uniform(2,5),
                })
        for p in particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["life"] -= 1
            if p["life"] > 0:
                a = int(200 * p["life"] / p["max"])
                r = max(1, int(p["r"] * p["life"] / p["max"]))
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["color"], a), (r,r), r)
                screen.blit(s, (int(p["x"])-r, int(p["y"])-r))
        particles = [p for p in particles if p["life"] > 0]

        # Título VITÓRIA!
        pulse = 1.0 + 0.035 * math.sin(tick * 0.1)
        for ofs, col in [((4,4),RED),((2,2),ORANGE),((0,0),YELLOW)]:
            ts = font_big.render("VITÓRIA!", True, col)
            tw = int(ts.get_width() * pulse)
            th = int(ts.get_height() * pulse)
            ts = pygame.transform.scale(ts, (tw, th))
            screen.blit(ts, ts.get_rect(center=(width//2+ofs[0], height//2-100+ofs[1])))

        # Separador
        lw = int(220 + 50 * math.sin(tick*0.06))
        pygame.draw.line(screen, GOLD,
                         (width//2-lw, height//2-30), (width//2+lw, height//2-30), 2)

        sub = font_mid.render(f"{winner_name}  —  Fase {phase} / {total_phases}", True, WHITE)
        screen.blit(sub, sub.get_rect(center=(width//2, height//2-5)))

        for btn in [btn_continue, btn_menu]:
            btn.update(mouse_pos)
            btn.draw(screen, font_small)

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════════════════════════
#  DERROTA
# ═════════════════════════════════════════════════════════════════════════════
def show_defeat(screen, clock, loser_name=""):
    width, height = screen.get_size()
    try:
        font_big   = pygame.font.SysFont("Impact", 80)
        font_mid   = pygame.font.SysFont("Impact", 34)
        font_small = pygame.font.SysFont("Impact", 24)
    except Exception:
        font_big   = pygame.font.Font(None, 80)
        font_mid   = pygame.font.Font(None, 34)
        font_small = pygame.font.Font(None, 24)

    btn_retry = Button("TENTAR NOVAMENTE", width//2 - 130, height//2 + 70,  w=260, h=48)
    btn_menu  = Button("MENU",             width//2 - 70,  height//2 + 132, w=140, h=44)

    particles = []
    tick = 0

    while True:
        tick += 1
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:      return "menu"
            if btn_retry.is_clicked(event):    return "retry"
            if btn_menu.is_clicked(event):     return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: return "retry"
                if event.key == pygame.K_ESCAPE: return "menu"

        # Overlay vermelho escuro
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(height):
            t = i / height
            c = _lerp_color((50, 0, 0), (10, 0, 0), t)
            pygame.draw.line(overlay, (*c, 210), (0,i), (width,i))
        screen.blit(overlay, (0,0))

        # Partículas vermelhas
        if tick % 5 == 0:
            for _ in range(2):
                particles.append({
                    "x": random.uniform(0, width), "y": height + 5,
                    "vx": random.uniform(-0.5,0.5), "vy": random.uniform(-1.5,-0.5),
                    "life": random.randint(80,150), "max": 150,
                    "color": random.choice([RED, RED_BRIGHT, (180,30,30)]),
                    "r": random.uniform(2,6),
                })
        for p in particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["life"] -= 1
            if p["life"] > 0:
                a = int(180 * p["life"] / p["max"])
                r = max(1, int(p["r"] * p["life"] / p["max"]))
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["color"], a), (r,r), r)
                screen.blit(s, (int(p["x"])-r, int(p["y"])-r))
        particles = [p for p in particles if p["life"] > 0]

        # Racha diagonal decorativa
        for i in range(5):
            crack_y = height//2 - 150 + i * 12
            pygame.draw.line(screen, (*RED, 40),
                             (width//2 - 300, crack_y), (width//2 + 300, crack_y + i*3), 1)

        # Título DERROTA!
        pulse = 1.0 + 0.03 * math.sin(tick * 0.1)
        for ofs, col in [((4,4),(80,0,0)),((2,2),RED_BRIGHT),((0,0),WHITE)]:
            ts = font_big.render("DERROTA!", True, col)
            tw = int(ts.get_width() * pulse)
            th = int(ts.get_height() * pulse)
            ts = pygame.transform.scale(ts, (tw, th))
            screen.blit(ts, ts.get_rect(center=(width//2+ofs[0], height//2-100+ofs[1])))

        lw = int(200 + 40 * math.sin(tick*0.05))
        pygame.draw.line(screen, RED_BRIGHT,
                         (width//2-lw, height//2-30), (width//2+lw, height//2-30), 2)

        sub = font_mid.render(f"{loser_name} foi derrotado...", True, GRAY_LIGHT)
        screen.blit(sub, sub.get_rect(center=(width//2, height//2-5)))

        for btn in [btn_retry, btn_menu]:
            btn.update(mouse_pos)
            btn.draw(screen, font_small)

        pygame.display.flip()
        clock.tick(60)