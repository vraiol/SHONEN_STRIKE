import cv2
import numpy as np
import os
import shutil

_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Coloque o nome EXATO da imagem que está na pasta "sprites base dos personagens"
NOME_DO_ARQUIVO = "Roronoa zoro.png"

# O código cria a pasta com o mesmo nome automaticamente
NOME_PERSONAGEM = os.path.splitext(NOME_DO_ARQUIVO)[0].lower()
ARQUIVO_IMAGEM = os.path.join(_DIR, 'assets', 'characters', 'sprites base dos personagens', NOME_DO_ARQUIVO)
PASTA_SAIDA = os.path.join(_DIR, "assets", "characters", NOME_PERSONAGEM)
MIN_WIDTH, MIN_HEIGHT = 15, 15

# Usado para controle interno de qual animação recebe "2 pastas seguidas" etc.
contadores_pastas = {}

def recortar_interativo():
    if not os.path.exists(ARQUIVO_IMAGEM):
        print(f"Erro: Arquivo não encontrado - {ARQUIVO_IMAGEM}")
        return

    print("Carregando imagem...")
    img = cv2.imread(ARQUIVO_IMAGEM, cv2.IMREAD_UNCHANGED)
    
    # Auto-detectar a cor de fundo (pega a cor do pixel do canto superior esquerdo)
    bg_color = img[0, 0, :3]
    print(f"Cor de fundo detectada: {bg_color}")
    
    lower_bound = np.clip(bg_color.astype(int) - 10, 0, 255).astype(np.uint8)
    upper_bound = np.clip(bg_color.astype(int) + 10, 0, 255).astype(np.uint8)
    
    mask = cv2.inRange(img[:,:,:3], lower_bound, upper_bound)
    mask_inv = cv2.bitwise_not(mask)
    contours, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_bboxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w >= MIN_WIDTH and h >= MIN_HEIGHT:
            valid_bboxes.append([x, y, w, h])

    bboxes_com_centro = []
    for x, y, w, h in valid_bboxes:
        cy = y + h / 2.0
        bboxes_com_centro.append((cy, x, y, w, h))
    bboxes_com_centro.sort(key=lambda item: item[0])

    linhas = []
    linha_atual = []
    centro_medio_atual = -1

    for cy, x, y, w, h in bboxes_com_centro:
        if centro_medio_atual == -1:
            linha_atual.append([x, y, w, h])
            centro_medio_atual = cy
            continue
        if abs(cy - centro_medio_atual) <= 90:
            linha_atual.append([x, y, w, h])
            centro_medio_atual = (centro_medio_atual * (len(linha_atual)-1) + cy) / len(linha_atual)
        else:
            linhas.append(linha_atual)
            linha_atual = [[x, y, w, h]]
            centro_medio_atual = cy
            
    if linha_atual:
        linhas.append(linha_atual)

    print(f"\nA imagem possui {len(linhas)} linhas/movimentos!")
    print("Preste atenção na JANELA QUE VAI ABRIR (não no terminal).")
    print("Aperte os números no seu teclado:")
    print("1 = stance | 2 = run | 3 = jump | 4 = attack combo | 5 = special movie | 6 = taking damage | 7 = introduction")
    print("Espaço (ou qualquer outra tecla) = Ignorar e pular para o próximo")

    for index_linha, bboxes_na_linha in enumerate(linhas):
        bboxes_na_linha.sort(key=lambda b: b[0])
        
        # Cria uma colagem com espaço extra em cima para o texto
        altura_max = max(b[3] for b in bboxes_na_linha)
        # Mostramos até 25 frames (quase todos) para você ter certeza que pegou tudo!
        largura_total = max(800, sum(b[2] for b in bboxes_na_linha[:25])) 
        preview = np.zeros((altura_max + 60, largura_total, 3), dtype=np.uint8)
        
        # Coloca o texto de instrução diretamente na janela
        cv2.putText(preview, "1:stance | 2:run | 3:jump | 4:attack | 5:special | 6:damage | 7:intro | Outra: PULAR", 
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(preview, f"Linha {index_linha + 1}/{len(linhas)} - ({len(bboxes_na_linha)} sprites encontrados)", 
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        offset_x = 0
        for x, y, w, h in bboxes_na_linha[:25]:
            frame = img[y:y+h, x:x+w, :3]
            preview[60:60+h, offset_x:offset_x+w] = frame
            offset_x += w
            
        cv2.imshow("Recorte Interativo", preview)
        
        # Pega a tecla digitada diretamente na janela (evita o "Não Responde" do Windows)
        tecla = cv2.waitKey(0) 
        
        nome_pasta = ""
        if tecla == ord('1'): nome_pasta = "stance"
        elif tecla == ord('2'): nome_pasta = "run"
        elif tecla == ord('3'): nome_pasta = "jump"
        elif tecla == ord('4'): nome_pasta = "attack combo"
        elif tecla == ord('5'): nome_pasta = "special movie"
        elif tecla == ord('6'): nome_pasta = "taking damage"
        elif tecla == ord('7'): nome_pasta = "introduction"
        
        if nome_pasta == "":
            print(f"[{index_linha + 1}] -> Ignorado!")
            continue
            
        path_completo = os.path.join(PASTA_SAIDA, nome_pasta)
        os.makedirs(path_completo, exist_ok=True)
        
        if nome_pasta not in contadores_pastas:
            contadores_pastas[nome_pasta] = 0
            
        for x, y, w, h in bboxes_na_linha:
            numero_frame = contadores_pastas[nome_pasta]
            sprite_crop = img[y:y+h, x:x+w]
            caminho_arquivo = os.path.join(path_completo, f"{numero_frame}.png")
            cv2.imwrite(caminho_arquivo, sprite_crop)
            contadores_pastas[nome_pasta] += 1
            
        print(f" -> Salvo na pasta {nome_pasta}!\n")

    try:
        cv2.destroyAllWindows()
    except:
        pass
    print("\nPROCESSO FINALIZADO COM SUCESSO! Todas as pastas estão perfeitas.")

if __name__ == "__main__":
    recortar_interativo()
