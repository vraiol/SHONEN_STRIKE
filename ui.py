import pygame
import math
import sys
from settings import *

def show_title_screen(screen, clock, font_big, font_med, font_sm):
    t = 0
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                return

        screen.fill(C_BG)
        for gx in range(0, SCREEN_W, 48):
            pygame.draw.line(screen, C_GRID, (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 48):
            pygame.draw.line(screen, C_GRID, (0, gy), (SCREEN_W, gy))

        pulse = 1.0 + 0.03 * math.sin(t * 0.05)
        ts = font_big.render(TITLE, True, C_PLAYER)
        w  = int(ts.get_width() * pulse)
        h  = int(ts.get_height() * pulse)
        ts = pygame.transform.scale(ts, (w, h))
        cx = SCREEN_W // 2
        screen.blit(ts, (cx - w//2, 160))

        sub = font_med.render("Roguelike com Transformacoes Geometricas", True, C_GRAY)
        screen.blit(sub, (cx - sub.get_width()//2, 220))

        for i, (key, desc, color) in enumerate([
            ("W A S D", "Mover jogador",     C_WHITE),
            ("Auto",    "Ataque automatico", C_PROJ),
            ("ESC",     "Sair",              C_RED),
        ]):
            screen.blit(font_sm.render(f"[{key}]", True, color), (cx - 120, 310 + i*26))
            screen.blit(font_sm.render(desc,        True, C_GRAY), (cx - 40,  310 + i*26))

        trs = font_sm.render("Translacao  *  Rotacao  *  Escala  *  Reflexao", True, C_PURPLE)
        screen.blit(trs, (cx - trs.get_width()//2, 440))

        if (t // 30) % 2 == 0:
            st = font_med.render("Pressione qualquer tecla para comecar", True, C_GOLD)
            screen.blit(st, (cx - st.get_width()//2, 510))

        t += 1
        pygame.display.flip()
