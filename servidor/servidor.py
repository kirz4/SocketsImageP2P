import socket

SERVER_IP = "0.0.0.0"
SERVER_PORT = 13377

clientes = []
imagens_compartilhadas = {}

def encontrar_cliente(ip, porta):
    for c in clientes:
        if c["ip"] == ip and c["porta"] == porta:
            return c
    return None

def registrar_cliente(senha, ip, porta, imagens):
    if not senha or not porta or not imagens:
        return "ERR INVALID_MESSAGE_FORMAT"

    imagens_validas = []
    for img in imagens:
        if "," not in img:
            return "ERR INVALID_MESSAGE_FORMAT"
        md5, nome = img.split(",", 1)
        if len(md5) != 32:
            return "ERR INVALID_MESSAGE_FORMAT"
        imagens_validas.append((md5, nome))

    # Se já existe cliente com este IP e porta, remove-o antes (re-registro)
    cliente_existente = encontrar_cliente(ip, porta)
    if cliente_existente:
        clientes.remove(cliente_existente)
        # Remove associações antigas
        for md5, info in list(imagens_compartilhadas.items()):
            if f"{ip}:{porta}" in info["clientes"]:
                info["clientes"].remove(f"{ip}:{porta}")
                if not info["clientes"]:
                    del imagens_compartilhadas[md5]

    cliente = {"ip": ip, "porta": porta, "senha": senha}
    clientes.append(cliente)

    for md5, nome in imagens_validas:
        if md5 not in imagens_compartilhadas:
            imagens_compartilhadas[md5] = {"nome": nome, "clientes": []}
        if f"{ip}:{porta}" not in imagens_compartilhadas[md5]["clientes"]:
            imagens_compartilhadas[md5]["clientes"].append(f"{ip}:{porta}")

    return f"OK {len(imagens_validas)}_REGISTERED_IMAGES"

def atualizar_registro(senha, ip, porta, imagens):
    cliente = encontrar_cliente(ip, porta)
    if not cliente or cliente["senha"] != senha:
        return "ERR IP_REGISTERED_WITH_DIFFERENT_PASSWORD"

    imagens_validas = []
    for img in imagens:
        if "," not in img:
            return "ERR INVALID_MESSAGE_FORMAT"
        md5, nome = img.split(",", 1)
        if len(md5) != 32:
            return "ERR INVALID_MESSAGE_FORMAT"
        imagens_validas.append((md5, nome))

    # Remove imagens antigas deste cliente
    for md5, info in list(imagens_compartilhadas.items()):
        if f"{ip}:{porta}" in info["clientes"]:
            info["clientes"].remove(f"{ip}:{porta}")
            if not info["clientes"]:
                del imagens_compartilhadas[md5]

    # Adiciona novas imagens
    for md5, nome in imagens_validas:
        if md5 not in imagens_compartilhadas:
            imagens_compartilhadas[md5] = {"nome": nome, "clientes": []}
        imagens_compartilhadas[md5]["clientes"].append(f"{ip}:{porta}")

    return f"OK {len(imagens_validas)}_REGISTERED_FILES"

def listar_imagens():
    if not imagens_compartilhadas:
        return "ERR NO_IMAGES_AVAILABLE"
    lista = []
    for md5, info in imagens_compartilhadas.items():
        linha = f"{md5},{info['nome']}"
        for cli in info["clientes"]:
            linha += f",{cli}"
        lista.append(linha)
    return ";".join(lista)

def desconectar_cliente(senha, ip, porta):
    cliente = encontrar_cliente(ip, porta)
    if not cliente or cliente["senha"] != senha:
        return "ERR IP_REGISTERED_WITH_DIFFERENT_PASSWORD"

    clientes.remove(cliente)
    for md5, info in list(imagens_compartilhadas.items()):
        if f"{ip}:{porta}" in info["clientes"]:
            info["clientes"].remove(f"{ip}:{porta}")
            if not info["clientes"]:
                del imagens_compartilhadas[md5]

    return "OK CLIENT_FINISHED"

def main():
    print("[LOG] Servidor iniciado...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((SERVER_IP, SERVER_PORT))
        print(f"[LOG] Servidor rodando na porta {SERVER_PORT}...")

        while True:
            data, addr = server.recvfrom(4096)
            msg = data.decode().strip()
            resposta = "ERR INVALID_MESSAGE_FORMAT"

            try:
                partes = msg.split(" ", 3)
                cmd = partes[0]

                if cmd == "REG":
                    # REG <SENHA> <PORTA> <IMAGENS>
                    if len(partes) == 4:
                        senha = partes[1]
                        porta = int(partes[2])
                        imagens_str = partes[3]
                        imagens_lista = imagens_str.split(";")
                        resposta = registrar_cliente(senha, addr[0], porta, imagens_lista)
                    else:
                        resposta = "ERR INVALID_MESSAGE_FORMAT"

                elif cmd == "UPD":
                    # UPD <SENHA> <PORTA> <IMAGENS>
                    if len(partes) == 4:
                        senha = partes[1]
                        porta = int(partes[2])
                        imagens_str = partes[3]
                        imagens_lista = imagens_str.split(";")
                        resposta = atualizar_registro(senha, addr[0], porta, imagens_lista)
                    else:
                        resposta = "ERR INVALID_MESSAGE_FORMAT"

                elif cmd == "LST":
                    if len(partes) == 1:
                        resposta = listar_imagens()
                    else:
                        resposta = "ERR INVALID_MESSAGE_FORMAT"

                elif cmd == "END":
                    # END <SENHA> <PORTA>
                    if len(partes) == 3:
                        senha = partes[1]
                        porta = int(partes[2])
                        resposta = desconectar_cliente(senha, addr[0], porta)
                    else:
                        resposta = "ERR INVALID_MESSAGE_FORMAT"
                else:
                    resposta = "ERR INVALID_MESSAGE_FORMAT"

            except Exception as e:
                print("[ERRO]", e)
                resposta = "ERR INVALID_MESSAGE_FORMAT"

            server.sendto(resposta.encode(), addr)

if __name__ == "__main__":
    main()
