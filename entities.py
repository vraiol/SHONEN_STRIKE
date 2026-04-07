import pygame
import math
import random
from settings import *
from sprites import make_surface_projectile

class Projectile:
    SPEED  = 6.5
    RADIUS = 7

    def __init__(self, x, y, target_x, target_y):
        self.x = float(x)
        self.y = float(y)
        self.radius    = self.RADIUS
        self.angle     = 0.0   # angulo de rotacao visual
        self.rot_speed = 8.0   # graus por frame
        self.alive     = True

        # Direcao normalizada -> usado na TRANSLACAO
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vx = (dx / dist) * self.SPEED
        self.vy = (dy / dist) * self.SPEED

        self.base_surf = make_surface_projectile(self.radius)

    def update(self):
        # TRANSLACAO: deslocar posicao a cada frame
        self.x += self.vx
        self.y += self.vy

        # ROTACAO: incrementar angulo a cada frame
        self.angle = (self.angle + self.rot_speed) % 360

        margin = 40
        if (self.x < -margin or self.x > SCREEN_W + margin or
                self.y < -margin or self.y > SCREEN_H + margin):
            self.alive = False

    def draw(self, screen):
        # ROTACAO: aplicada via pygame.transform.rotate
        rotated = pygame.transform.rotate(self.base_surf, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2,      self.radius * 2
        )


class Enemy:
    BASE_SIZE  = 32
    BASE_SPEED = 1.4

    def __init__(self, player_x, player_y, sprites, difficulty=1.0):
        """
        sprites: dict pre-carregado { "bat": Surface, "eye": Surface }
        """
        # Spawn nas bordas da tela
        side = random.randint(0, 3)
        if   side == 0: self.x, self.y = random.uniform(0, SCREEN_W), -30.0
        elif side == 1: self.x, self.y = SCREEN_W + 30.0, random.uniform(0, SCREEN_H)
        elif side == 2: self.x, self.y = random.uniform(0, SCREEN_W), SCREEN_H + 30.0
        else:           self.x, self.y = -30.0, random.uniform(0, SCREEN_H)

        self.speed = (self.BASE_SPEED
                      * random.uniform(0.8, 1.4)
                      * min(difficulty * 0.3 + 0.7, 2.0))
        self.alive = True

        # ESCALA: comeca em 1.0 e cresce com o tempo
        self.scale       = 1.0
        self.scale_timer = 0
        self.scale_speed = 0.0002
        self.max_scale   = 2.2

        self.shape     = random.choice(list(sprites.keys()))
        self.base_surf = sprites[self.shape]   # sprite ja carregado

        self.angle = 0.0

    def update(self, player_x, player_y):
        # TRANSLACAO: mover em direcao ao jogador
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy) or 1
        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed

        # ESCALA: cresce gradualmente
        self.scale_timer += 1
        self.scale = min(1.0 + self.scale_timer * self.scale_speed, self.max_scale)

        # Rotacao decorativa (wobble organico)
        self.angle = math.sin(pygame.time.get_ticks() * 0.005 + id(self)) * 12

    def draw(self, screen):
        # ESCALA: redimensionar sprite com pygame.transform.scale
        new_size = int(self.BASE_SIZE * self.scale)
        scaled   = pygame.transform.scale(self.base_surf, (new_size, new_size))

        # Rotacao decorativa via pygame.transform.rotate
        rotated = pygame.transform.rotate(scaled, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)

        # Barra de tamanho (indica o quanto cresceu)
        if self.scale > 1.3:
            bar_w = new_size
            bx = int(self.x) - bar_w // 2
            by = int(self.y) - new_size // 2 - 6
            fill = min((self.scale - 1.0) / (self.max_scale - 1.0), 1.0)
            pygame.draw.rect(screen, (60, 40, 40), (bx, by, bar_w, 3))
            pygame.draw.rect(screen, C_GOLD,       (bx, by, int(bar_w * fill), 3))

    def get_radius(self):
        return int((self.BASE_SIZE // 2) * self.scale)

    def get_damage(self):
        """Inimigos maiores causam mais dano."""
        return 1 + int((self.scale - 1.0) * 2)


class Player:
    SPEED          = 4.0
    MAX_HP         = 100
    BASE_SIZE      = 36
    SHOOT_COOLDOWN = 45  # frames

    def __init__(self, sprite):
        self.x = float(SCREEN_W // 2)
        self.y = float(SCREEN_H // 2)
        self.hp    = self.MAX_HP
        self.alive = True

        # REFLEXAO: controla se o sprite esta espelhado
        self.facing_left = False

        # ESCALA: modificada pelo power-up
        self.scale            = 1.0
        self.powerup_timer    = 0
        self.powerup_duration = 300  # frames (~5 s)

        self.shoot_timer = 0
        self.iframes     = 0     # frames de invencibilidade apos dano
        self.base_surf   = sprite
        self.trail       = []    # trilha visual de movimento

    def handle_input(self):
        keys   = pygame.key.get_pressed()
        vx, vy = 0.0, 0.0
        speed  = self.SPEED * self.scale

        if keys[pygame.K_w] or keys[pygame.K_UP]:    vy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  vy += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx -= speed
            self.facing_left = True    # REFLEXAO: virar para esquerda
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx += speed
            self.facing_left = False   # REFLEXAO: virar para direita

        # Normalizar movimento diagonal
        if vx != 0 and vy != 0:
            vx *= 0.707
            vy *= 0.707

        # TRANSLACAO: atualizar coordenadas (x, y)
        self.x = max(18, min(SCREEN_W - 18, self.x + vx))
        self.y = max(18, min(SCREEN_H - 18, self.y + vy))

        if vx != 0 or vy != 0:
            self.trail.append((int(self.x), int(self.y),
                               max(0, 180 - len(self.trail) * 30)))
        if len(self.trail) > 6:
            self.trail.pop(0)

    def update(self, enemies, projectiles):
        self.handle_input()

        if self.shoot_timer > 0: self.shoot_timer -= 1
        if self.iframes     > 0: self.iframes     -= 1

        # Power-up expira
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
            if self.powerup_timer == 0:
                self.scale = 1.0  # ESCALA retorna ao normal

        # Disparo automatico no inimigo mais proximo
        if self.shoot_timer == 0 and enemies:
            target = min(enemies,
                         key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
            projectiles.append(Projectile(self.x, self.y, target.x, target.y))
            self.shoot_timer = max(15, self.SHOOT_COOLDOWN - len(enemies) * 2)

        # Colisao com inimigos -> reduz HP
        if self.iframes == 0:
            for e in enemies:
                if math.hypot(e.x - self.x, e.y - self.y) < e.get_radius() + self.get_radius():
                    self.hp -= e.get_damage()
                    self.iframes = 45
                    if self.hp <= 0:
                        self.alive = False
                    break

    def apply_powerup(self):
        """ESCALA: power-up aumenta tamanho e velocidade do jogador."""
        self.scale         = 1.5
        self.powerup_timer = self.powerup_duration

    def get_radius(self):
        return int((self.BASE_SIZE // 2) * self.scale * 0.7)

    def draw(self, screen):
        # Trilha de movimento
        for i, (tx, ty, alpha) in enumerate(self.trail):
            r = max(2, int(6 * self.scale) - (len(self.trail) - i))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_PLAYER, max(0, alpha)), (r, r), r)
            screen.blit(s, (tx - r, ty - r))

        # ESCALA: redimensionar sprite
        size = int(self.BASE_SIZE * self.scale)
        surf = pygame.transform.scale(self.base_surf, (size, size))

        # REFLEXAO: espelhar horizontalmente ao mover para esquerda
        if self.facing_left:
            surf = pygame.transform.flip(surf, True, False)

        # Piscar durante invencibilidade
        if self.iframes > 0 and (self.iframes // 4) % 2 == 0:
            return

        screen.blit(surf, surf.get_rect(center=(int(self.x), int(self.y))))

        # Aura dourada quando power-up esta ativo
        if self.powerup_timer > 0:
            alpha = int(80 + 50 * math.sin(pygame.time.get_ticks() * 0.01))
            aura  = pygame.Surface((size + 20, size + 20), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*C_GOLD, alpha),
                               (size//2 + 10, size//2 + 10), size//2 + 8, 3)
            screen.blit(aura, (int(self.x) - size//2 - 10,
                               int(self.y) - size//2 - 10))

    def draw_hud(self, screen, font_big, font_sm, score, elapsed):
        # Barra de HP
        bar_x, bar_y, bar_w, bar_h = 16, 16, 220, 18
        pygame.draw.rect(screen, (40, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        hp_ratio = max(0, self.hp / self.MAX_HP)
        hp_color = (int(220*(1-hp_ratio)), int(180*hp_ratio), 60)
        pygame.draw.rect(screen, hp_color,
                         (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=4)
        pygame.draw.rect(screen, (100, 80, 80),
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        screen.blit(font_sm.render(f"HP: {max(0,self.hp)}/{self.MAX_HP}", True, C_WHITE),
                    (bar_x + 6, bar_y + 1))

        # Cronometro central
        mins, secs = elapsed // 60, elapsed % 60
        t = font_big.render(f"{mins:02d}:{secs:02d}", True, C_GOLD)
        screen.blit(t, (SCREEN_W//2 - t.get_width()//2, 12))

        # Contador de kills
        screen.blit(font_sm.render(f"Kills: {score}", True, C_PURPLE),
                    (SCREEN_W - 100, 16))

        # Indicador de power-up ativo
        if self.powerup_timer > 0:
            pu = font_sm.render("POWER-UP ATIVO!", True, C_GOLD)
            screen.blit(pu, (SCREEN_W//2 - pu.get_width()//2, 44))


class PowerUp:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.alive  = True
        self.timer  = 0
        self.radius = 10

    def update(self):
        self.timer += 1

    def draw(self, screen):
        pulse = 1.0 + 0.2 * math.sin(self.timer * 0.1)
        r = int(self.radius * pulse)
        s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C_GOLD,  200), (r+2, r+2), r)
        pygame.draw.circle(s, (*C_WHITE, 255), (r+2, r+2), r//2)
        screen.blit(s, (int(self.x)-r-2, int(self.y)-r-2))

    def get_rect(self):
        return pygame.Rect(self.x-self.radius, self.y-self.radius,
                           self.radius*2, self.radius*2)


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5.0)
        self.vx, self.vy = math.cos(angle)*speed, math.sin(angle)*speed
        self.life = self.max_life = random.randint(15, 35)
        self.color  = color
        self.radius = random.randint(2, 5)

    def update(self):
        self.x  += self.vx;  self.y  += self.vy
        self.vx *= 0.92;     self.vy *= 0.92
        self.life -= 1

    def draw(self, screen):
        alpha = int(255 * self.life / self.max_life)
        r     = max(1, int(self.radius * self.life / self.max_life))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        screen.blit(s, (int(self.x)-r, int(self.y)-r))
