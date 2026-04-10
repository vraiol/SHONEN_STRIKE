# ============================================================
#  menu.py
#  Telas do jogo: Menu Principal, Vitória e Derrota.
#  Implementa: Escala (título pulsante), Rotação (orbe)
# ============================================================

import pygame
import math
import sys

SW, SH = 1000, 620

# Paleta
C_BG1    = (5,   8,  20)
C_BG2    = (10, 15,  40)
C_ACCENT = (255, 60,  60)
C_GOLD   = (255, 200,  50)
C_WHITE  = (255, 255, 255)
C_GRAY   = (100, 100, 120)
C_BORDER = ( 50,  60, 120)
C_GREEN  = ( 60, 220, 100)
C_RED    = (220,  50,  50)


def _draw_bg(screen):
    """Fundo com gradiente e grade hexagonal."""
    for y in range(SH):
        t = y / SH
        r = int(5  + (10 - 5)  * t)
        g = int(8  + (15 - 8)  * t)
        b = int(20 + (40 - 20) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (SW, y))
    for hx in range(0, SW, 90):
        for hy in range(0, SH, 78):
            pts = []
            for k in range(6):
                a = math.radians(60 * k - 30)
                pts.append((hx + 36 * math.cos(a), hy + 36 * math.sin(a)))
            pygame.draw.polygon(screen, (15, 20, 45), pts, 1)


# ─────────────────────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────────────────────
def show_main_menu(screen, clock) -> str:
    """
    Exibe o menu principal.
    Retorna: "play" ou "quit"
    """
    f_title  = pygame.font.SysFont("impact",  72, bold=True)
    f_sub    = pygame.font.SysFont("impact",  20)
    f_option = pygame.font.SysFont("impact",  36, bold=True)
    f_hint   = pygame.font.SysFont("consolas", 13)

    options    = ["JOGAR", "SAIR"]
    sel        = 0
    frame      = 0
    orb_angle  = 0.0

    # Orbe do menu (projétil giratório decorativo — ROTAÇÃO)
    orb_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
    pts = []
    for k in range(10):
        r_val = 16 if k % 2 == 0 else 7
        a     = math.radians(36 * k - 90)
        pts.append((18 + r_val * math.cos(a), 18 + r_val * math.sin(a)))
    pygame.draw.polygon(orb_surf, C_ACCENT, pts)
    pygame.draw.polygon(orb_surf, C_WHITE,  pts, 1)
    pygame.draw.circle(orb_surf, C_WHITE, (18, 18), 4)

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return "play" if sel == 0 else "quit"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

        _draw_bg(screen)

        # ── ESCALA: título pulsa levemente ────────────────
        pulse     = 1.0 + 0.025 * math.sin(frame * 0.05)
        title_raw = f_title.render("ANIME FIGHTERS", True, C_WHITE)
        tw = int(title_raw.get_width()  * pulse)
        th = int(title_raw.get_height() * pulse)
        # ESCALA via pygame.transform.scale
        title_scaled = pygame.transform.scale(title_raw, (tw, th))
        screen.blit(title_scaled, (SW//2 - tw//2, 120 - th//2))

        # Sublinhado vermelho animado
        lw = int(220 + 80 * math.sin(frame * 0.04))
        pygame.draw.line(screen, C_ACCENT,
                         (SW//2 - lw//2, 170), (SW//2 + lw//2, 170), 3)

        sub = f_sub.render("UM JOGO DE LUTA 2D", True, C_GRAY)
        screen.blit(sub, (SW//2 - sub.get_width()//2, 182))

        # ── ROTAÇÃO: orbe giratório ───────────────────────
        orb_angle = (orb_angle + 4) % 360
        # ROTAÇÃO via pygame.transform.rotate
        orb_rot = pygame.transform.rotate(orb_surf, orb_angle)
        screen.blit(orb_rot, (SW//2 - 18, 240))

        # Opções do menu
        for i, opt in enumerate(options):
            is_sel = i == sel
            color  = C_ACCENT if is_sel else C_GRAY

            # Caixa de seleção
            if is_sel:
                box = pygame.Surface((280, 50), pygame.SRCALPHA)
                pygame.draw.rect(box, (255, 60, 60, 30), (0, 0, 280, 50), border_radius=8)
                pygame.draw.rect(box, C_ACCENT, (0, 0, 280, 50), 2, border_radius=8)
                screen.blit(box, (SW//2 - 140, 295 + i * 70))

            txt = f_option.render(opt, True, color)
            screen.blit(txt, (SW//2 - txt.get_width()//2, 305 + i * 70))

            # Seta indicadora
            if is_sel:
                arrow = f_option.render("►", True, C_ACCENT)
                screen.blit(arrow, (SW//2 - 150, 305 + i * 70))

        hint = f_hint.render("↑↓ Navegar   ENTER Confirmar", True, C_GRAY)
        screen.blit(hint, (SW//2 - hint.get_width()//2, SH - 30))

        pygame.display.flip()
        frame += 1


# ─────────────────────────────────────────────────────────
#  TELA DE VITÓRIA
# ─────────────────────────────────────────────────────────
def show_victory(screen, clock, winner_name: str,
                 phase: int, total_phases: int) -> str:
    """
    Exibe tela de vitória.
    Retorna: "continue" (próxima fase) ou "quit"
    """
    f_big  = pygame.font.SysFont("impact",  60, bold=True)
    f_med  = pygame.font.SysFont("impact",  28)
    f_sm   = pygame.font.SysFont("consolas", 15)

    frame      = 0
    orb_angle  = 0.0
    is_final   = (phase >= total_phases)
    options    = ["MENU PRINCIPAL"] if is_final else ["PRÓXIMA FASE", "MENU PRINCIPAL"]
    sel        = 0

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    sel = (sel - 1) % len(options)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    sel = (sel + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[sel] == "PRÓXIMA FASE":
                        return "continue"
                    else:
                        return "quit"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

        _draw_bg(screen)

        # Flash dourado de fundo
        alpha = int(30 + 20 * math.sin(frame * 0.08))
        flash = pygame.Surface((SW, SH), pygame.SRCALPHA)
        flash.fill((255, 200, 50, alpha))
        screen.blit(flash, (0, 0))

        # ── ESCALA: título de vitória pulsa ───────────────
        pulse    = 1.0 + 0.04 * math.sin(frame * 0.07)
        vic_raw  = f_big.render("VITÓRIA!", True, C_GOLD)
        vw = int(vic_raw.get_width()  * pulse)
        vh = int(vic_raw.get_height() * pulse)
        # ESCALA via pygame.transform.scale
        vic_scaled = pygame.transform.scale(vic_raw, (vw, vh))
        screen.blit(vic_scaled, (SW//2 - vw//2, 130))

        name_txt = f_med.render(f"{winner_name} venceu!", True, C_WHITE)
        screen.blit(name_txt, (SW//2 - name_txt.get_width()//2, 210))

        phase_txt = f_sm.render(
            f"FASE {phase} / {total_phases} CONCLUÍDA" if not is_final
            else "CAMPANHA CONCLUÍDA! Você venceu todos os inimigos!",
            True, C_GRAY)
        screen.blit(phase_txt, (SW//2 - phase_txt.get_width()//2, 250))

        # ── ROTAÇÃO: orbe decorativo ──────────────────────
        orb_angle = (orb_angle + 5) % 360
        orb_surf  = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(orb_surf, C_GOLD, (15, 15), 12)
        pygame.draw.circle(orb_surf, C_WHITE, (15, 15), 5)
        # ROTAÇÃO via pygame.transform.rotate
        orb_rot = pygame.transform.rotate(orb_surf, orb_angle)
        screen.blit(orb_rot, (SW//2 - 15, 295))

        # Botões
        total_w = len(options) * 220 + (len(options) - 1) * 20
        bx = SW//2 - total_w//2
        for i, opt in enumerate(options):
            is_s = i == sel
            bw, bh = 200, 48
            box = pygame.Surface((bw, bh), pygame.SRCALPHA)
            fill_c = (60, 220, 100, 50) if is_s else (30, 30, 60, 120)
            border_c = C_GREEN if is_s else C_BORDER
            pygame.draw.rect(box, fill_c,   (0, 0, bw, bh), border_radius=8)
            pygame.draw.rect(box, border_c, (0, 0, bw, bh), 2, border_radius=8)
            screen.blit(box, (bx + i * 220, 350))
            t = f_sm.render(opt, True, C_WHITE if is_s else C_GRAY)
            screen.blit(t, (bx + i*220 + bw//2 - t.get_width()//2, 350 + bh//2 - t.get_height()//2))

        hint = f_sm.render("← → Navegar   ENTER Confirmar", True, C_GRAY)
        screen.blit(hint, (SW//2 - hint.get_width()//2, SH - 30))

        pygame.display.flip()
        frame += 1


# ─────────────────────────────────────────────────────────
#  TELA DE DERROTA
# ─────────────────────────────────────────────────────────
def show_defeat(screen, clock, loser_name: str) -> str:
    """
    Exibe tela de derrota.
    Retorna: "retry" ou "quit"
    """
    f_big = pygame.font.SysFont("impact",  60, bold=True)
    f_med = pygame.font.SysFont("impact",  26)
    f_sm  = pygame.font.SysFont("consolas", 15)

    frame     = 0
    orb_angle = 0.0
    options   = ["TENTAR NOVAMENTE", "MENU PRINCIPAL"]
    sel       = 0

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    sel = (sel - 1) % len(options)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    sel = (sel + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return "retry" if sel == 0 else "quit"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

        _draw_bg(screen)

        # Flash vermelho de fundo
        alpha = int(40 + 25 * math.sin(frame * 0.08))
        flash = pygame.Surface((SW, SH), pygame.SRCALPHA)
        flash.fill((220, 30, 30, alpha))
        screen.blit(flash, (0, 0))

        # ── ESCALA: título de derrota ─────────────────────
        pulse   = 1.0 + 0.03 * math.sin(frame * 0.07)
        def_raw = f_big.render("DERROTA!", True, C_RED)
        dw = int(def_raw.get_width()  * pulse)
        dh = int(def_raw.get_height() * pulse)
        # ESCALA via pygame.transform.scale
        def_scaled = pygame.transform.scale(def_raw, (dw, dh))
        screen.blit(def_scaled, (SW//2 - dw//2, 130))

        sub = f_med.render(f"{loser_name} foi derrotado...", True, C_GRAY)
        screen.blit(sub, (SW//2 - sub.get_width()//2, 215))

        # ── ROTAÇÃO: orbe vermelho giratório ──────────────
        orb_angle = (orb_angle + 6) % 360
        orb_surf  = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(orb_surf, C_RED, (14, 14), 11)
        pygame.draw.circle(orb_surf, (255, 150, 150), (14, 14), 4)
        # ROTAÇÃO via pygame.transform.rotate
        orb_rot = pygame.transform.rotate(orb_surf, orb_angle)
        screen.blit(orb_rot, (SW//2 - 14, 280))

        # Botões
        total_w = len(options) * 230 + (len(options)-1)*20
        bx = SW//2 - total_w//2
        for i, opt in enumerate(options):
            is_s = i == sel
            bw, bh = 210, 48
            box = pygame.Surface((bw, bh), pygame.SRCALPHA)
            fill_c   = (255, 60, 60, 50) if is_s else (30, 30, 60, 120)
            border_c = C_RED if is_s else C_BORDER
            pygame.draw.rect(box, fill_c,   (0, 0, bw, bh), border_radius=8)
            pygame.draw.rect(box, border_c, (0, 0, bw, bh), 2, border_radius=8)
            screen.blit(box, (bx + i * 250, 345))
            t = f_sm.render(opt, True, C_WHITE if is_s else C_GRAY)
            screen.blit(t, (bx + i*250 + bw//2 - t.get_width()//2, 345 + bh//2 - t.get_height()//2))

        hint = f_sm.render("← → Navegar   ENTER Confirmar", True, C_GRAY)
        screen.blit(hint, (SW//2 - hint.get_width()//2, SH - 30))

        pygame.display.flip()
        frame += 1
