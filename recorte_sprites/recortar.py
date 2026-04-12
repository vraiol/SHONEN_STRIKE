import cv2
import numpy as np
import os
_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Carrega a imagem da sprite sheet
img_path = os.path.join(_DIR, 'sprites base dos personagens', 'Sasuke.png')
img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

# 2. Define qual é a cor do fundo da sprite sheet.
# No OpenCV, as cores são lidas em BGR (Azul, Verde, Vermelho).

# --- OPÇÕES DE CORES (Descomente a que for usar e comente as outras) ---

# --------- VERMELHO (Atual) ---------
# lower_color = np.array([0, 0, 100])
# upper_color = np.array([100, 100, 255])

# --------- VERDE ---------
# lower_color = np.array([0, 100, 0])
# upper_color = np.array([100, 255, 100])

# --------- AZUL ---------
lower_color = np.array([100, 0, 0])
upper_color = np.array([255, 100, 100])

# --------- MAGENTA (Rosa Choque/Roxo) ---------
# lower_color = np.array([100, 0, 100])
# upper_color = np.array([255, 50, 255])

# --------- BRANCO ---------
# lower_color = np.array([200, 200, 200])
# upper_color = np.array([255, 255, 255])

# --------- PRETO ---------
# lower_color = np.array([0, 0, 0])
# upper_color = np.array([40, 40, 40])

# 3. Cria uma máscara ignorando a cor de fundo escolhida
mask = cv2.inRange(img[:,:,:3], lower_color, upper_color)
mask_inv = cv2.bitwise_not(mask) # Inverte para pegar os personagens

# 4. Encontra os contornos de cada sprite
contours, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Pega as caixas de contorno e ordena da esquerda pra direita, cima para baixo
bounding_boxes = [cv2.boundingRect(c) for c in contours]
contours_ordenados = sorted(zip(contours, bounding_boxes), key=lambda b: (b[1][1] // 10, b[1][0]))

# 5. Salva cada sprite recortado na ordem certa
out_dir = os.path.join(_DIR, 'frames sasuke')
os.makedirs(out_dir, exist_ok=True)
for i, (contour, bbox) in enumerate(contours_ordenados):
    x, y, w, h = bbox
    
    # Ignora ruídos ou pixels soltos muito pequenos
    if w > 10 and h > 10:
        # Recorta a imagem
        sprite = img[y:y+h, x:x+w]
        
        # Salva na pasta frames
        caminho_frame = os.path.join(out_dir, f'sasuke_frame_{i}.png')
        cv2.imwrite(caminho_frame, sprite)

print("Recorte finalizado!")