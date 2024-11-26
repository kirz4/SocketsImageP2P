import hashlib
import os

def calcular_md5(caminho):
    """Calcula o hash MD5 de um arquivo."""
    with open(caminho, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def listar_arquivos(diretorio):
    """Lista arquivos de um diretório."""
    return [os.path.join(diretorio, f) for f in os.listdir(diretorio) if os.path.isfile(os.path.join(diretorio, f))]
