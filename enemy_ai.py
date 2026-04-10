# ============================================================
#  enemy_ai.py
#  Controlador de IA para os inimigos.
#  A IA usa EXATAMENTE os mesmos métodos de Character
#  que o jogador humano usa — apenas a ativação é diferente.
# ============================================================

import random
from character import Character, STATE_DEAD, STATE_HIT, CHAR_W


class EnemyAI:
    """
    Controla um Character como inimigo.
    NÃO possui ataques exclusivos — usa attack_light(),
    attack_medium() e attack_special() da classe Character.
    """

    def __init__(self, character: Character, aggression: float = 0.5,
                 attack_range: int = 110):
        self.char        = character
        self.aggression  = aggression   # 0.0–1.0: frequência de ataque
        self.attack_range = attack_range

        # Timer interno de "pensar" (evita decisões a cada frame)
        self.think_timer  = 0
        self.think_delay  = 20          # frames entre decisões
        self.idle_timer   = 0           # pausa antes de avançar

    # ─────────────────────────────────────────────────────
    #  UPDATE — chamado a cada frame pelo game loop
    # ─────────────────────────────────────────────────────

    def update(self, player: Character, combat_manager):
        """
        Atualiza IA: decide movimento e ataque com base
        na posição do jogador e nos cooldowns do personagem.
        """
        enemy = self.char

        if not enemy.alive or enemy.state == STATE_DEAD:
            return

        # Não agir enquanto tomando dano
        if enemy.state == STATE_HIT:
            return

        # Congelar a IA inimiga se o jogador estiver usando o especial (Cinematic Wait)
        if player.state == "attack_special":
            enemy.stop_horizontal()
            return

        # ── Timer de raciocínio ────────────────────────
        self.think_timer += 1
        if self.think_timer < self.think_delay:
            self._execute_movement(player)
            return
        self.think_timer = 0

        # Calcular distância até o jogador
        dist_x = player.center_x - enemy.center_x
        dist   = abs(dist_x)

        # ── REFLEXÃO: virar para o jogador ────────────
        # (chama move_left/move_right indiretamente para atualizar facing)
        if dist_x < 0:
            enemy.facing_right = False
        else:
            enemy.facing_right = True

        # ── Decidir ação ──────────────────────────────
        if dist <= self.attack_range:
            self._decide_attack(dist, combat_manager)
        else:
            self._decide_movement(player, dist_x)

    # ─────────────────────────────────────────────────────
    #  MOVIMENTO (TRANSLAÇÃO)
    # ─────────────────────────────────────────────────────

    def _decide_movement(self, player: Character, dist_x: float):
        """
        TRANSLAÇÃO: mover o inimigo em direção ao jogador.
        Usa os mesmos métodos move_left/move_right do Character.
        """
        enemy = self.char

        # Pausa ocasional para parecer mais natural
        if self.idle_timer > 0:
            self.idle_timer -= 1
            enemy.stop_horizontal()
            return

        if random.random() < 0.05:
            self.idle_timer = random.randint(10, 25)
            return

        # Aproximar do jogador
        if dist_x < 0:
            enemy.move_left()
        else:
            enemy.move_right()

    def _execute_movement(self, player: Character):
        """Executa o movimento decidido anteriormente (entre frames de decisão)."""
        enemy  = self.char
        dist_x = player.center_x - enemy.center_x
        dist   = abs(dist_x)

        if self.idle_timer > 0:
            self.idle_timer -= 1
            enemy.stop_horizontal()
            return

        if dist > self.attack_range:
            if dist_x < 0:
                enemy.move_left()
            else:
                enemy.move_right()
        else:
            enemy.stop_horizontal()

    # ─────────────────────────────────────────────────────
    #  DECISÃO DE ATAQUE
    #  Usa EXATAMENTE os mesmos métodos do personagem jogável
    # ─────────────────────────────────────────────────────

    def _decide_attack(self, dist: int, combat_manager):
        """
        Escolhe aleatoriamente entre os 3 ataques do personagem.
        Respeita cooldowns (attack_* retorna False se em cooldown).
        A probabilidade de atacar é controlada por self.aggression.
        """
        enemy = self.char

        if enemy.is_attacking:
            return

        # Probabilidade de tentar atacar neste frame de decisão
        if random.random() > self.aggression:
            enemy.stop_horizontal()
            return

        # Pesos: especial mais raro, leve mais frequente
        roll = random.random()

        if roll < 0.15:
            if enemy.attack_special():
                return

        if roll < 0.45:
            # Golpe médio (30%)
            enemy.attack_medium()
            return

        # Golpe leve (55%)
        enemy.attack_light()

    # ─────────────────────────────────────────────────────
    #  AUMENTAR DIFICULDADE
    # ─────────────────────────────────────────────────────

    def increase_difficulty(self):
        """
        Chamado ao avançar de fase.
        Aumenta agressividade e reduz intervalo de pensamento.
        """
        self.aggression   = min(0.95, self.aggression + 0.2)
        self.think_delay  = max(8,    self.think_delay  - 4)
        self.attack_range = min(160,  self.attack_range + 15)
