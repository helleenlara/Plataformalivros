from pathlib import Path

# Lista de pastas que precisam do __init__.py
pastas = [
    "app",
    "app/pages",
    "app/services",
    "app/utils"
]

for pasta in pastas:
    caminho = Path(pasta) / "__init__.py"
    caminho.parent.mkdir(parents=True, exist_ok=True)  # Cria as pastas se não existirem
    caminho.touch(exist_ok=True)  # Cria o arquivo se não existir
    print(f"✅ Criado: {caminho}")
