import pygame

def make_surface_projectile(r):
    """Cria sprite da shuriken (projetil giratorio)."""
    size = r * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pts = [
        (cx,              cy - int(r*1.5)),
        (cx + int(r*0.4), cy - int(r*0.4)),
        (cx + int(r*1.5), cy),
        (cx + int(r*0.4), cy + int(r*0.4)),
        (cx,              cy + int(r*1.5)),
        (cx - int(r*0.4), cy + int(r*0.4)),
        (cx - int(r*1.5), cy),
        (cx - int(r*0.4), cy - int(r*0.4)),
    ]
    pygame.draw.polygon(surf, (200, 200, 210), pts)
    pygame.draw.polygon(surf, (100, 100, 110), pts, 2)
    pygame.draw.circle(surf, (30, 30, 40),    (cx, cy), int(r*0.4)+1)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(1, int(r*0.2)))
    return surf

def make_surface_player(w, h):
    """Cria sprite do jogador (samurai procedural)."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    
    C_SKIN = (255, 218, 185)
    C_HAIR = (20, 20, 25)
    C_ROBE = (30, 35, 50)
    C_BELT = (240, 170, 40)
    C_SWORD = (40, 100, 60)
    C_SHOES = (100, 60, 40)
    
    hx = w // 2 + 2
    hr = int(w * 0.18)
    hy = hr + 4
    
    bx = hx - int(w * 0.15)
    by = hy + hr - 2
    bw = int(w * 0.3)
    bh = int(h * 0.3)
    
    pygame.draw.line(surf, C_SWORD, (hx + 2, by + 6), (hx - 16, by + 6), 3)
    
    lw = 4
    lh = h - (by + bh) - 2
    pygame.draw.rect(surf, (180, 140, 120), (bx + 1, by + bh, lw, lh))
    pygame.draw.rect(surf, C_SHOES, (bx, by + bh + lh - 2, lw+2, 3))
    pygame.draw.rect(surf, C_SKIN, (bx + bw - lw, by + bh, lw, lh))
    pygame.draw.rect(surf, C_SHOES, (bx + bw - lw - 1, by + bh + lh - 2, lw+2, 3))
    
    pygame.draw.rect(surf, C_ROBE, (bx, by, bw, bh), border_radius=2)
    pygame.draw.polygon(surf, C_ROBE, [(bx, by+bh-2), (bx-3, by+bh+4), (bx+bw+3, by+bh+4), (bx+bw, by+bh-2)])
    pygame.draw.rect(surf, C_BELT, (bx, by + bh - 4, bw, 3))
    
    pygame.draw.circle(surf, C_SKIN, (hx, hy), hr)
    pygame.draw.rect(surf, C_HAIR, (hx - hr - 2, hy - hr, hr * 2, hr + 1))
    pygame.draw.rect(surf, C_HAIR, (hx - hr - 2, hy - hr, hr+1, hr * 2 + 2))
    pygame.draw.polygon(surf, C_HAIR, [(hx - hr, hy - hr + 2), (hx - hr - 6, hy - hr - 4), (hx - hr - 1, hy - hr - 2)])
    pygame.draw.polygon(surf, C_HAIR, [(hx - hr - 2, hy - hr - 2), (hx - hr - 10, hy + 2), (hx - hr, hy - hr)])

    pygame.draw.rect(surf, (0, 0, 0), (hx + 1, hy - 1, 2, 3))
    
    pygame.draw.line(surf, C_ROBE, (bx + bw - 3, by + 2), (bx + bw + 4, by + 8), 4)
    pygame.draw.circle(surf, C_SKIN, (bx + bw + 4, by + 8), 2)
    pygame.draw.line(surf, (80, 80, 80), (bx + bw, by + 8), (bx + bw + 8, by + 8), 2)

    return surf


def make_surface_enemy(w, h, shape):
    """Cria sprite do inimigo"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    
    if shape == "bat":
        pts_left = [(cx - 6, cy - 1), (cx - 16, cy - 8), (cx - 14, cy), (cx - 12, cy + 8), (cx - 6, cy + 3)]
        pts_right = [(cx + 6, cy - 1), (cx + 16, cy - 8), (cx + 14, cy), (cx + 12, cy + 8), (cx + 6, cy + 3)]
        pygame.draw.polygon(surf, (40, 30, 50), pts_left)
        pygame.draw.polygon(surf, (40, 30, 50), pts_right)
        pygame.draw.polygon(surf, (40, 30, 50), [(cx - 4, cy - 5), (cx - 6, cy - 12), (cx - 1, cy - 6)])
        pygame.draw.polygon(surf, (40, 30, 50), [(cx + 4, cy - 5), (cx + 6, cy - 12), (cx + 1, cy - 6)])
        pygame.draw.circle(surf, (40, 30, 50), (cx, cy), 7)
        pygame.draw.circle(surf, (255, 50, 50), (cx - 3, cy - 1), 2)
        pygame.draw.circle(surf, (255, 50, 50), (cx + 3, cy - 1), 2)
        
    elif shape == "eye":
        pygame.draw.circle(surf, (200, 50, 70), (cx, cy), 12)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 8)
        pygame.draw.circle(surf, (30, 100, 200), (cx, cy), 4)
        pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 2)
        pygame.draw.polygon(surf, (100, 30, 40), [(cx - 10, cy), (cx - 18, cy - 6), (cx - 12, cy + 4)])
        pygame.draw.polygon(surf, (100, 30, 40), [(cx + 10, cy), (cx + 18, cy - 6), (cx + 12, cy + 4)])

    return surf
