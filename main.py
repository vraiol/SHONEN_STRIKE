import pygame
import sys

from settings import *
from ui import show_title_screen
from game import Game

if __name__ == "__main__":
    pygame.init()
    screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock    = pygame.time.Clock()
    
    font_big = pygame.font.SysFont("consolas", 28, bold=True)
    font_med = pygame.font.SysFont("consolas", 20)
    font_sm  = pygame.font.SysFont("consolas", 15)

    show_title_screen(screen, clock, font_big, font_med, font_sm)
    Game().run()
