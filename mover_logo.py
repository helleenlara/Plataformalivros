import os
import shutil

# Caminho da imagem renomeada
imagem_original = r"C:\Users\fabio\Downloads\logo_litme.jpg"

# Cria a pasta static se ela não existir
if not os.path.isdir("static"):
    os.mkdir("static")

# Copia a imagem para a pasta static com o nome certo
shutil.copy(imagem_original, "static/logo_litme.jpg")

print("✅ Imagem copiada com sucesso para static/logo_litme.jpg!")
