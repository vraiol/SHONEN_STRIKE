import pygame
import sys
import math
import os

pygame.init()

# ── Configurações da janela ──────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SHONEN STRIKE")
clock = pygame.time.Clock()

# ── Paleta de cores ──────────────────────────────────────────────────────────
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
BG_TOP      = (10, 0, 30)        # roxo escuro
BG_BOT      = (30, 0, 10)        # vermelho escuro
ORANGE      = (255, 120, 0)
ORANGE_DIM  = (180, 70, 0)
YELLOW      = (255, 220, 50)
RED         = (220, 30, 30)
GRAY_DARK   = (30, 30, 40)
GRAY_LIGHT  = (180, 180, 200)
CYAN        = (0, 220, 255)

# ── Fontes ───────────────────────────────────────────────────────────────────
try:
    font_title  = pygame.font.SysFont("Impact", 70)
    font_sub    = pygame.font.SysFont("Impact", 22)
    font_btn    = pygame.font.SysFont("Impact", 28)
    font_ctrl   = pygame.font.SysFont("Impact", 32)
    font_small  = pygame.font.SysFont("Arial", 18)
except Exception:
    font_title  = pygame.font.Font(None, 60)
    font_sub    = pygame.font.Font(None, 22)
    font_btn    = pygame.font.Font(None, 42)
    font_ctrl   = pygame.font.Font(None, 32)
    font_small  = pygame.font.Font(None, 18)

# ── Imagem de fundo ──────────────────────────────────────────────────────────
# 👉 Coloque o caminho da sua imagem aqui:
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_IMAGE_PATH = os.path.join(_BASE_DIR, "imagens", "menu.png")

try:
    bg_image = pygame.image.load(BG_IMAGE_PATH).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    USE_BG_IMAGE = True
except Exception as e:
    bg_image = None
    USE_BG_IMAGE = False
    print(f"[AVISO] Imagem de fundo não encontrada: '{BG_IMAGE_PATH}'")
    print(f"        Erro: {e}")

# ── Estado do menu ───────────────────────────────────────────────────────────
STATE_MAIN     = "main"
STATE_CONTROLS = "controls"
current_state  = STATE_MAIN

# ── Partículas decorativas ────────────────────────────────────────────────────
import random

class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x  = random.randint(0, WIDTH)
        self.y  = random.randint(0, HEIGHT)
        self.r  = random.uniform(1, 3)
        self.vy = random.uniform(-0.4, -1.2)
        self.vx = random.uniform(-0.3, 0.3)
        self.alpha = random.randint(80, 200)
        self.color = random.choice([ORANGE, YELLOW, RED, CYAN])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 0.6
        if self.y < -10 or self.alpha <= 0:
            self.reset()
            self.y = HEIGHT + 5

    def draw(self, surf):
        if self.alpha <= 0:
            return
        s = pygame.Surface((int(self.r * 2 + 1), int(self.r * 2 + 1)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.alpha)), (int(self.r), int(self.r)), int(self.r))
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))

particles = [Particle() for _ in range(80)]

# ── Botões ────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, text, x, y, action):
        self.text   = text
        self.y      = y
        self.action = action
        self.w      = 160
        self.h      = 34
        self.x      = x
        self.hovered = False
        self.scale   = 1.0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, mouse_pos):
        self.hovered = self.rect().collidepoint(mouse_pos)
        target = 1.07 if self.hovered else 1.0
        self.scale += (target - self.scale) * 0.15

    def draw(self, surf):
        # tamanho com escala
        sw = int(self.w * self.scale)
        sh = int(self.h * self.scale)
        sx = self.x - int((sw - self.w) / 2)  # cresce para a direita
        sy = self.y + (self.h - sh) // 2

        btn_rect = pygame.Rect(sx, sy, sw, sh)

        # sombra semitransparente
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(topleft=(0, 0)), border_radius=8)
        surf.blit(shadow_surf, (sx + 3, sy + 3))

        # fundo do botão transparente
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
        color = YELLOW if self.hovered else WHITE
        text_surf = font_btn.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=btn_rect.center)
        surf.blit(text_surf, text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect().collidepoint(event.pos):
                self.action()

# ── Ações dos botões ──────────────────────────────────────────────────────────
def action_play():
    print("[JOGAR] – conecte a lógica do jogo aqui!")
    # TODO: carregar cena do jogo
    # ex: import game; game.run()

def action_controls():
    global current_state
    current_state = STATE_CONTROLS

def action_quit():
    pygame.quit()
    sys.exit()

_BX  = 20          # margem esquerda
_GAP = 50          # espaço entre botões
_BY  = HEIGHT - 50 # ponto base (botão mais baixo)

buttons = [
    Button("SAIR",      _BX, _BY,              action_quit),
    Button("CONTROLES", _BX, _BY - _GAP,       action_controls),
    Button("JOGAR",      _BX, _BY - _GAP * 2,   action_play),
]

# ── Conteúdo da tela de Controles ────────────────────────────────────────────
controls_info = [
    ("MOVIMENTAÇÃO",  "W / A / S / D  ou  ← ↑ ↓ →"),
    ("ATACAR",        "J  ou  Botão X"),
    ("DESVIAR",       "K  ou  Botão O"),
    ("ESPECIAL",      "U  ou  Botão □"),
    ("PAUSAR",        "ESC  ou  Enter"),
]

# ── Gradiente de fundo ────────────────────────────────────────────────────────
def draw_background(surf):
    if USE_BG_IMAGE and bg_image:
        surf.blit(bg_image, (0, 0))
    else:
        # Fallback: gradiente original
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

# ── Linhas decorativas laterais ───────────────────────────────────────────────
def draw_decorations(surf, tick):
    # linhas verticais pulsando
    for i, xpos in enumerate([60, WIDTH - 60]):
        alpha = int(120 + 80 * math.sin(tick * 0.05 + i * math.pi))
        s = pygame.Surface((3, HEIGHT), pygame.SRCALPHA)
        s.fill((*ORANGE, alpha))
        surf.blit(s, (xpos, 0))

    # linha horizontal sob o título
    bar_y = 185
    pygame.draw.rect(surf, ORANGE, (80, bar_y, WIDTH - 160, 3), border_radius=2)

# ── Título ────────────────────────────────────────────────────────────────────
def draw_title(surf, tick):
    # sombra colorida
    for offset, color in [((4, 4), RED), ((2, 2), ORANGE)]:
        shadow = font_title.render("SHONEN STRIKE", True, color)
        sr = shadow.get_rect(center=(WIDTH // 2 + offset[0], 50 + offset[1]))
        surf.blit(shadow, sr)

    # texto principal fixo
    title_surf = font_title.render("SHONEN STRIKE", True, YELLOW)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 50))
    surf.blit(title_surf, title_rect)

    
# ── Tela de Controles ─────────────────────────────────────────────────────────
def draw_controls_screen(surf, tick, mouse_pos):
    draw_background(surf)

    # painel semitransparente centralizado
    panel_w, panel_h = 600, 420
    panel_x = WIDTH  // 2 - panel_w // 2
    panel_y = HEIGHT // 2 - panel_h // 2
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 160), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (*ORANGE_DIM, 180), panel.get_rect(), width=2, border_radius=16)
    surf.blit(panel, (panel_x, panel_y))

    # titulo
    t = font_ctrl.render("CONTROLES", True, YELLOW)
    surf.blit(t, t.get_rect(center=(WIDTH // 2, panel_y + 28)))

    # linha separadora sutil
    sep_y = panel_y + 54
    sep = pygame.Surface((panel_w - 60, 1), pygame.SRCALPHA)
    sep.fill((255, 255, 255, 60))
    surf.blit(sep, (panel_x + 30, sep_y))

    # tabela com duas colunas: ACAO | TECLAS
    row_h   = 58
    start_y = sep_y + 16
    col_action = panel_x + 40
    col_keys   = panel_x + panel_w // 2 + 10

    for i, (action, keys) in enumerate(controls_info):
        row_y = start_y + i * row_h

        # fundo alternado
        if i % 2 == 0:
            row_bg = pygame.Surface((panel_w - 20, row_h - 6), pygame.SRCALPHA)
            pygame.draw.rect(row_bg, (255, 255, 255, 18), row_bg.get_rect(), border_radius=6)
            surf.blit(row_bg, (panel_x + 10, row_y))

        # acao (coluna esquerda)
        a_surf = font_ctrl.render(action, True, ORANGE)
        surf.blit(a_surf, a_surf.get_rect(midleft=(col_action, row_y + row_h // 2)))

        # teclas (coluna direita)
        k_surf = font_ctrl.render(keys, True, WHITE)
        surf.blit(k_surf, k_surf.get_rect(midleft=(col_keys, row_y + row_h // 2)))

    # botao voltar transparente
    back_rect = pygame.Rect(WIDTH // 2 - 90, panel_y + panel_h - 52, 180, 38)
    hov = back_rect.collidepoint(mouse_pos)
    back_surf = pygame.Surface((180, 38), pygame.SRCALPHA)
    pygame.draw.rect(back_surf, (255, 140, 0, 120) if hov else (0, 0, 0, 80), back_surf.get_rect(), border_radius=8)
    surf.blit(back_surf, back_rect.topleft)
    pygame.draw.rect(surf, YELLOW if hov else ORANGE_DIM, back_rect, width=2, border_radius=8)
    back_txt = font_ctrl.render("← VOLTAR", True, YELLOW if hov else GRAY_LIGHT)
    surf.blit(back_txt, back_txt.get_rect(center=back_rect.center))
    return back_rect

# ── Loop principal ────────────────────────────────────────────────────────────
tick = 0
running = True

while running:
    tick += 1
    mouse_pos = pygame.mouse.get_pos()
    back_rect = None

    # ── Eventos ──────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_state == STATE_MAIN:
            for btn in buttons:
                btn.check_click(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        elif current_state == STATE_CONTROLS:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect and back_rect.collidepoint(event.pos):
                    current_state = STATE_MAIN
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                current_state = STATE_MAIN

    # ── Render ────────────────────────────────────────────────────────────────
    if current_state == STATE_MAIN:
        draw_background(screen)


        draw_title(screen, tick)

        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw(screen)

        # rodapé
        footer = font_small.render("© 2025 Shonen Strike  –  v0.1", True, (80, 80, 100))
        screen.blit(footer, footer.get_rect(bottomright=(WIDTH - 20, HEIGHT - 10)))

    elif current_state == STATE_CONTROLS:
        back_rect = draw_controls_screen(screen, tick, mouse_pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()