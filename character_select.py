"""
============================================================
  character_select.py
  Tela de Seleção de Personagem - Jogo de Luta 2D
  Estilo anime / Street Fighter
============================================================

  SPRITES NECESSÁRIOS (pasta assets/characters/):
    ryu.png / naruto.png / goku.png / ichigo.png / luffy.png
  Caso não existam, exibe silhueta colorida como placeholder.

  Retorna:
    run_selection()  →  índice do personagem escolhido (0–4)
                        ou None se o jogador sair (ESC)
"""

import pygame
import math
import os
import sys
import re

# ── Dimensões ────────────────────────────────────────────
SW, SH = 1000, 620
FPS    = 60

# ── Paleta ───────────────────────────────────────────────
C_BG1      = (5,   8,  20)   # fundo escuro superior
C_BG2      = (10, 15,  40)   # fundo escuro inferior
C_ACCENT   = (255, 60,  60)  # vermelho anime
C_ACCENT2  = (255, 180,  0)  # dourado
C_WHITE    = (255, 255, 255)
C_GRAY     = (100, 100, 120)
C_DARKGRAY = ( 30,  30,  50)
C_PANEL    = ( 12,  16,  36)
C_CARD_OFF = ( 18,  22,  45)
C_CARD_ON  = ( 28,  34,  70)
C_BORDER   = ( 50,  60, 120)
C_BORDER_SEL = (255, 60, 60)
C_HP_GREEN = ( 80, 220,  80)
C_SP_BLUE  = ( 60, 160, 255)
C_SHADOW   = (  0,   0,   0, 160)

# ── Dados dos personagens ─────────────────────────────────
from characters import CHARACTERS

# ── Tamanhos dos cards ────────────────────────────────────
CARD_W, CARD_H = 140, 180
CARD_GAP       = 20
PREVIEW_W      = 280   # largura do painel de preview
TOTAL_CARDS    = len(CHARACTERS)


# ─────────────────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────────────────

def load_or_placeholder(path, w, h, color):
    """Carrega sprite ou cria silhueta colorida como placeholder."""
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (w, h))
        except Exception:
            pass
    # Placeholder: silhueta genérica de lutador
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    c = color
    # Sombra
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 80), (w//4, h - 20, w//2, 14))
    surf.blit(shadow, (0, 0))
    # Corpo
    bx, by = w//2 - 22, h//2 - 10
    pygame.draw.rect(surf, c, (bx, by, 44, 55), border_radius=6)
    # Cabeça
    pygame.draw.circle(surf, c, (w//2, h//2 - 28), 22)
    # Pernas
    pygame.draw.rect(surf, tuple(max(0, x-40) for x in c),
                     (bx + 4, by + 55, 16, 35), border_radius=4)
    pygame.draw.rect(surf, tuple(max(0, x-40) for x in c),
                     (bx + 24, by + 55, 16, 35), border_radius=4)
    # Braços
    pygame.draw.rect(surf, c, (bx - 14, by + 4, 14, 38), border_radius=4)
    pygame.draw.rect(surf, c, (bx + 44, by + 4, 14, 38), border_radius=4)
    # Brilho
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*c, 30), (w//2, h//2 - 10), 55)
    surf.blit(glow, (0, 0))
    return surf

def draw_bar(surf, x, y, w, h, ratio, color_fill, color_bg=(30, 30, 50)):
    pygame.draw.rect(surf, color_bg, (x, y, w, h), border_radius=3)
    if ratio > 0:
        pygame.draw.rect(surf, color_fill,
                         (x, y, int(w * ratio), h), border_radius=3)
    pygame.draw.rect(surf, (80, 80, 100), (x, y, w, h), 1, border_radius=3)

def draw_text_shadow(surf, text, font, color, x, y, shadow_color=(0,0,0), offset=2):
    s = font.render(text, True, shadow_color)
    surf.blit(s, (x + offset, y + offset))
    t = font.render(text, True, color)
    surf.blit(t, (x, y))

def lerp(a, b, t):
    return a + (b - a) * t


# ─────────────────────────────────────────────────────────
#  CLASSE: TELA DE SELEÇÃO
# ─────────────────────────────────────────────────────────
class CharacterSelectScreen:

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        # Fontes
        self.f_title  = pygame.font.SysFont("arial",  46, bold=True)
        self.f_big    = pygame.font.SysFont("arial",  32, bold=True)
        self.f_name   = pygame.font.SysFont("arial",  26, bold=True)
        self.f_med    = pygame.font.SysFont("arial", 16, bold=True)
        self.f_sm     = pygame.font.SysFont("arial", 13)
        self.f_tiny   = pygame.font.SysFont("arial", 11)

        # Estado
        self.selected   = 0          # índice selecionado
        self.confirmed  = False
        self.result     = None       # retorno final

        # Animação
        self.frame      = 0
        self.preview_scale  = 1.0   # ESCALA do preview (anima ao selecionar)
        self.target_scale   = 1.0
        self.card_offsets   = [0.0] * TOTAL_CARDS   # offset Y dos cards
        self.particles      = []
        self.flash_timer    = 0      # flash de confirmação

        # Posicionamento dos cards
        total_w = TOTAL_CARDS * CARD_W + (TOTAL_CARDS - 1) * CARD_GAP
        self.cards_start_x = (SW - total_w) // 2
        self.cards_y       = SH - CARD_H - 55

        # Carregar sprites dos personagens
        self.sprites = []
        for ch in CHARACTERS:
            frames = []
            if "anim_folder" in ch:
                # Tenta puxar de introduction, se não houver puxa de stance.
                folder = os.path.join(ch["anim_folder"], "introduction")
                if not os.path.exists(folder) or not os.listdir(folder):
                    folder = os.path.join(ch["anim_folder"], "stance")
                
                if os.path.exists(folder):
                    valid_exts = ('.png', '.jpg', '.jpeg')
                    raw_files = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
                    files = sorted(raw_files, key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
                    for fname in files:
                        fpath = os.path.join(folder, fname)
                        try:
                            img = pygame.image.load(fpath).convert_alpha()
                            colorkey = ch.get("colorkey", None)
                            target_color = colorkey if colorkey else img.get_at((0, 0))
                            
                            pix = pygame.PixelArray(img)
                            try:
                                pix.replace(target_color, (0, 0, 0, 0))
                            except ValueError:
                                pass
                            del pix
                            frames.append(img)
                        except Exception:
                            continue
            
            if not frames:
                # Fallback antigo
                img = load_or_placeholder(ch.get("sprite", ""), 200, 260, ch["color"])
                frames.append(img)
                
            self.sprites.append(frames)

        # Pré-renderizar fundo
        self._build_bg()

    # ── Fundo ─────────────────────────────────────────────
    def _build_bg(self):
        self.bg = pygame.Surface((SW, SH))
        # Gradiente vertical
        for y in range(SH):
            t = y / SH
            r = int(lerp(C_BG1[0], C_BG2[0], t))
            g = int(lerp(C_BG1[1], C_BG2[1], t))
            b = int(lerp(C_BG1[2], C_BG2[2], t))
            pygame.draw.line(self.bg, (r, g, b), (0, y), (SW, y))
        # Linhas decorativas em diagonal
        for i in range(0, SW + SH, 80):
            pygame.draw.line(self.bg, (255, 255, 255, 8),
                             (i, 0), (i - SH, SH), 1)
        # Hexágonos de fundo (decoração)
        for hx in range(0, SW, 90):
            for hy in range(0, SH, 78):
                pts = []
                for k in range(6):
                    angle = math.radians(60 * k - 30)
                    pts.append((hx + 36 * math.cos(angle),
                                hy + 36 * math.sin(angle)))
                pygame.draw.polygon(self.bg, (15, 20, 45), pts, 1)

    # ── Partículas de energia ──────────────────────────────
    def _spawn_particles(self, x, y, color, n=12):
        import random
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 40),
                "max_life": 40,
                "color": color,
                "r": random.randint(3, 7),
            })

    def _update_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.9
            p["vy"] *= 0.9
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self):
        for p in self.particles:
            alpha = int(255 * p["life"] / p["max_life"])
            r = max(1, int(p["r"] * p["life"] / p["max_life"]))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha), (r, r), r)
            self.screen.blit(s, (int(p["x"])-r, int(p["y"])-r))

    # ── Desenho do card individual ─────────────────────────
    def _draw_card(self, idx, sel):
        ch   = CHARACTERS[idx]
        x    = self.cards_start_x + idx * (CARD_W + CARD_GAP)
        y    = self.cards_y + int(self.card_offsets[idx])

        # Sombra do card
        sh_s = pygame.Surface((CARD_W + 10, CARD_H + 10), pygame.SRCALPHA)
        pygame.draw.rect(sh_s, (0, 0, 0, 80), (5, 5, CARD_W, CARD_H), border_radius=10)
        self.screen.blit(sh_s, (x - 2, y + 4))

        # Fundo do card
        card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        bg_color  = C_CARD_ON if sel else C_CARD_OFF
        pygame.draw.rect(card_surf, bg_color, (0, 0, CARD_W, CARD_H), border_radius=10)

        # Gradiente interno (brilho superior)
        for row in range(CARD_H // 2):
            alpha = int(30 * (1 - row / (CARD_H // 2)))
            pygame.draw.rect(card_surf, (255, 255, 255, alpha),
                             (1, row + 1, CARD_W - 2, 1))
        self.screen.blit(card_surf, (x, y))

        # Borda colorida
        border_color = ch["color"] if sel else C_BORDER
        border_w     = 2 if not sel else 3
        pygame.draw.rect(self.screen, border_color,
                         (x, y, CARD_W, CARD_H), border_w, border_radius=10)

        # Se selecionado: borda dupla brilhante animada
        if sel:
            pulse = int(40 + 30 * math.sin(self.frame * 0.1))
            glow  = pygame.Surface((CARD_W + 12, CARD_H + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*ch["color"], pulse),
                             (0, 0, CARD_W + 12, CARD_H + 12), 4, border_radius=13)
            self.screen.blit(glow, (x - 6, y - 6))

        # Sprite do personagem no card (ESCALA e ANIMAÇÃO reduzida para caber no card)
        thumb_w, thumb_h = CARD_W - 16, CARD_H - 50
        
        frame_list = self.sprites[idx]
        current_img = frame_list[(self.frame // 10) % len(frame_list)]
        thumb = pygame.transform.scale(current_img, (thumb_w, thumb_h))
        
        self.screen.blit(thumb, (x + 8, y + 4))

        # Nome
        name_surf = self.f_tiny.render(ch["name"], True,
                                       ch["color"] if sel else C_GRAY)
        nx = x + CARD_W // 2 - name_surf.get_width() // 2
        self.screen.blit(name_surf, (nx, y + CARD_H - 40))

        # Linha separadora
        pygame.draw.line(self.screen, ch["color"] if sel else C_BORDER,
                         (x + 8, y + CARD_H - 44),
                         (x + CARD_W - 8, y + CARD_H - 44), 1)

        # Barras de HP/Speed mini
        draw_bar(self.screen, x + 8, y + CARD_H - 30,
                 CARD_W - 16, 5, ch["hp"] / 130, C_HP_GREEN)
        draw_bar(self.screen, x + 8, y + CARD_H - 18,
                 CARD_W - 16, 5, ch["speed"] / 10, C_SP_BLUE)

        labels = [
            self.f_tiny.render("HP",  True, C_GRAY),
            self.f_tiny.render("VEL", True, C_GRAY),
        ]
        self.screen.blit(labels[0], (x + 8,             y + CARD_H - 31))
        self.screen.blit(labels[1], (x + 8,             y + CARD_H - 19))

    # ── Painel de preview (personagem selecionado) ─────────
    def _draw_preview(self):
        ch    = CHARACTERS[self.selected]
        px    = 30
        py    = 90
        pw    = PREVIEW_W
        ph    = self.cards_y - py - 20

        # Fundo do painel
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*C_PANEL, 200), (0, 0, pw, ph), border_radius=12)
        pygame.draw.rect(panel, (*ch["color"], 60), (0, 0, pw, ph), border_radius=12)
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, ch["color"],
                         (px, py, pw, ph), 2, border_radius=12)

        # ── ESCALA + ROTAÇÃO do preview ──────────────────────
        # Puxa o quadro de animação da lista baseado no frame do loop do jogo
        frame_list = self.sprites[self.selected]
        current_img = frame_list[(self.frame // 10) % len(frame_list)]
        
        preview_h = int(ph * 0.78)
        preview_w = int(preview_h * 0.75)
        base_sprite = pygame.transform.scale(current_img, (preview_w, preview_h))

        # ESCALA: aplica escala animada (pulsa quando muda de personagem)
        sc = self.preview_scale
        if sc != 1.0:
            sw2 = int(preview_w * sc)
            sh2 = int(preview_h * sc)
            base_sprite = pygame.transform.scale(base_sprite, (sw2, sh2))

        # Aura de energia atrás do sprite
        aura_r = int(preview_w * 0.6 + 15 * math.sin(self.frame * 0.07))
        aura   = pygame.Surface((aura_r*2, aura_r*2), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*ch["color"], 30), (aura_r, aura_r), aura_r)
        
        # Mover o centro do personagem para a direita (fora da caixa de informações)
        sprite_cx = px + pw + 250
        
        self.screen.blit(aura, (sprite_cx - aura_r,
                                py + ph//2 - aura_r - 20))

        cx_sprite = sprite_cx - base_sprite.get_width()//2
        cy_sprite = py + ph - base_sprite.get_height() - 10
        self.screen.blit(base_sprite, (cx_sprite, cy_sprite))

        # ── Informações textuais ──────────────────────────────
        tx = px + 12
        # Nome grande
        draw_text_shadow(self.screen, ch["name"], self.f_name,
                         ch["color"], tx, py + 12)
        # Título
        title_s = self.f_sm.render(ch["title"], True, C_WHITE)
        self.screen.blit(title_s, (tx, py + 42))

        # Linha
        pygame.draw.line(self.screen, ch["color"],
                         (tx, py + 60), (px + pw - 12, py + 60), 1)

        # Estilo
        style_s = self.f_tiny.render(f"ESTILO: {ch['style']}", True, C_ACCENT2)
        self.screen.blit(style_s, (tx, py + 66))

        # Barras de stats
        stats = [
            ("HP",        ch["hp"] / 130,     C_HP_GREEN),
            ("VELOCIDADE", ch["speed"] / 10,  C_SP_BLUE),
        ]
        for i, (lbl, ratio, color) in enumerate(stats):
            sy = py + 84 + i * 22
            lbl_s = self.f_tiny.render(lbl, True, C_GRAY)
            self.screen.blit(lbl_s, (tx, sy))
            draw_bar(self.screen, tx + 70, sy + 2, pw - 90, 10, ratio, color)

        # Golpes
        moves_y = py + 134
        pygame.draw.line(self.screen, C_BORDER,
                         (tx, moves_y - 4), (px + pw - 12, moves_y - 4), 1)
        for i, (label, key, move) in enumerate([
            ("[J] LEVE",    "J", ch["light"]["name"]),
            ("[K] MÉDIO",   "K", ch["medium"]["name"]),
            ("[L] ESPECIAL","L", ch["special"]["name"]),
        ]):
            my = moves_y + i * 26
            key_color = C_ACCENT if i == 2 else C_ACCENT2
            k_s = self.f_tiny.render(label,  True, key_color)
            m_s = self.f_tiny.render(move,   True, C_WHITE)
            self.screen.blit(k_s, (tx,      my))
            self.screen.blit(m_s, (tx + 90, my))

        # Descrição
        desc_y = moves_y + 82
        pygame.draw.line(self.screen, C_BORDER,
                         (tx, desc_y - 6), (px + pw - 12, desc_y - 6), 1)
        words = ch["desc"].split()
        line, lines_out = "", []
        for w in words:
            test = line + (" " if line else "") + w
            if self.f_tiny.size(test)[0] > pw - 24:
                lines_out.append(line); line = w
            else:
                line = test
        if line: lines_out.append(line)
        for i, l in enumerate(lines_out[:3]):
            self.screen.blit(self.f_tiny.render(l, True, C_WHITE),
                             (tx, desc_y + i * 15))

    # ── Projétil giratório decorativo (ROTAÇÃO) ────────────
    def _draw_rotating_orb(self):
        """
        ROTAÇÃO: projétil de energia gira continuamente no topo da tela
        como elemento decorativo, demonstrando a transformação geométrica.
        """
        ch    = CHARACTERS[self.selected]
        orb_x = SW // 2
        orb_y = 50
        angle = self.frame * 4   # ângulo cresce a cada frame

        # Corpo do orbe
        orb_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pts = [
            (15, 2), (20, 10), (28, 10),
            (22, 17), (25, 26),
            (15, 21), (5, 26),
            (8, 17), (2, 10), (10, 10),
        ]  # estrela de 5 pontas
        pygame.draw.polygon(orb_surf, ch["color"], pts)
        pygame.draw.polygon(orb_surf, C_WHITE, pts, 1)

        # ROTAÇÃO: pygame.transform.rotate gira o orbe pelo ângulo acumulado
        rotated = pygame.transform.rotate(orb_surf, angle)
        rect    = rotated.get_rect(center=(orb_x, orb_y))
        self.screen.blit(rotated, rect)

        # Satélites orbitando (também giram)
        for i in range(3):
            orbit_angle = math.radians(angle + i * 120)
            sx = int(orb_x + 32 * math.cos(orbit_angle))
            sy = int(orb_y + 18 * math.sin(orbit_angle))
            mini = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(mini, (*ch["color"], 180), (6, 6), 5)
            # ROTAÇÃO: mini orbe também rotaciona
            mini_rot = pygame.transform.rotate(mini, -angle * 2)
            self.screen.blit(mini_rot, (sx - 6, sy - 6))

    # ── Cabeçalho ──────────────────────────────────────────
    def _draw_header(self):
        # Faixa de título
        hbar = pygame.Surface((SW, 72), pygame.SRCALPHA)
        pygame.draw.rect(hbar, (0, 0, 0, 140), (0, 0, SW, 72))
        pygame.draw.line(hbar, C_ACCENT, (0, 71), (SW, 71), 2)
        self.screen.blit(hbar, (0, 0))

        # Renderiza o título estático (sem animação de escala)
        title_base = self.f_title.render("ESCOLHA SEU LUTADOR", True, C_WHITE)
        tw = title_base.get_width()
        th = title_base.get_height()
        self.screen.blit(title_base, (SW//2 - tw//2, 36 - th//2))

        # Linha decorativa vermelha abaixo do título
        lw = int(200 + 60 * math.sin(self.frame * 0.05))
        pygame.draw.line(self.screen, C_ACCENT,
                         (SW//2 - lw//2, 68), (SW//2 + lw//2, 68), 2)

    # ── Rodapé com controles ────────────────────────────────
    def _draw_footer(self):
        fy = SH - 30
        fbar = pygame.Surface((SW, 30), pygame.SRCALPHA)
        pygame.draw.rect(fbar, (0, 0, 0, 140), (0, 0, SW, 30))
        pygame.draw.line(fbar, C_BORDER, (0, 0), (SW, 0), 1)
        self.screen.blit(fbar, (0, fy))

        controls = [
            ("← →",    "Navegar"),
            ("ENTER",  "Confirmar"),
            ("ESC",    "Voltar"),
        ]
        total_w = sum(self.f_tiny.size(f"{k}  {v}    ")[0] for k, v in controls)
        cx = (SW - total_w) // 2
        for key, desc in controls:
            k_s = self.f_tiny.render(key,  True, C_ACCENT2)
            d_s = self.f_tiny.render(f"  {desc}    ", True, C_GRAY)
            self.screen.blit(k_s, (cx, fy + 8))
            cx += k_s.get_width()
            self.screen.blit(d_s, (cx, fy + 8))
            cx += d_s.get_width()

    # ── Confirmação (flash) ─────────────────────────────────
    def _draw_confirm_flash(self):
        if self.flash_timer <= 0:
            return
        alpha = int(200 * self.flash_timer / 20)
        flash = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ch    = CHARACTERS[self.selected]
        flash.fill((*ch["color"], alpha))
        self.screen.blit(flash, (0, 0))

        if self.flash_timer > 10:
            txt = self.f_big.render(f"{CHARACTERS[self.selected]['name']}  SELECIONADO!", True, C_WHITE)
            self.screen.blit(txt, (SW//2 - txt.get_width()//2, SH//2 - 20))

        self.flash_timer -= 1
        if self.flash_timer == 0:
            self.result = self.selected

    # ── Evento de troca de personagem ─────────────────────
    def _on_change(self):
        ch = CHARACTERS[self.selected]
        # Dispara partículas na posição do card selecionado
        cx = self.cards_start_x + self.selected * (CARD_W + CARD_GAP) + CARD_W // 2
        cy = self.cards_y + CARD_H // 2
        self._spawn_particles(cx, cy, ch["color"], n=16)
        # Trigger de escala do preview
        self.target_scale = 1.08

    # ── Loop principal da tela ─────────────────────────────
    def run(self):
        import random
        while True:
            self.clock.tick(FPS)

            # ── Eventos ───────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN and self.flash_timer == 0:
                    if event.key == pygame.K_ESCAPE:
                        return None

                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        # TRANSLAÇÃO: cursor navega para esquerda
                        self.selected = (self.selected - 1) % TOTAL_CARDS
                        self._on_change()

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        # TRANSLAÇÃO: cursor navega para direita
                        self.selected = (self.selected + 1) % TOTAL_CARDS
                        self._on_change()

                    elif event.key == pygame.K_RETURN:
                        self.flash_timer = 20
                        ch = CHARACTERS[self.selected]
                        cx = SW // 2
                        cy = SH // 2
                        self._spawn_particles(cx, cy, ch["color"], n=40)

            # ── Atualizar animações ───────────────────────
            self.frame += 1

            # Suavizar escala do preview (ESCALA animada)
            self.preview_scale = lerp(self.preview_scale, self.target_scale, 0.15)
            if abs(self.preview_scale - self.target_scale) < 0.005:
                self.target_scale = 1.0

            # Bobbing dos cards (offset Y animado)
            for i in range(TOTAL_CARDS):
                if i == self.selected:
                    # Card selecionado sobe levemente (TRANSLAÇÃO vertical)
                    target_off = -12.0 + 4 * math.sin(self.frame * 0.08)
                else:
                    target_off = 0.0
                self.card_offsets[i] = lerp(self.card_offsets[i], target_off, 0.12)

            self._update_particles()

            # REFLEXÃO: se personagem está "virado" para esquerda,
            # espelhar seu sprite no preview (demonstração da transformação)
            # (aqui sempre virado para direita por padrão no menu)

            # ── Renderizar ────────────────────────────────
            self.screen.blit(self.bg, (0, 0))

            self._draw_header()
            self._draw_preview()        # ESCALA + sprite
            self._draw_particles()

            # Desenhar cards
            for i in range(TOTAL_CARDS):
                self._draw_card(i, i == self.selected)

            self._draw_footer()
            self._draw_confirm_flash()

            pygame.display.flip()

            # Retornar resultado quando flash terminar
            if self.result is not None:
                return self.result


# ─────────────────────────────────────────────────────────
#  FUNÇÃO PÚBLICA
# ─────────────────────────────────────────────────────────

def run_selection(screen=None, clock=None):
    """
    Executa a tela de seleção de personagem.
    Retorna o índice (0–4) do personagem escolhido,
    ou None se o jogador pressionar ESC.
    """
    standalone = screen is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Seleção de Personagem")
        clock  = pygame.time.Clock()

    result = CharacterSelectScreen(screen, clock).run()

    if standalone:
        if result is not None:
            print(f"Personagem escolhido: {CHARACTERS[result]['name']} (índice {result})")
        pygame.quit()

    return result


# ─────────────────────────────────────────────────────────
#  ENTRY POINT (teste standalone)
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_selection()