# ============================================================
#  characters.py
#  Define os dados de todos os personagens e inimigos do jogo.
#  NÃO contém lógica de jogo, apenas as fichas dos lutadores.
# ============================================================

# Cada personagem possui:
#   name       → nome de exibição
#   hp         → vida máxima
#   speed      → velocidade de movimento (pixels/frame)
#   color      → cor representativa (usada como fallback sem sprite)
#   sprite     → caminho para sprite sheet ou imagem estática
#   light      → golpe leve   { damage, cooldown, range, name }
#   medium     → golpe médio  { damage, cooldown, range, name }
#   special    → golpe especial { damage, cooldown, range, name, projectile }

CHARACTERS = [
    {
        "id":    "raikiri",
        "name":  "RAIKIRI",
        "title": "O Relâmpago",
        "hp":    100,
        "speed": 5,
        "style": "Ninjutsu Elétrico",
        "desc": "Velocidade acima de tudo. Golpes rápidos e devastadores.",
        "color": (80, 160, 255),
        "sprite": "assets/characters/raikiri.png",
        "light":   {"name": "Corte Rápido",    "damage": 8,  "cooldown": 20, "range": 80},
        "medium":  {"name": "Palma Trovão",    "damage": 15, "cooldown": 35, "range": 90},
        "special": {"name": "Relâmpago Duplo", "damage": 28, "cooldown": 70, "range": 200,
                    "projectile": True},
    },
    {
        "id":    "naruto",
        "name":  "NARUTO",
        "title": "Ninja da Aldeia da Folha",
        "hp":    100,
        "speed": 8,
        "style": "Hokage",
        "desc": "Um ninja hiperativo e obstinado da Vila da Folha Secreta.",
        "color": (255, 120, 20),
        "sprite": "assets/characters/naruto.png",
        "anim_folder": "assets/characters/naruto",
        "colorkey": (0, 64, 138),  # Ajuste essa cor para remover o fundo azul das imagens nas pastas
        "sprite_scale": 1.5,
        "light":   {"name": "Combo Taijutsu", "damage": 8,  "cooldown": 18, "range": 85},
        "medium":  {"name": "Rasengan",       "damage": 16, "cooldown": 32, "range": 105},
        "special": {"name": "Ninja Laser",   "damage": 30, "cooldown": 75, "range": 220,
                    "projectile": True, "is_beam": True},
    },
    {
        "id":    "ryujin",
        "name":  "RYUJIN",
        "title": "Senhor dos Dragões",
        "hp":    130,
        "speed": 3,
        "style": "Punho do Dragão",
        "desc": "Força bruta incomparável. Cada golpe abala o campo de batalha.",
        "color": (255, 100, 40),
        "sprite": "assets/characters/ryujin.png",
        "light":   {"name": "Soco Pesado",      "damage": 12, "cooldown": 28, "range": 85},
        "medium":  {"name": "Chama Dracônica",  "damage": 20, "cooldown": 42, "range": 95},
        "special": {"name": "Rugido do Dragão", "damage": 35, "cooldown": 80, "range": 240,
                    "projectile": True},
    },
    {
        "id":    "tsukikage",
        "name":  "TSUKIKAGE",
        "title": "Sombra da Lua",
        "hp":    110,
        "speed": 4,
        "style": "Espada da Lua",
        "desc": "Espadachim de equilíbrio perfeito entre ataque e defesa.",
        "color": (200, 220, 255),
        "sprite": "assets/characters/tsukikage.png",
        "light":   {"name": "Corte Lunar",   "damage": 10, "cooldown": 22, "range": 90},
        "medium":  {"name": "Dança da Lua",  "damage": 17, "cooldown": 38, "range": 100},
        "special": {"name": "Eclipse Total", "damage": 32, "cooldown": 72, "range": 210,
                    "projectile": True},
    },
    {
        "id":    "araumi",
        "name":  "ARAUMI",
        "title": "Tempestade do Mar",
        "hp":    120,
        "speed": 4,
        "style": "Punho do Mar",
        "desc": "Resistência lendária. Quanto mais apanha, mais forte fica.",
        "color": (40, 200, 180),
        "sprite": "assets/characters/araumi.png",
        "light":   {"name": "Jab Veloz",       "damage": 9,  "cooldown": 19, "range": 78},
        "medium":  {"name": "Onda Brutal",      "damage": 16, "cooldown": 36, "range": 95},
        "special": {"name": "Tempestade Final", "damage": 33, "cooldown": 78, "range": 230,
                    "projectile": True},
    },
]

# Inimigos das 3 fases — usam a MESMA estrutura de personagem
# A IA instancia Character com esses dados, reutilizando todo o sistema de combate
ENEMIES = [
    {   # Fase 1 — inimigo mais fraco
        "id":    "oni_vermelho",
        "name":  "ONI VERMELHO",
        "title": "Guardião da Fase 1",
        "hp":    90,
        "speed": 3,
        "color": (220, 40, 40),
        "sprite": "assets/characters/oni_vermelho.png",
        "light":   {"name": "Soco do Oni",    "damage": 10, "cooldown": 30, "range": 85},
        "medium":  {"name": "Chifrada",       "damage": 18, "cooldown": 45, "range": 95},
        "special": {"name": "Fogo do Inferno","damage": 30, "cooldown": 90, "range": 200,
                    "projectile": True},
        "ai_aggression": 0.4,   # probabilidade de atacar por frame quando perto
        "ai_attack_range": 110, # distância para começar a atacar
    },
    {   # Fase 2 — intermediário
        "id":    "samurai_sombra",
        "name":  "SAMURAI SOMBRA",
        "title": "Guardião da Fase 2",
        "hp":    110,
        "speed": 4,
        "color": (80, 80, 160),
        "sprite": "assets/characters/samurai_sombra.png",
        "light":   {"name": "Corte Sombrio",   "damage": 12, "cooldown": 25, "range": 90},
        "medium":  {"name": "Lâmina Dupla",    "damage": 20, "cooldown": 40, "range": 100},
        "special": {"name": "Tempestade Negra","damage": 33, "cooldown": 80, "range": 210,
                    "projectile": True},
        "ai_aggression": 0.6,
        "ai_attack_range": 120,
    },
    {   # Fase 3 — chefe final
        "id":    "dragao_negro",
        "name":  "DRAGÃO NEGRO",
        "title": "Chefe Final",
        "hp":    150,
        "speed": 5,
        "color": (160, 0, 220),
        "sprite": "assets/characters/dragao_negro.png",
        "light":   {"name": "Garra Negra",      "damage": 14, "cooldown": 22, "range": 95},
        "medium":  {"name": "Sopro Dracônico",  "damage": 24, "cooldown": 38, "range": 110},
        "special": {"name": "Apocalipse Negro", "damage": 40, "cooldown": 75, "range": 250,
                    "projectile": True},
        "ai_aggression": 0.8,
        "ai_attack_range": 130,
    },
]

# Cenários das fases
STAGES = [
    {
        "name":       "Templo das Chamas",
        "background": "assets/backgrounds/stage1.png",
        "floor_color": (80, 50, 30),
        "sky_color":   (40, 20, 10),
    },
    {
        "name":       "Floresta das Sombras",
        "background": "assets/backgrounds/stage2.png",
        "floor_color": (20, 40, 20),
        "sky_color":   (10, 15, 30),
    },
    {
        "name":       "Pico do Dragão",
        "background": "assets/backgrounds/stage3.png",
        "floor_color": (30, 30, 60),
        "sky_color":   (5,  5,  20),
    },
]
