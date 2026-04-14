"""
============================================================
  character_select.py  –  Tela de Seleção de Personagem
  Estilo anime premium — Shonen Strike
============================================================
"""

import pygame
import math
import os
import sys
import re
import random

# ── Dimensões ────────────────────────────────────────────
SW, SH = 1000, 620
FPS    = 60

# ── Paleta ───────────────────────────────────────────────
C_BG1      = (4,  6, 14)
C_BG2      = (14, 18, 30)
C_ACCENT   = (255, 55,  55)
C_ACCENT2  = (255, 185,  0)
C_WHITE    = (255, 255, 255)
C_GRAY     = (120, 120, 135)
C_PANEL    = (18, 22, 38)
C_CARD_OFF = (18, 22, 35)
C_CARD_ON  = (30, 38, 62)
C_BORDER   = (38, 46, 72)
C_GOLD     = (255, 200, 40)
C_HP_GREEN = ( 70, 220,  80)
C_SP_BLUE  = ( 60, 165, 255)
C_SHADOW   = (  0,   0,   0, 160)

from characters import CHARACTERS

CARD_W, CARD_H = 118, 148
CARD_GAP       = 12
PREVIEW_W      = 290
TOTAL_CARDS    = len(CHARACTERS)


# ─────────────────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────────────────
def _lerp(a, b, t):
    return a + (b - a) * t

def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def load_or_placeholder(path, w, h, color):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (w, h))
        except Exception:
            pass
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    c = color
    pygame.draw.ellipse(surf, (0,0,0,80), (w//4, h-20, w//2, 14))
    bx, by = w//2 - 22, h//2 - 10
    pygame.draw.rect(surf, c, (bx, by, 44, 55), border_radius=6)
    pygame.draw.circle(surf, c, (w//2, h//2 - 28), 22)
    pygame.draw.rect(surf, tuple(max(0,x-40) for x in c), (bx+4,  by+55, 16, 35), border_radius=4)
    pygame.draw.rect(surf, tuple(max(0,x-40) for x in c), (bx+24, by+55, 16, 35), border_radius=4)
    pygame.draw.rect(surf, c, (bx-14, by+4, 14, 38), border_radius=4)
    pygame.draw.rect(surf, c, (bx+44, by+4, 14, 38), border_radius=4)
    return surf

def draw_bar(surf, x, y, w, h, ratio, color_fill, color_bg=(20, 20, 40)):
    # Fundo
    pygame.draw.rect(surf, color_bg, (x, y, w, h), border_radius=4)
    if ratio > 0:
        fw = int(w * ratio)
        # Gradiente na barra
        bar_s = pygame.Surface((fw, h), pygame.SRCALPHA)
        for i in range(h):
            t = i / max(1, h-1)
            top = _lerp_color(color_fill, C_WHITE, 0.4)
            bot = color_fill
            pygame.draw.line(bar_s, _lerp_color(top, bot, t), (0,i), (fw,i))
        surf.blit(bar_s, (x, y))
    # Borda
    pygame.draw.rect(surf, (60,60,90), (x, y, w, h), 1, border_radius=4)

def draw_text_shadow(surf, text, font, color, x, y, shadow_color=(0,0,0), offset=2):
    s = font.render(text, True, shadow_color)
    surf.blit(s, (x+offset, y+offset))
    t = font.render(text, True, color)
    surf.blit(t, (x, y))


# ─────────────────────────────────────────────────────────
#  TELA DE SELEÇÃO
# ─────────────────────────────────────────────────────────
class CharacterSelectScreen:

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        # Fontes
        self.f_title  = pygame.font.SysFont("Arial", 44, bold=True)
        self.f_big    = pygame.font.SysFont("Arial", 34, bold=True)
        self.f_name   = pygame.font.SysFont("Arial", 24, bold=True)
        self.f_med    = pygame.font.SysFont("Arial", 17, bold=True)
        self.f_sm     = pygame.font.SysFont("Arial", 14)
        self.f_tiny   = pygame.font.SysFont("Arial", 12)

        # Estado
        self.selected  = 0
        self.confirmed = False
        self.result    = None

        # Animação
        self.frame         = 0
        self.preview_scale = 1.0
        self.target_scale  = 1.0
        self.card_offsets  = [0.0] * TOTAL_CARDS
        self.particles     = []
        self.bg_particles  = []
        self.flash_timer   = 0
        self.aura_pulse    = 0.0

        # Posicionamento dos cards
        total_w = TOTAL_CARDS * CARD_W + (TOTAL_CARDS - 1) * CARD_GAP
        self.cards_start_x = (SW - total_w) // 2
        self.cards_y       = SH - CARD_H - 52

        # Carregar sprites
        self.sprites = []
        for ch in CHARACTERS:
            frames = []
            if "anim_folder" in ch:
                for sub in ("introduction", "stance"):
                    folder = os.path.join(ch["anim_folder"], sub)
                    if os.path.exists(folder) and os.listdir(folder):
                        break
                if os.path.exists(folder):
                    valid_exts = ('.png', '.jpg', '.jpeg')
                    raw = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
                    files = sorted(raw, key=lambda s: [int(t) if t.isdigit() else t.lower()
                                                        for t in re.split(r'(\d+)', s)])
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
                img = load_or_placeholder(ch.get("sprite",""), 200, 260, ch["color"])
                frames.append(img)
            self.sprites.append(frames)

       

        self._build_bg()

    # ── Fundo ─────────────────────────────────────────────
    def _build_bg(self):
        self.bg = pygame.Surface((SW, SH))
        for y in range(SH):
            t = y / SH
            c = _lerp_color(C_BG1, C_BG2, t)
            pygame.draw.line(self.bg, c, (0, y), (SW, y))

        # Linhas diagonais sutis
        for i in range(0, SW + SH, 55):
            x1 = i; y1 = 0
            x2 = i - SH; y2 = SH
            ls = pygame.Surface((SW, SH), pygame.SRCALPHA)
            pygame.draw.line(ls, (255, 140, 0, 12), (x1,y1), (x2,y2), 1)
            self.bg.blit(ls, (0,0))

        # Grade de pontos
        for gx in range(0, SW, 46):
            for gy in range(0, SH, 46):
                pygame.draw.circle(self.bg, (30, 36, 58), (gx, gy), 1)

    def _make_bg_particle(self):
        return {
            "x": random.uniform(0, SW),
            "y": random.uniform(0, SH),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.8, -0.2),
            "life": random.randint(80, 200),
            "max": 200,
            "color": random.choice([(255,160,0),(255,220,50),(255,80,0),(200,100,0)]),
            "r": random.uniform(1.0, 3.0),
        }

    def _update_bg_particles(self):
        for p in self.bg_particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["life"] -= 1
            if p["life"] <= 0 or p["y"] < -5:
                p.update(self._make_bg_particle())
                p["y"] = SH + 5

    def _draw_bg_particles(self):
        for p in self.bg_particles:
            alpha = int(150 * p["life"] / p["max"])
            r     = max(1, int(p["r"] * p["life"] / p["max"]))
            s     = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha//2), (r+1,r+1), r+1)
            pygame.draw.circle(s, (*p["color"], alpha),    (r+1,r+1), max(1,r-1))
            self.screen.blit(s, (int(p["x"])-r-1, int(p["y"])-r-1))

    # ── Partículas de seleção ──────────────────────────────
    def _spawn_particles(self, x, y, color, n=14):
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2.5, 7.0)
            self.particles.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(angle)*speed, "vy": math.sin(angle)*speed,
                "life": random.randint(22, 45), "max_life": 45,
                "color": color, "r": random.randint(3, 8),
            })

    def _update_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            p["vx"] *= 0.88;   p["vy"] *= 0.88
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self):
        for p in self.particles:
            alpha = int(255 * p["life"] / p["max_life"])
            r     = max(1, int(p["r"] * p["life"] / p["max_life"]))
            s     = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha//3), (r+1,r+1), r+1)
            pygame.draw.circle(s, (*p["color"], alpha),    (r+1,r+1), max(1,r-1))
            self.screen.blit(s, (int(p["x"])-r-1, int(p["y"])-r-1))

    # ── Card ──────────────────────────────────────────────
    def _draw_card(self, idx, sel):
        ch = CHARACTERS[idx]
        x  = self.cards_start_x + idx * (CARD_W + CARD_GAP)
        y  = self.cards_y + int(self.card_offsets[idx])

        # Sombra do card
        shad = pygame.Surface((CARD_W+6, CARD_H+6), pygame.SRCALPHA)
        pygame.draw.rect(shad, (0,0,0,100), shad.get_rect(), border_radius=12)
        self.screen.blit(shad, (x-2, y+4))

        # Fundo com gradiente
        card_s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        if sel:
            top_c = (40, 50, 80)
            bot_c = (22, 28, 50)
        else:
            top_c = (22, 26, 42)
            bot_c = (15, 18, 32)
        for i in range(CARD_H):
            t = i / CARD_H
            c = _lerp_color(top_c, bot_c, t)
            pygame.draw.line(card_s, (*c, 240), (0,i), (CARD_W,i))
        # rounded mask
        msk = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(msk, (255,255,255,255), msk.get_rect(), border_radius=10)
        card_s.blit(msk, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(card_s, (x, y))


        # Borda
        border_color = ch["color"] if sel else C_BORDER
        border_w     = 2 if sel else 1
        pygame.draw.rect(self.screen, border_color, (x, y, CARD_W, CARD_H), border_w, border_radius=10)
        if sel:
            # linha interior
            pygame.draw.rect(self.screen, (*ch["color"], 100),
                             (x+3, y+3, CARD_W-6, CARD_H-6), 1, border_radius=8)

        # Sprite no card
        thumb_h = int(CARD_H * 0.62)
        thumb_w = int(thumb_h * 0.75)
        frame_list  = self.sprites[idx]
        current_img = frame_list[(self.frame // 10) % len(frame_list)]

        scale_factor = ch.get("sprite_scale", 1.5)
        actual_h = int(thumb_h * scale_factor * 0.7)
        actual_w = int(thumb_w * scale_factor * 0.7)
        thumb = pygame.transform.scale(current_img, (actual_w, actual_h))

        cx = x + CARD_W//2 - actual_w//2
        cy = y + CARD_H - actual_h - 28
        self.screen.blit(thumb, (cx, cy))

        # Nome do card
        name_str = ch["name"]
        if len(name_str) > 12:
            name_str = name_str[:11] + "…"
        name_surf = self.f_tiny.render(name_str, True, C_GOLD if sel else C_GRAY)
        nx = x + CARD_W//2 - name_surf.get_width()//2
        self.screen.blit(name_surf, (nx, y + CARD_H - 22))

        # Indicador selecionado
        if sel:
            tri_pts = [(x + CARD_W//2 - 5, y + CARD_H - 8),
                       (x + CARD_W//2 + 5, y + CARD_H - 8),
                       (x + CARD_W//2,     y + CARD_H - 1)]
            pygame.draw.polygon(self.screen, C_GOLD, tri_pts)

    # ── Preview ────────────────────────────────────────────
    def _draw_preview(self):
        ch = CHARACTERS[self.selected]
        px = 22
        py = 78
        pw = PREVIEW_W
        ph = self.cards_y - py - 18

        # Sombra do painel
        shad = pygame.Surface((pw+8, ph+8), pygame.SRCALPHA)
        shad.fill((0,0,0,80))
        self.screen.blit(shad, (px-2, py+4))

        # Fundo com gradiente vertical
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for i in range(ph):
            t = i / ph
            c = _lerp_color((28, 18, 48), (12, 8, 24), t)
            pygame.draw.line(panel, (*c, 235), (0,i), (pw,i))
        msk = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(msk, (255,255,255,255), msk.get_rect(), border_radius=12)
        panel.blit(msk, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(panel, (px, py))

        # Borda dupla colorida
        pygame.draw.rect(self.screen, ch["color"], (px, py, pw, ph), 2, border_radius=12)
        pygame.draw.rect(self.screen, (*ch["color"], 60),
                         (px+4, py+4, pw-8, ph-8), 1, border_radius=9)

        # Cabeçalho colorido do painel
        head_h = 38
        head_s = pygame.Surface((pw, head_h), pygame.SRCALPHA)
        for i in range(head_h):
            t = i / head_h
            c = _lerp_color(ch["color"], tuple(x//3 for x in ch["color"]), t)
            pygame.draw.line(head_s, (*c, 200), (0,i), (pw,i))
        head_msk = pygame.Surface((pw, head_h), pygame.SRCALPHA)
        pygame.draw.rect(head_msk, (255,255,255,255),
                         (0, 0, pw, head_h), border_radius=12)
        head_s.blit(head_msk, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(head_s, (px, py))

        # Nome grande
        tx = px + 10
        draw_text_shadow(self.screen, ch["name"], self.f_name, C_WHITE, tx, py + 8, (0,0,0))

        pygame.draw.line(self.screen, (*ch["color"], 180),
                         (px+6, py+head_h), (px+pw-6, py+head_h), 1)

        # Título / subtítulo
        ty_off = py + head_h + 8
        title_s  = self.f_sm.render(ch.get("title",""), True, C_GOLD)
        style_s  = self.f_tiny.render(f"ESTILO: {ch.get('style','')}", True, C_ACCENT2)
        self.screen.blit(title_s, (tx, ty_off))
        self.screen.blit(style_s, (tx, ty_off + 20))

        # Stats
        pygame.draw.line(self.screen, C_BORDER, (tx, ty_off+38), (px+pw-10, ty_off+38), 1)
        stats = [
            ("HP",         ch["hp"] / 150,    C_HP_GREEN),
            ("VELOCIDADE", ch["speed"] / 10,  C_SP_BLUE),
            ("DANO ESP.", ch["special"]["damage"] / 50, C_ACCENT),
        ]
        for i, (lbl, ratio, color) in enumerate(stats):
            sy = ty_off + 46 + i * 22
            lbl_s = self.f_tiny.render(lbl, True, C_GRAY)
            self.screen.blit(lbl_s, (tx, sy))
            draw_bar(self.screen, tx + 75, sy + 2, pw - 90, 11, ratio, color)

        # Golpes
        moves_y = ty_off + 125
        pygame.draw.line(self.screen, C_BORDER, (tx, moves_y-4), (px+pw-10, moves_y-4), 1)
        moves_title = self.f_tiny.render("GOLPES", True, C_GOLD)
        self.screen.blit(moves_title, (tx, moves_y - 16))

        for i, (label, move) in enumerate([
            ("[J] LEVE",     ch["light"]["name"]),
            ("[K] MÉDIO",    ch["medium"]["name"]),
            ("[L] ESPECIAL", ch["special"]["name"]),
        ]):
            my = moves_y + i * 24
            key_color = C_ACCENT if i == 2 else C_ACCENT2
            k_s = self.f_tiny.render(label, True, key_color)
            m_s = self.f_tiny.render(move,  True, C_WHITE)
            self.screen.blit(k_s, (tx,      my))
            self.screen.blit(m_s, (tx + 88, my))

        # Descrição
        desc_y = moves_y + 80
        pygame.draw.line(self.screen, C_BORDER, (tx, desc_y-6), (px+pw-10, desc_y-6), 1)
        words = ch.get("desc","").split()
        line, lines_out = "", []
        for wd in words:
            test = line + (" " if line else "") + wd
            if self.f_tiny.size(test)[0] > pw - 22:
                lines_out.append(line); line = wd
            else:
                line = test
        if line: lines_out.append(line)
        for i, l in enumerate(lines_out[:4]):
            self.screen.blit(self.f_tiny.render(l, True, (190,190,210)), (tx, desc_y + i*14))

        # ── Sprite grande centrado na tela ─────────────────
        frame_list  = self.sprites[self.selected]
        current_img = frame_list[(self.frame // 8) % len(frame_list)]
        scale_f = ch.get("sprite_scale", 1.5)
        prev_h  = int(ph * 0.82)
        prev_w  = int(prev_h * 0.62 * scale_f)
        prev_h2 = int(prev_h * scale_f * 0.82)

        # Limitar tamanho
        max_h = ph - 20
        if prev_h2 > max_h:
            ratio = max_h / prev_h2
            prev_h2 = max_h
            prev_w  = int(prev_w * ratio)

        base_sprite = pygame.transform.scale(current_img, (prev_w, prev_h2))
        sc = self.preview_scale
        if abs(sc - 1.0) > 0.002:
            sw2 = int(prev_w * sc)
            sh2 = int(prev_h2 * sc)
            base_sprite = pygame.transform.scale(base_sprite, (sw2, sh2))

        sprite_cx = px + pw + (SW - (px + pw)) // 2
        sprite_boty = py + ph - 10

        # Sombra no chão
        shadow_surf = pygame.Surface((prev_w + 40, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0,0,0,100), shadow_surf.get_rect())
        self.screen.blit(shadow_surf, (sprite_cx - (prev_w+40)//2, sprite_boty - 6))

        # Sprite
        sx = sprite_cx - base_sprite.get_width()//2
        sy = sprite_boty - base_sprite.get_height()
        self.screen.blit(base_sprite, (sx, sy))

    # ── Cabeçalho ──────────────────────────────────────────
    def _draw_header(self):
        # Faixa de fundo
        hbar = pygame.Surface((SW, 70), pygame.SRCALPHA)
        for i in range(70):
            t = i / 70
            c = _lerp_color((15, 8, 28), (8, 4, 18), t)
            pygame.draw.line(hbar, (*c, 230), (0,i), (SW,i))
        self.screen.blit(hbar, (0, 0))

        # Linha inferior decorativa dupla
        lw = int(240 + 80 * math.sin(self.frame * 0.04))
        pygame.draw.line(self.screen, C_ACCENT, (0, 69), (SW, 69), 2)
        pygame.draw.line(self.screen, (*C_ACCENT, 80),
                         (SW//2 - lw, 66), (SW//2 + lw, 66), 1)

        # Ícone de espada à esquerda e direita do título
        pulse = 1.0 + 0.018 * math.sin(self.frame * 0.07)
        title_s = self.f_title.render("ESCOLHA SEU LUTADOR", True, C_WHITE)
        tw = int(title_s.get_width()  * pulse)
        th = int(title_s.get_height() * pulse)
        title_s = pygame.transform.scale(title_s, (tw, th))
        # Sombra vermelha
        shadow_s = self.f_title.render("ESCOLHA SEU LUTADOR", True, C_ACCENT)
        shadow_s = pygame.transform.scale(shadow_s, (tw, th))
        shadow_s.set_alpha(80)
        self.screen.blit(shadow_s, shadow_s.get_rect(center=(SW//2+3, 33+3)))
        self.screen.blit(title_s,  title_s.get_rect(center=(SW//2, 33)))

    # ── Rodapé ────────────────────────────────────────────
    def _draw_footer(self):
        fy = SH - 28
        fbar = pygame.Surface((SW, 28), pygame.SRCALPHA)
        for i in range(28):
            pygame.draw.line(fbar, (0,0,0,180), (0,i), (SW,i))
        pygame.draw.line(fbar, (*C_BORDER, 200), (0,0), (SW,0), 1)
        self.screen.blit(fbar, (0, fy))

        controls = [("← →", "Navegar"), ("ENTER", "Confirmar"), ("ESC", "Voltar")]
        parts = []
        for key, desc in controls:
            parts.append((key, desc))

        total_w = sum(
            self.f_sm.size(k)[0] + self.f_sm.size(f"  {d}    ")[0]
            for k,d in parts
        )
        cx = (SW - total_w) // 2
        for key, desc in parts:
            k_s = self.f_sm.render(key, True, C_ACCENT2)
            d_s = self.f_sm.render(f"  {desc}    ", True, C_GRAY)
            self.screen.blit(k_s, (cx, fy + 6))
            cx += k_s.get_width()
            self.screen.blit(d_s, (cx, fy + 6))
            cx += d_s.get_width()

    # ── Flash de confirmação ───────────────────────────────
    def _draw_confirm_flash(self):
        if self.flash_timer <= 0:
            return
        ch    = CHARACTERS[self.selected]
        alpha = int(220 * self.flash_timer / 24)
        flash = pygame.Surface((SW, SH), pygame.SRCALPHA)
        # Gradiente radial
        for r in range(300, 0, -20):
            a = int(alpha * (1 - r/300))
            pygame.draw.circle(flash, (*ch["color"], a), (SW//2, SH//2), r)
        self.screen.blit(flash, (0,0))

        if self.flash_timer > 12:
            # Borda brilhante
            pygame.draw.rect(self.screen, ch["color"], (20,20,SW-40,SH-40), 3, border_radius=12)
            txt = self.f_big.render(f"{ch['name']}  —  SELECIONADO!", True, C_WHITE)
            # Sombra
            sh = self.f_big.render(f"{ch['name']}  —  SELECIONADO!", True, (0,0,0))
            self.screen.blit(sh, sh.get_rect(center=(SW//2+3, SH//2+3)))
            self.screen.blit(txt, txt.get_rect(center=(SW//2, SH//2)))

        self.flash_timer -= 1
        if self.flash_timer == 0:
            self.result = self.selected


    # ── Evento de troca ────────────────────────────────────
    def _on_change(self):
        ch = CHARACTERS[self.selected]
        cx = self.cards_start_x + self.selected*(CARD_W+CARD_GAP) + CARD_W//2
        cy = self.cards_y + CARD_H//2
        self._spawn_particles(cx, cy, ch["color"], n=18)
        self.target_scale = 1.10

    # ── Loop principal ─────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and self.flash_timer == 0:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.selected = (self.selected - 1) % TOTAL_CARDS
                        self._on_change()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.selected = (self.selected + 1) % TOTAL_CARDS
                        self._on_change()
                    elif event.key == pygame.K_RETURN:
                        self.flash_timer = 24
                        ch = CHARACTERS[self.selected]
                        self._spawn_particles(SW//2, SH//2, ch["color"], n=50)

            self.frame += 1
            self.preview_scale = _lerp(self.preview_scale, self.target_scale, 0.14)
            if abs(self.preview_scale - self.target_scale) < 0.004:
                self.target_scale = 1.0

            for i in range(TOTAL_CARDS):
                if i == self.selected:
                    target_off = -14.0 + 5*math.sin(self.frame*0.09)
                else:
                    target_off = 0.0
                self.card_offsets[i] = _lerp(self.card_offsets[i], target_off, 0.13)

            self._update_particles()
            self._update_bg_particles()

            # Render
            self.screen.blit(self.bg, (0,0))
            self._draw_bg_particles()
            self._draw_header()
            self._draw_preview()
            self._draw_particles()
            for i in range(TOTAL_CARDS):
                self._draw_card(i, i == self.selected)

            self._draw_footer()
            self._draw_confirm_flash()
            pygame.display.flip()

            if self.result is not None:
                return self.result


# ─────────────────────────────────────────────────────────
#  PAUSE MENU (chamado do fight.py via import)
# ─────────────────────────────────────────────────────────
def draw_pause_overlay(screen, clock, SW, SH, on_resume, on_quit):
    """
    Exibe um menu de pausa estilo anime sobre o frame atual.
    Retorna "resume" ou "quit".
    """
    try:
        f_title = pygame.font.SysFont("impact", 72, bold=True)
        f_sub   = pygame.font.SysFont("impact", 28)
        f_tiny  = pygame.font.SysFont("impact", 18)
    except Exception:
        f_title = pygame.font.Font(None, 72)
        f_sub   = pygame.font.Font(None, 28)
        f_tiny  = pygame.font.Font(None, 18)

    # Captura o frame atual como fundo
    bg_snap = screen.copy()

    tick = 0
    while True:
        clock.tick(60)
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return "resume"
                if event.key == pygame.K_q:
                    return "quit"

        screen.blit(bg_snap, (0,0))

        # Overlay escuro com gradiente
        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        for i in range(SH):
            t = i / SH
            a = int(180 + 30 * math.sin(tick*0.05))
            c = _lerp_color((0,0,20), (0,0,8), t)
            pygame.draw.line(ov, (*c, a), (0,i), (SW,i))
        screen.blit(ov, (0,0))

        # Linhas diagonais
        for i in range(0, SW+SH, 50):
            ls = pygame.Surface((SW,SH), pygame.SRCALPHA)
            pygame.draw.line(ls, (255,140,0,15), (i,0), (i-SH,SH), 1)
            screen.blit(ls, (0,0))

        # Painel central
        pw, ph = 420, 280
        px, py = SW//2 - pw//2, SH//2 - ph//2
        panel  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for i in range(ph):
            t = i/ph
            c = _lerp_color((25,12,45),(12,5,22),t)
            pygame.draw.line(panel, (*c, 230), (0,i),(pw,i))
        msk = pygame.Surface((pw,ph),pygame.SRCALPHA)
        pygame.draw.rect(msk, (255,255,255,255), msk.get_rect(), border_radius=16)
        panel.blit(msk,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(panel, (px, py))

        # Borda dupla dourada
        gw = int(80 + 30*math.sin(tick*0.06))
        pygame.draw.rect(screen, C_GOLD,    (px,py,pw,ph), 2, border_radius=16)
        pygame.draw.rect(screen, (120,80,10,120), (px+4,py+4,pw-8,ph-8), 1, border_radius=13)

        # Linha superior decorativa
        pygame.draw.line(screen, C_GOLD,
                         (SW//2-gw, py+48), (SW//2+gw, py+48), 1)

        # Título PAUSADO
        pulse = 1.0 + 0.02*math.sin(tick*0.08)
        for ofs, col in [((3,3),(120,60,0)),((1,1),(255,100,0)),((0,0),C_GOLD)]:
            ts = f_title.render("PAUSADO", True, col)
            tw = int(ts.get_width()*pulse); th = int(ts.get_height()*pulse)
            ts = pygame.transform.scale(ts,(tw,th))
            screen.blit(ts, ts.get_rect(center=(SW//2+ofs[0], py+34+ofs[1])))

        # Opções
        opts = [
            ("[ ENTER ]  Continuar", (200,200,200)),
            ("[ Q ]  Sair para o Menu", (255,100,100)),
        ]
        for i,(text,color) in enumerate(opts):
            ts = f_sub.render(text, True, color)
            screen.blit(ts, ts.get_rect(center=(SW//2, py+130 + i*52)))
            # Linha separadora
            if i == 0:
                pygame.draw.line(screen, (*C_BORDER, 160),
                                 (px+30, py+160), (px+pw-30, py+160), 1)

        # Hint
        hint = f_tiny.render("ESC  também retoma o jogo", True, (80,70,110))
        screen.blit(hint, hint.get_rect(center=(SW//2, py+ph-18)))

        pygame.display.flip()


# ─────────────────────────────────────────────────────────
#  FUNÇÃO PÚBLICA
# ─────────────────────────────────────────────────────────
def run_selection(screen=None, clock=None):
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


if __name__ == "__main__":
    run_selection()
