# ============================================================
#  main.py
#  Controlador geral do jogo.
#  Orquestra: menu → seleção → lutas → vitória/derrota
#
#  Transformações geométricas implementadas:
#    TRANSLAÇÃO  → character.py  (move_left, move_right, jump, física)
#    REFLEXÃO    → character.py  (facing_right + transform.flip)
#    ESCALA      → character.py  (especial), fight.py (KO/countdown),
#                  menu.py (títulos pulsantes), character_select.py
#    ROTAÇÃO     → combat.py     (projéteis giram via transform.rotate),
#                  menu.py       (orbes decorativos)
# ============================================================

import pygame
import sys
import os

# Garantir que o diretório do script esteja no path
sys.path.insert(0, os.path.dirname(__file__))

from characters       import CHARACTERS, ENEMIES, STAGES
from character        import Character
from character_select import run_selection
from menu             import show_main_menu, show_victory, show_defeat
from fight            import FightScreen

SW, SH = 1000, 620


def make_character(data: dict, x: float, facing_right: bool) -> Character:
    """Instancia um Character a partir dos dados do dicionário."""
    ch = Character(data, x, facing_right)
    return ch


def reset_character(ch: Character, data: dict, x: float, facing_right: bool):
    """Reseta HP e posição de um personagem para nova luta."""
    ch.hp             = data["hp"]
    ch.x              = float(x)
    ch.facing_right   = facing_right
    ch.state          = "idle"
    ch.state_timer    = 0
    ch.cd_light       = 0
    ch.cd_medium      = 0
    ch.cd_special     = 0
    ch.active_hitbox  = None
    ch.hit_timer      = 0
    ch.dead_timer     = 0
    ch.current_scale  = 1.0
    ch.target_scale   = 1.0
    ch.vx = ch.vy     = 0.0
    ch.on_ground      = True


def main():
    pygame.init()
    screen = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption("Anime Fighters")
    clock  = pygame.time.Clock()

    # Criar pasta de assets se não existir (para evitar erros)
    for folder in ["assets/characters", "assets/backgrounds", "assets/effects"]:
        os.makedirs(folder, exist_ok=True)

    total_phases = len(ENEMIES)

    while True:
        # ── MENU PRINCIPAL ────────────────────────────────
        action = show_main_menu(screen, clock)
        if action == "quit":
            pygame.quit()
            sys.exit()

        # ── SELEÇÃO DE PERSONAGEM ─────────────────────────
        chosen_idx = run_selection(screen, clock)
        if chosen_idx is None:
            continue   # voltou ao menu principal

        player_data = CHARACTERS[chosen_idx]

        # ── CAMPANHA: 3 FASES ─────────────────────────────
        fight_screen = FightScreen(screen, clock)
        phase        = 1
        retry_phase  = phase

        while phase <= total_phases:
            enemy_data  = ENEMIES[phase - 1]
            stage_data  = STAGES[phase - 1]

            # Adicionar dados de IA no stage_data para o FightScreen
            stage_data["ai_aggression"]  = enemy_data.get("ai_aggression",  0.5)
            stage_data["ai_attack_range"]= enemy_data.get("ai_attack_range", 110)

            # Instanciar personagens frescos para cada luta
            player = make_character(player_data, 150.0, True)
            enemy  = make_character(enemy_data,  SW - 150.0 - 64, False)

            # ── LUTA ──────────────────────────────────────
            result = fight_screen.run(
                player, enemy, stage_data, phase, total_phases)

            if result == "quit":
                break

            # ── RESULTADO ─────────────────────────────────
            if result == "player_win":
                action = show_victory(
                    screen, clock,
                    winner_name  = player_data["name"],
                    phase        = phase,
                    total_phases = total_phases)

                if action == "continue":
                    phase += 1
                else:
                    break   # voltar ao menu

            elif result == "enemy_win":
                action = show_defeat(
                    screen, clock,
                    loser_name = player_data["name"])

                if action == "retry":
                    continue   # rlutar a mesma fase novamente
                else:
                    break   # voltar ao menu

        # Fim da campanha ou saída → volta ao while True externo (menu)


if __name__ == "__main__":
    main()
