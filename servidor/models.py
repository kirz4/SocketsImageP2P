from threading import Lock

clientes = {}  # {endereco: {"senha": ..., "porta": ..., "imagens": [...]}}
imagens = {}   # {md5: {"nome": ..., "clientes": [...]}}

lock = Lock()

def registrar_cliente(addr, senha, porta, imagens_cliente):
    """Registra um cliente e suas imagens."""
    with lock:
        clientes[addr] = {"senha": senha, "porta": porta, "imagens": imagens_cliente}
        for imagem in imagens_cliente:
            md5, nome = imagem.split(",")
            if md5 not in imagens:
                imagens[md5] = {"nome": nome, "clientes": []}
            imagens[md5]["clientes"].append(addr)
