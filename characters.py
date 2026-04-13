# ============================================================
#  characters.py
#  Define os dados de todos os personagens e inimigos do jogo.
#  NÃO contém lógica de jogo, apenas as fichas dos lutadores.
# ============================================================

import os
_DIR = os.path.dirname(os.path.abspath(__file__))

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
        "id":    "ichigo",
        "name":  "ICHIGO KUROSAKI",
        "title": "Shinigami Substituto",
        "hp":    110,
        "speed": 6,
        "style": "Zangetsu",
        "desc": "Um humano com poderes de Shinigami e sua Katana Zangetsu.",
        "color": (255, 100, 0),
        "sprite": "assets/characters/ichigo.png",
        "anim_folder": os.path.join(_DIR, "sprites", "ichigo"),
        "colorkey": (0, 128, 0),
        "sprite_scale": 1.6,
        "light":   {"name": "Corte Rápido",    "damage": 10, "cooldown": 20, "range": 90},
        "medium":  {"name": "Corte Preciso",   "damage": 18, "cooldown": 35, "range": 100},
        "special": {"name": "Getsuga Tenshou", "damage": 35, "cooldown": 75, "range": 220,
                    "projectile": True},
    },
    {
        "id":    "luffy",
        "name":  "MONKEY D LUFFY",
        "title": "CHÁPEU DE PALHA",
        "hp":    100,
        "speed": 8,
        "style": "Nika",
        "desc": "Um pirata que sonha em ser o Rei dos Piratas.",
        "color": (80, 160, 255),
        "sprite": "assets/characters/raikiri.png",
        "anim_folder": os.path.join(_DIR, "sprites", "luffy"),
        "sprite_scale": 1.5,
        "light":   {"name": "Gomu Gomu no Pistol",    "damage": 8,  "cooldown": 20, "range": 80},
        "medium":  {"name": "Gomu Gomu no Gatling",    "damage": 15, "cooldown": 35, "range": 90},
        "special": {"name": "Gomu Gomu no Elephant Pistol", "damage": 28, "cooldown": 70, "range": 200,
                    "projectile": True},
    },
    {
        "id":    "naruto",
        "name":  "NARUTO",
        "title": "Ninja da Aldeia da Folha",
        "hp":    100,
        "speed": 8,
        "style": "Hokage",
        "desc": "Um ninja hiperativo e obstinado da Vila Secreta da Folha.",
        "color": (255, 120, 20),
        "sprite": "assets/characters/naruto.png",
        "anim_folder": os.path.join(_DIR, "sprites", "naruto"),
        "colorkey": (0, 64, 128),  
        "sprite_scale": 1.5,
        "light":   {"name": "Combo Taijutsu", "damage": 8,  "cooldown": 18, "range": 85},
        "medium":  {"name": "Rasengan",       "damage": 16, "cooldown": 32, "range": 105},
        "special": {"name": "Ninja Laser",   "damage": 30, "cooldown": 75, "range": 220,
                    "projectile": True, "is_beam": True},
    },
    {
        "id":    "uchiha_sasuke",
        "name":  "UCHIHA SASUKE",
        "title": "O último Uchiha",
        "hp":    130,
        "speed": 8,
        "style": "Sharingan",
        "desc": "Um ninja prodígio e vingativo, obcecado em restaurar a honra de seu clã.",
        "color": (255, 100, 40),
        "sprite": "assets/characters/sasuke.png",
        "anim_folder": os.path.join(_DIR, "sprites", "sasuke"),
        "light":   {"name": "Soco Pesado",      "damage": 12, "cooldown": 28, "range": 85},
        "medium":  {"name": "Chama Dracônica",  "damage": 20, "cooldown": 42, "range": 95},
        "special": {"name": "Rugido do Dragão", "damage": 35, "cooldown": 80, "range": 240,
                    "projectile": True},
    },
    {
        "id":    "zoro",
        "name":  "RORONOA ZORO",
        "title": "O Caçador de Piratas",
        "hp":    120,
        "speed": 6,
        "style": "Santoryu",
        "desc": "Espadachim que quer se tornar o melhor espadachim do mundo.",
        "color": (50, 150, 50),
        "sprite": "assets/characters/zoro.png",
        "anim_folder": os.path.join(_DIR, "sprites", "roronoa zoro"),
        "light":   {"name": "Corte Simples",  "damage": 10, "cooldown": 25, "range": 95},
        "medium":  {"name": "Onigiri",        "damage": 22, "cooldown": 40, "range": 110},
        "special": {"name": "Sanzen Sekai",   "damage": 40, "cooldown": 80, "range": 230,
                    "projectile": True},
    },
    {
        "id":    "zaraki",
        "name":  "ZARAKI KENPACHI",
        "title": "Capitão do 11º Esquadrão",
        "hp":    110,
        "speed": 8,
        "style": "Bruto",
        "desc": "Um guerreiro sanguinário que vive apenas para lutar.",
        "color": (200, 200, 50),
        "sprite": "assets/characters/zaraki.png",
        "anim_folder": os.path.join(_DIR, "sprites", "kenpachi zaraki"),
        "light":   {"name": "Talho Grosseiro", "damage": 15, "cooldown": 30, "range": 100},
        "medium":  {"name": "Corte Brutal",    "damage": 25, "cooldown": 45, "range": 110},
        "special": {"name": "Pressão Espiritual","damage": 45, "cooldown": 85, "range": 200,
                    "projectile": True},
    },

]

# Inimigos das 3 fases — usam a MESMA estrutura de personagem
# A IA instancia Character com esses dados, reutilizando todo o sistema de combate
ENEMIES = [
    {   # Fase 1 — inimigo mais fraco
        "id":    "sosuke_aizen",
        "name":  "SOSUKE AIZEN",
        "title": "Capitão da 5ª Divisão",
        "hp":    90,
        "speed": 4,
        "color": (220, 40, 40),
        "sprite": "assets/characters/sosuke_aizen.png",
        "anim_folder": os.path.join(_DIR, "sprites", "aizen"),
        "light":   {"name": "Corte Ilusório",   "damage": 10, "cooldown": 30, "range": 85},
        "medium":  {"name": "Kurohitsugi",      "damage": 18, "cooldown": 45, "range": 120},
        "special": {"name": "Kyoka Suigetsu",   "damage": 30, "cooldown": 90, "range": 200, "projectile": True},
        "ai_aggression": 0.4,   # probabilidade de atacar por frame quando perto
        "ai_attack_range": 110, # distância para começar a atacar
    },
    {   # Fase 2 — intermediário
        "id":    "uzumaki_nagato",
        "name":  "PAIN",
        "title": "Líder da Akatsuki",
        "hp":    110,
        "speed": 5,
        "color": (80, 80, 160),
        "sprite": "assets/characters/pain.png",
        "anim_folder": os.path.join(_DIR, "sprites", "pain"),
        "light":   {"name": "Banshō Ten'in",   "damage": 12, "cooldown": 25, "range": 100},
        "medium":  {"name": "Shinra Tensei",   "damage": 20, "cooldown": 40, "range": 140},
        "special": {"name": "Chibaku Tensei",  "damage": 33, "cooldown": 80, "range": 230, "projectile": True},
        "ai_aggression": 0.6,
        "ai_attack_range": 120,
    },
    {   # Fase 3 — chefe final
        "id":    "donquixote_doflamingo",
        "name":  "DONQUIXOTE DOFLAMINGO",
        "title": "Joker",
        "hp":    150,
        "speed": 6,
        "color": (255, 50, 200),
        "sprite": "assets/characters/donquixote_doflamingo.png",
        "anim_folder": os.path.join(_DIR, "sprites", "donquixote doflamingo"),
        "light":   {"name": "Chute Afiado",   "damage": 14, "cooldown": 22, "range": 95},
        "medium":  {"name": "Goshikito",      "damage": 24, "cooldown": 38, "range": 130},
        "special": {"name": "Torikago",       "damage": 40, "cooldown": 75, "range": 240, "projectile": True},
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
        "name":       "Templo Uchiha",
        "background": "assets/backgrounds/fase 2.png",
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
