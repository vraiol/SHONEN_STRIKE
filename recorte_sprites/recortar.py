import cv2
import numpy as np
import os

# 1. Carrega a imagem da sprite sheet
img = cv2.imread('sprites base dos personagens/Ichigo Kurosaki.png', cv2.IMREAD_UNCHANGED)

# 2. Define qual é a cor do fundo (verde). 
# No OpenCV, as cores são lidas em BGR (Azul, Verde, Vermelho).
# O verde puro seria algo próximo de [0, 255, 0], mas vamos criar uma margem.
lower_green = np.array([0, 100, 0])
upper_green = np.array([100, 255, 100])

# 3. Cria uma máscara ignorando o fundo verde
mask = cv2.inRange(img[:,:,:3], lower_green, upper_green)
mask_inv = cv2.bitwise_not(mask) # Inverte para pegar os personagens

# 4. Encontra os contornos de cada sprite
contours, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Pega as caixas de contorno e ordena da esquerda pra direita, cima para baixo
bounding_boxes = [cv2.boundingRect(c) for c in contours]
contours_ordenados = sorted(zip(contours, bounding_boxes), key=lambda b: (b[1][1] // 10, b[1][0]))

# 5. Salva cada sprite recortado na ordem certa
os.makedirs('frames ichigo', exist_ok=True)
for i, (contour, bbox) in enumerate(contours_ordenados):
    x, y, w, h = bbox
    
    # Ignora ruídos ou pixels soltos muito pequenos
    if w > 10 and h > 10:
        # Recorta a imagem
        sprite = img[y:y+h, x:x+w]
        
        # Salva na pasta frames
        caminho_frame = os.path.join('frames ichigo', f'ichigo_frame_{i}.png')
        cv2.imwrite(caminho_frame, sprite)

print("Recorte finalizado!")