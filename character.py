# ============================================================
#  character.py
#  Classe base Character — usada tanto pelo jogador quanto
#  pelos inimigos controlados por IA.
#  Implementa: Translação, Reflexão, Escala
# ============================================================

import pygame
import math
import os
import re


# ── Constantes de estado ──────────────────────────────────
STATE_IDLE      = "idle"
STATE_WALK      = "walk"
STATE_JUMP      = "jump"
STATE_CROUCH    = "crouch"
STATE_ATTACK_L  = "attack_light"
STATE_ATTACK_M  = "attack_medium"
STATE_ATTACK_S  = "attack_special"
STATE_HIT       = "hit"
STATE_DEAD      = "dead"

# Física
GRAVITY      = 0.7
FLOOR_Y      = 480   # Y do chão (definido em relação à tela 1000x620)
JUMP_FORCE   = -16
CHAR_W       = 64
CHAR_H       = 96


def _load_sprite(path, w, h, color):
    """Carrega sprite externo ou cria placeholder colorido."""
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (w, h))
        except Exception:
            pass
    # Placeholder: silhueta geométrica do lutador
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # Sombra do chão
    pygame.draw.ellipse(surf, (0, 0, 0, 60), (w//4, h - 10, w//2, 8))
    # Pernas
    lw = w // 5
    pygame.draw.rect(surf, tuple(max(0, c-50) for c in color),
                     (w//2 - lw - 2, h - h//3, lw, h//3 - 8), border_radius=4)
    pygame.draw.rect(surf, tuple(max(0, c-50) for c in color),
                     (w//2 + 2, h - h//3, lw, h//3 - 8), border_radius=4)
    # Corpo
    bw, bh = w * 2//3, h * 2//5
    pygame.draw.rect(surf, color,
                     (w//2 - bw//2, h - h//3 - bh + 4, bw, bh), border_radius=6)
    # Cabeça
    pygame.draw.circle(surf, color, (w//2, h - h//3 - bh - h//8), h//7)
    # Braços
    pygame.draw.rect(surf, color,
                     (w//2 - bw//2 - 10, h - h//3 - bh + 8, 10, bh//2), border_radius=4)
    pygame.draw.rect(surf, color,
                     (w//2 + bw//2,      h - h//3 - bh + 8, 10, bh//2), border_radius=4)
    # Brilho lateral
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, 25), (w//2, h//2), w//2)
    surf.blit(glow, (0, 0))
    return surf


def _load_animations_from_folder(base_folder, colorkey):
    """
    Lê pastas com quadros manuais nomeados e as mapeia para os estados do jogo.
    Se a pasta não tiver frames, retorna lista vazia para o estado correspondente (causando fallback).
    """
    if not os.path.exists(base_folder):
        return {}

    FOLDER_MAP = {
        STATE_IDLE: "stance",
        STATE_WALK: "run",
        STATE_JUMP: "jump",
        STATE_CROUCH: "stance", # fallback para croutch se não tiver
        STATE_HIT:  "taking damage",
        STATE_DEAD: "taking damage",
        STATE_ATTACK_L: "attack combo",
        STATE_ATTACK_M: "attack combo",
        STATE_ATTACK_S: "special movie",
    }
    
    animations = {}
    for state, folder_name in FOLDER_MAP.items():
        folder_path = os.path.join(base_folder, folder_name)
        frames = []
        if os.path.isdir(folder_path):
            valid_exts = ('.png', '.jpg', '.jpeg')
            raw_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]
            # Natural sort para que 10.png venha depois de 2.png
            files = sorted(raw_files, key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
            
            for fname in files:
                fpath = os.path.join(folder_path, fname)
                try:
                    img = pygame.image.load(fpath).convert_alpha()
                    
                    corner_color = img.get_at((0, 0))
                    if corner_color.a == 255:  # Se não for pixel em branco/vazio
                        pix = pygame.PixelArray(img)
                        pix.replace(corner_color, (0, 0, 0, 0))
                        del pix # Destrava a imagem na memória
                        
                    frames.append(img)
                except Exception:
                    continue
        animations[state] = frames
        
    return animations


class Character:
    """
    Classe base compartilhada por jogador e inimigos.
    Gerencia física (y para pulo, x para movimento), máquina de estados,
    ataques (hitboxes) e draw (animação manual por frames em pasta ou estático).
    """
    def __init__(self, data: dict, x: float, facing_right: bool = True):
        self.data         = data
        self.name         = data["name"]
        self.max_hp       = data["hp"]
        self.hp           = data["hp"]
        self.base_speed   = data["speed"]

        self.x   = float(x)
        self.y   = float(FLOOR_Y)
        self.vx  = 0.0
        self.vy  = 0.0

        self.facing_right = facing_right

        self.base_scale    = 1.0
        self.current_scale = 1.0
        self.target_scale  = 1.0

        self.state       = STATE_IDLE
        self.on_ground   = True
        self.crouching   = False

        self.cd_light   = 0
        self.cd_medium  = 0
        self.cd_special = 0

        self.state_timer = 0

        self.active_hitbox = None
        self.hitbox_timer  = 0

        self.projectiles = []
        self.hit_timer  = 0
        self.dead_timer = 0
        self.attack_timer = 0

        self.sprite_base = _load_sprite(
            data.get("sprite", ""), CHAR_W, CHAR_H, data["color"])
        self.color = data["color"]

        self.animations = {}
        self.current_anim_frames = []
        self.frame_index = 0
        self.anim_timer = 0
        self._last_state = STATE_IDLE
        self.sprite_scale_factor = data.get("sprite_scale", 1.8)
        
        if "anim_folder" in data:
            self.animations = _load_animations_from_folder(
                data["anim_folder"], data.get("colorkey", None)
            )
            self._set_anim(STATE_IDLE)

        self.arena_left  = 60
        self.arena_right = 940

    def _set_anim(self, state: str):
        if state in self.animations:
            if self.current_anim_frames != self.animations[state]:
                self.current_anim_frames = self.animations[state]
                self.frame_index = 0
                self.anim_timer = 0

    # ─────────────────────────────────────────────────────
    #  PROPRIEDADES
    # ─────────────────────────────────────────────────────

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def is_attacking(self) -> bool:
        return self.state in (STATE_ATTACK_L, STATE_ATTACK_M, STATE_ATTACK_S)

    @property
    def center_x(self) -> float:
        return self.x + CHAR_W // 2

    @property
    def body_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y) - CHAR_H,
                           CHAR_W, CHAR_H)

    # ─────────────────────────────────────────────────────
    #  MOVIMENTAÇÃO (TRANSLAÇÃO)
    # ─────────────────────────────────────────────────────

    def move_left(self):
        """
        TRANSLAÇÃO: decrementa x (move para esquerda).
        REFLEXÃO: atualiza direção para esquerda.
        """
        if self.is_attacking or self.state == STATE_HIT:
            return
        self.vx           = -self.base_speed
        self.facing_right = False          # REFLEXÃO
        if self.on_ground:
            self.state = STATE_WALK

    def move_right(self):
        """
        TRANSLAÇÃO: incrementa x (move para direita).
        REFLEXÃO: atualiza direção para direita.
        """
        if self.is_attacking or self.state == STATE_HIT:
            return
        self.vx           = self.base_speed
        self.facing_right = True           # REFLEXÃO
        if self.on_ground:
            self.state = STATE_WALK

    def stop_horizontal(self):
        self.vx = 0.0
        if self.on_ground and self.state == STATE_WALK:
            self.state = STATE_IDLE

    def jump(self):
        """TRANSLAÇÃO: aplica força vertical para pular."""
        if not self.on_ground or self.is_attacking:
            return
        self.vy       = JUMP_FORCE
        self.on_ground = False
        self.state    = STATE_JUMP

    def crouch(self):
        if self.on_ground and not self.is_attacking:
            self.crouching = True
            self.state     = STATE_CROUCH

    def stand_up(self):
        self.crouching = False
        if self.state == STATE_CROUCH:
            self.state = STATE_IDLE

    # ─────────────────────────────────────────────────────
    #  ATAQUES — sistema genérico (player e IA usam igual)
    # ─────────────────────────────────────────────────────

    def _can_attack(self) -> bool:
        return (self.alive
                and not self.is_attacking
                and self.state != STATE_HIT
                and self.state != STATE_DEAD)

    def _build_hitbox(self, attack_range: int) -> pygame.Rect:
        """Cria hitbox na frente do personagem."""
        if self.facing_right:
            hx = int(self.x + CHAR_W)
        else:
            hx = int(self.x - attack_range)
        return pygame.Rect(hx, int(self.y) - CHAR_H + 10,
                           attack_range, CHAR_H - 20)

    def attack_light(self):
        """Golpe leve — rápido, pouco dano."""
        if not self._can_attack() or self.cd_light > 0:
            return False
        atk            = self.data["light"]
        self.state     = STATE_ATTACK_L
        self.state_timer = atk["cooldown"]
        self.cd_light  = atk["cooldown"]
        self.active_hitbox = self._build_hitbox(atk["range"])
        self.hitbox_timer  = atk["cooldown"] // 3
        return True

    def attack_medium(self):
        """Golpe médio — equilibrado."""
        if not self._can_attack() or self.cd_medium > 0:
            return False
        atk            = self.data["medium"]
        self.state     = STATE_ATTACK_M
        self.state_timer = atk["cooldown"]
        self.cd_medium = atk["cooldown"]
        self.active_hitbox = self._build_hitbox(atk["range"])
        self.hitbox_timer  = atk["cooldown"] // 3
        return True

    def attack_special(self):
        """
        Golpe especial — poderoso, com projétil.
        ESCALA: personagem aumenta temporariamente ao usar o especial.
        """
        if not self._can_attack() or self.cd_special > 0:
            return False
        atk             = self.data["special"]
        self.state      = STATE_ATTACK_S
        self.state_timer  = atk["cooldown"]
        self.cd_special = atk["cooldown"]
        self.active_hitbox = self._build_hitbox(atk["range"])
        self.hitbox_timer  = atk["cooldown"] // 2

        # ESCALA: aumentar personagem temporariamente no especial
        self.target_scale = 1.35

        return True

    # ─────────────────────────────────────────────────────
    #  RECEBER DANO
    # ─────────────────────────────────────────────────────

    def take_damage(self, amount: int):
        if not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self.state       = STATE_HIT
        self.state_timer = 18
        self.hit_timer   = 18
        self.active_hitbox = None
        # Knockback leve
        self.vx = 4.0 if self.facing_right else -4.0
        if self.hp <= 0:
            self.state = STATE_DEAD

    # ─────────────────────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────────────────────

    def update(self):
        # Transição de animação ao mudar de estado
        if self.state != self._last_state:
            self._set_anim(self.state)
            self._last_state = self.state

        # Update de frames da animação
        if self.current_anim_frames and len(self.current_anim_frames) > 0:
            self.anim_timer += 1
            
            # Dinâmica de velocidade: Especial muito mais lento
            speed_limit = 14 if self.state == STATE_ATTACK_S else 8
            
            if self.anim_timer >= speed_limit:
                self.anim_timer = 0
                self.frame_index += 1
                
                # Se for ataque, trava no último frame (não repete o loop inteiro)
                if self.is_attacking:
                    self.frame_index = min(self.frame_index, len(self.current_anim_frames) - 1)
                else:
                    self.frame_index = self.frame_index % len(self.current_anim_frames)

        if self.state == STATE_DEAD:
            self.dead_timer += 1
            return

        # ── Física: gravidade e solo ──────────────────────
        # TRANSLAÇÃO: aplicar velocidade à posição (x, y)
        if not self.on_ground:
            self.vy += GRAVITY

        self.x += self.vx
        self.y += self.vy

        # Aterrissar
        if self.y >= FLOOR_Y:
            self.y        = FLOOR_Y
            self.vy       = 0.0
            self.on_ground = True
            if self.state == STATE_JUMP:
                self.state = STATE_IDLE

        # Limites horizontais da arena
        self.x = max(self.arena_left, min(self.arena_right - CHAR_W, self.x))

        # Atrito horizontal
        if self.on_ground:
            self.vx *= 0.75

        # ── Timers de estado e cooldown ───────────────────
        if self.state_timer > 0:
            self.state_timer -= 1
            if self.state_timer == 0 and self.is_attacking:
                self.state = STATE_IDLE

        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0 and self.state == STATE_HIT:
                self.state = STATE_IDLE

        if self.hitbox_timer > 0:
            self.hitbox_timer -= 1
        else:
            self.active_hitbox = None

        if self.cd_light  > 0: self.cd_light  -= 1
        if self.cd_medium > 0: self.cd_medium -= 1
        if self.cd_special > 0: self.cd_special -= 1

        # ── ESCALA: interpolação suave de volta a 1.0 ─────
        self.current_scale += (self.target_scale - self.current_scale) * 0.15
        if abs(self.current_scale - self.target_scale) < 0.005:
            if self.target_scale != 1.0:
                self.target_scale = 1.0   # volta ao normal após atingir o pico

    # ─────────────────────────────────────────────────────
    #  RENDERIZAÇÃO
    # ─────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        # ── ESCOLHER E CORTAR FRAME MANUAL ────────────────
        surf = None
        if self.current_anim_frames and len(self.current_anim_frames) > 0:
            surf = self.current_anim_frames[self.frame_index]
        
        # Fallback se não tiver sprite animado
        if surf is None:
            surf = self.sprite_base

        # ── ESCALA: redimensionar proporcional ────────────
        valid_anim = self.current_anim_frames and len(self.current_anim_frames) > 0
        if valid_anim:
            factor = self.sprite_scale_factor * self.current_scale
            sw = int(surf.get_width() * factor)
            sh = int(surf.get_height() * factor)
        else:
            sc  = self.current_scale
            sw  = int(CHAR_W * sc)
            sh  = int(CHAR_H * sc)
            
        scaled_surf = pygame.transform.scale(surf, (sw, sh))

        # ── REFLEXÃO: espelhar se virado para esquerda ────
        if not self.facing_right:
            scaled_surf = pygame.transform.flip(scaled_surf, True, False)

        # Piscar em vermelho ao tomar dano
        if self.hit_timer > 0 and (self.hit_timer // 3) % 2 == 0:
            tint = pygame.Surface((sw, sh), pygame.SRCALPHA)
            tint.fill((255, 50, 50, 120))
            scaled_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Aura dourada no especial
        if self.state == STATE_ATTACK_S:
            aura = pygame.Surface((sw + 40, sh + 40), pygame.SRCALPHA)
            alpha = int(60 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.ellipse(aura, (*self.color, alpha),
                                (0, 0, sw + 40, sh + 40))
            screen.blit(aura, (int(self.x) - 20, int(self.y) - sh - 20))

        # Posicionar sprite (pés ancorados no piso, X centralizado)
        draw_x = int(self.x) + (CHAR_W - sw) // 2
        draw_y = int(self.y) - sh
        screen.blit(scaled_surf, (draw_x, draw_y))

        # Sombra no chão
        shadow = pygame.Surface((max(CHAR_W, sw - 10), 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, max(CHAR_W, sw - 10), 10))
        sh_x = int(self.x) + (CHAR_W - shadow.get_width()) // 2
        screen.blit(shadow, (sh_x, int(self.y) - 4))

        # Debug: hitbox ativa (descomente para ver)
        # if self.active_hitbox:
        #     pygame.draw.rect(screen, (255, 0, 0), self.active_hitbox, 2)

    def draw_name_tag(self, screen, font, side="left"):
        """Exibe nome acima do personagem."""
        txt   = font.render(self.name, True, self.color)
        tag_x = int(self.x) + CHAR_W // 2 - txt.get_width() // 2
        tag_y = int(self.y) - CHAR_H - 22
        screen.blit(txt, (tag_x, tag_y))
