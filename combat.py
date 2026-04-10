# ============================================================
#  combat.py
#  Sistema de combate: projéteis, colisões e efeitos.
#  Implementa: Rotação (projéteis), Translação (movimento)
# ============================================================

import pygame
import math
import random
import os
import re

from character import Character, STATE_DEAD, CHAR_W, CHAR_H


# ── Paleta de efeitos ─────────────────────────────────────
C_HIT_LIGHT   = (255, 220, 80)
C_HIT_MEDIUM  = (255, 140, 40)
C_HIT_SPECIAL = (255, 60,  200)


# ─────────────────────────────────────────────────────────
#  PROJÉTIL
#  Implementa: Translação (movimento) + Rotação (visual)
# ─────────────────────────────────────────────────────────
class Projectile:
    SPEED  = 8
    RADIUS = 14

    def __init__(self, owner: Character, damage: int, color: tuple, is_beam: bool = False):
        self.owner  = owner
        self.damage = damage
        self.color  = color
        self.alive  = True
        self.is_beam = is_beam
        self.life   = 35 # Tempo máximo que o laser fica aceso antes de apagar

        # TRANSLAÇÃO: posição inicial na frente do personagem
        self.x  = owner.x + CHAR_W + 5 if owner.facing_right else owner.x - 10
        self.vx = self.SPEED if owner.facing_right else -self.SPEED
        if self.is_beam:
            self.vx = 0.0 # O laser não viaja, ele estica!

        self.y   = owner.y - CHAR_H // 2
        self.vy  = 0.0

        # ROTAÇÃO: ângulo acumulado (gira a cada frame)
        self.angle     = 0.0
        self.rot_speed = 7.0

        # Animação Baseada em Sprites (Pasta)
        self.frames = []
        self.frame_index = 0
        self.anim_timer = 0
        
        anim_folder = owner.data.get("anim_folder", "")
        if anim_folder:
            proj_folder = os.path.join(anim_folder, "projectile")
            if os.path.exists(proj_folder):
                valid_exts = ('.png', '.jpg', '.jpeg')
                raw_files = [f for f in os.listdir(proj_folder) if f.lower().endswith(valid_exts)]
                files = sorted(raw_files, key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
                
                for fname in files:
                    fpath = os.path.join(proj_folder, fname)
                    try:
                        img = pygame.image.load(fpath).convert_alpha()
                        corner_color = img.get_at((0, 0))
                        if corner_color.a == 255:
                            pix = pygame.PixelArray(img)
                            pix.replace(corner_color, (0, 0, 0, 0))
                            del pix
                        self.frames.append(img)
                    except Exception:
                        continue

        if not self.frames:
            # Montar superfície do projétil genérico (estrela de 4 pontas) fallback
            self._build_surf()

    def _build_surf(self):
        r    = self.RADIUS
        size = r * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        # Estrela de 4 pontas
        pts = [
            (cx,          cy - r),
            (cx + r//3,   cy - r//3),
            (cx + r,      cy),
            (cx + r//3,   cy + r//3),
            (cx,          cy + r),
            (cx - r//3,   cy + r//3),
            (cx - r,      cy),
            (cx - r//3,   cy - r//3),
        ]
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 1)
        # Núcleo branco brilhante
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r // 3)
        self.base_surf = surf

    def update(self):
        if self.is_beam:
            # Ficar preso à mão de quem disparou o laser
            self.x = self.owner.x + CHAR_W if self.owner.facing_right else self.owner.x
            self.y = self.owner.y - CHAR_H // 2
            self.life -= 1
            if self.life <= 0:
                self.alive = False
        else:
            # TRANSLAÇÃO: mover projétil bola de energia normal
            self.x += self.vx
            self.y += self.vy

        # ROTAÇÃO: incrementar ângulo a cada frame
        self.angle = (self.angle + self.rot_speed) % 360

        # Transformar animação se tiver frames
        if self.frames:
            self.anim_timer += 1
            if self.anim_timer >= 7: # Vel da animação do disparo (maior = mais lento)
                self.anim_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)

        # Desativar se sair da tela
        if self.x < -150 or self.x > 1150:
            self.alive = False

    def draw(self, screen: pygame.Surface):
        if self.frames:
            surf = self.frames[self.frame_index]
            if not self.owner.facing_right:
                surf = pygame.transform.flip(surf, True, False)
                
            if self.is_beam:
                # Esticar o laser agressivamente ocupando o ecrã até a borda final
                dist = 1100 - self.x if self.owner.facing_right else self.x + 100
                dist = max(1, int(dist))
                sh = min(90, surf.get_height()) # Altura controlada do feixe
                stretched = pygame.transform.scale(surf, (dist, sh))
                
                if self.owner.facing_right:
                    rect = stretched.get_rect(midleft=(int(self.x), int(self.y)))
                else:
                    rect = stretched.get_rect(midright=(int(self.x), int(self.y)))
                screen.blit(stretched, rect)
            else:
                rect = surf.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(surf, rect)
            return

        # ROTAÇÃO: aplicar via pygame.transform.rotate (fallback estrela)
        rotated = pygame.transform.rotate(self.base_surf, self.angle)
        rect    = rotated.get_rect(center=(int(self.x), int(self.y)))

        # Aura de brilho
        aura_r = self.RADIUS + 6
        aura   = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*self.color, 50), (aura_r, aura_r), aura_r)
        screen.blit(aura, (int(self.x) - aura_r, int(self.y) - aura_r))

        screen.blit(rotated, rect)

    def get_rect(self) -> pygame.Rect:
        if self.is_beam:
            dist = 1100 - self.x if self.owner.facing_right else self.x + 100
            draw_x = int(self.x) if self.owner.facing_right else -100
            return pygame.Rect(draw_x, int(self.y) - 25, max(1, int(dist)), 50)
            
        if self.frames:
            surf = self.frames[self.frame_index]
            r = surf.get_rect(center=(int(self.x), int(self.y)))
            return r
        return pygame.Rect(int(self.x) - self.RADIUS, int(self.y) - self.RADIUS,
                           self.RADIUS * 2, self.RADIUS * 2)


# ─────────────────────────────────────────────────────────
#  PARTÍCULA DE IMPACTO
# ─────────────────────────────────────────────────────────
class HitParticle:
    def __init__(self, x: float, y: float, color: tuple, n: int = 10):
        self.sparks = []
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 7)
            self.sparks.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(12, 28),
                "max": 28,
                "r": random.randint(2, 5),
                "color": color,
            })

    def update(self):
        for s in self.sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["vx"] *= 0.88
            s["vy"] *= 0.88
            s["life"] -= 1
        self.sparks = [s for s in self.sparks if s["life"] > 0]

    @property
    def alive(self):
        return len(self.sparks) > 0

    def draw(self, screen: pygame.Surface):
        for s in self.sparks:
            alpha = int(255 * s["life"] / s["max"])
            r     = max(1, int(s["r"] * s["life"] / s["max"]))
            surf  = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*s["color"], alpha), (r, r), r)
            screen.blit(surf, (int(s["x"]) - r, int(s["y"]) - r))


# ─────────────────────────────────────────────────────────
#  TEXTO DE DANO FLUTUANTE
# ─────────────────────────────────────────────────────────
class DamageText:
    def __init__(self, x, y, amount, color, font):
        self.x     = float(x)
        self.y     = float(y)
        self.vy    = -2.5
        self.life  = 40
        self.max   = 40
        self.text  = font.render(f"-{amount}", True, color)

    def update(self):
        self.y   += self.vy
        self.vy  *= 0.94
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, screen):
        alpha = int(255 * self.life / self.max)
        s = self.text.copy()
        s.set_alpha(alpha)
        screen.blit(s, (int(self.x), int(self.y)))


# ─────────────────────────────────────────────────────────
#  GERENCIADOR DE COMBATE
# ─────────────────────────────────────────────────────────
class CombatManager:

    def __init__(self):
        self.projectiles : list[Projectile]  = []
        self.particles   : list[HitParticle] = []
        self.damage_texts: list[DamageText]  = []
        self._font = None

    def set_font(self, font):
        self._font = font

    # ── Lançar projétil ───────────────────────────────────
    def spawn_projectile(self, owner: Character):
        atk   = owner.data["special"]
        color = owner.color
        is_bm = atk.get("is_beam", False)
        proj  = Projectile(owner, atk["damage"], color, is_beam=is_bm)
        self.projectiles.append(proj)

    # ── Efeito de impacto ─────────────────────────────────
    def spawn_hit_effect(self, x, y, damage, attack_type, color):
        if attack_type == "light":
            c, n = C_HIT_LIGHT, 8
        elif attack_type == "medium":
            c, n = C_HIT_MEDIUM, 12
        else:
            c, n = C_HIT_SPECIAL, 20
        self.particles.append(HitParticle(x, y, c, n))
        if self._font:
            self.damage_texts.append(DamageText(x, y - 20, damage, color, self._font))

    # ── Checar colisão de hitbox corpo-a-corpo ────────────
    def check_melee_hit(self,
                        attacker: Character,
                        defender: Character,
                        attack_type: str) -> bool:
        """
        Verifica se a hitbox do atacante acertou o corpo do defensor.
        Retorna True e aplica dano se houve colisão.
        """
        if attacker.active_hitbox is None:
            return False
        if not defender.alive:
            return False
        # Evitar o atacante atingir a si mesmo
        if attacker is defender:
            return False

        if attacker.active_hitbox.colliderect(defender.body_rect):
            atk_data = attacker.data[attack_type]
            damage   = atk_data["damage"]
            defender.take_damage(damage)
            cx = defender.center_x
            cy = defender.y - CHAR_H // 2
            self.spawn_hit_effect(cx, cy, damage, attack_type, attacker.color)
            # Anular hitbox após o primeiro acerto (um golpe por swing)
            attacker.active_hitbox = None
            return True
        return False

    # ── Checar colisão de projéteis ───────────────────────
    def check_projectile_hits(self, defenders: list[Character]):
        for proj in self.projectiles[:]:
            if not proj.alive:
                continue
            for defender in defenders:
                if not defender.alive:
                    continue
                if defender is proj.owner:
                    continue
                if proj.get_rect().colliderect(defender.body_rect):
                    defender.take_damage(proj.damage)
                    self.spawn_hit_effect(
                        proj.x, proj.y, proj.damage,
                        "special", proj.color)
                    proj.alive = False
                    break

    # ── Update geral ──────────────────────────────────────
    def update(self, player: Character, enemy: Character):
        # Atualizar projéteis
        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Checar colisões corpo-a-corpo (os dois lados)
        for atk_type in ("light", "medium", "special"):
            # player → enemy
            if player.state == f"attack_{atk_type.replace('light','light').replace('medium','medium').replace('special','special')}":
                pass
        # Mapeamento correto de estado → tipo
        state_to_type = {
            "attack_light":   "light",
            "attack_medium":  "medium",
            "attack_special": "special",
        }
        for state, atype in state_to_type.items():
            if player.state == state:
                self.check_melee_hit(player, enemy, atype)
            if enemy.state == state:
                self.check_melee_hit(enemy, player, atype)

        # Checar projéteis contra ambos
        self.check_projectile_hits([player, enemy])

        # Atualizar partículas e textos
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for dt in self.damage_texts:
            dt.update()
        self.damage_texts = [dt for dt in self.damage_texts if dt.alive]

    # ── Desenhar ──────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        for proj in self.projectiles:
            proj.draw(screen)
        for p in self.particles:
            p.draw(screen)
        for dt in self.damage_texts:
            dt.draw(screen)

    def reset(self):
        self.projectiles.clear()
        self.particles.clear()
        self.damage_texts.clear()
