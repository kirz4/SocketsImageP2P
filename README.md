# SocketsImageP2P

Este projeto implementa um sistema de compartilhamento de imagens P2P (peer-to-peer) baseado em sockets. Ele possui dois componentes principais:

1. **Servidor (server)**: Responsável por registrar clientes, manter a lista de imagens e seus respectivos donos, bem como responder a requisições simples como registro, listagem, atualização e desconexão. O servidor não envia nem recebe as imagens, apenas gerencia as informações de quais clientes possuem quais arquivos.

2. **Cliente (client)**: Conecta-se ao servidor, envia a lista de suas imagens para registro e, a partir da informação do servidor, pode conectar-se diretamente a outros clientes para fazer download de imagens. Cada cliente disponibiliza um pequeno servidor TCP interno para compartilhar suas imagens com outros clientes.
## Características

- **Protocolo simples**: As mensagens trocadas entre cliente e servidor utilizam UDP e seguem formatos específicos (REG, LST, UPD, END). Não é utilizado JSON, apenas strings simples conforme o enunciado do protocolo.
- **P2P verdadeiro**: O servidor não transfere imagens; ele apenas gerencia informações. A transferência de imagens ocorre entre clientes diretamente via TCP.
- **Detecção de imagens**: O cliente utiliza `imghdr` (biblioteca padrão do Python) para verificar se o arquivo é uma imagem antes de registrá-la.
- **Portas aleatórias**: O cliente obtém uma porta TCP livre automaticamente do sistema operacional.
- **Prevenção de sobrescrita**: Ao baixar uma imagem que já existe no diretório, o cliente renomeia o arquivo de destino para evitar corromper o arquivo original.
- **Arquitetura**:
  - Servidor: roda em UDP na porta 13377.
  - Cliente: escolhe dinamicamente uma porta TCP, registra-se no servidor, ouve conexões para envio de imagens e permite que o usuário interaja via menu para listar e baixar imagens.
## Requisitos

- Python 3.8 ou superior.
- Não é necessário instalar bibliotecas externas. O `imghdr` já faz parte da biblioteca padrão do Python (note que, embora o `imghdr` esteja deprecado em versões futuras do Python, ele ainda funciona no Python 3.11 e anteriores).

## Executando o Servidor

No diretório do `servidor`, execute:

```bash
python servidor.py 
```
Ou, conforme a sua configuração de Python, pode ser:

```bash
python3 servidor.py 
```

O servidor iniciará e ficará aguardando conexões na porta 13377 (UDP).


## Executando o Cliente

No diretório do `cliente`, execute:

```bash
python cliente.py <IP_SERVIDOR> <DIRETORIO_IMAGENS>
```
Por exemplo:

```bash
python cliente.py 127.0.0.1 C:\Users\Lucas\Pictures\imagi
```
- <IP_SERVIDOR> é o IP do servidor, por exemplo 127.0.0.1 se estiver tudo na mesma máquina.
- <DIRETORIO_IMAGENS> é o diretório local onde estão as imagens que o cliente quer compartilhar e onde também serão salvas as imagens baixadas.

## Ao iniciar, o cliente apresentará um menu interativo:

- Registrar no servidor
- Listar imagens
- Baixar imagens
- Atualizar registro
- Desconectar do servidor (END)
- Sair


## Fluxo de Operação

1. **Registrar no servidor**: O cliente enviará a lista das imagens no diretório especificado, junto com um hash MD5 de cada arquivo, e uma senha gerada automaticamente. O servidor responderá com `OK` se o registro for bem-sucedido.

2. **Listar imagens**: O cliente enviará `LST` ao servidor, que retornará a lista de imagens disponíveis na rede, incluindo os endereços (IP:PORTA) dos clientes que as possuem.

3. **Baixar imagens**: Ao escolher "Baixar imagens", o cliente obterá a lista do servidor, exibirá as imagens e seus donos. Ao escolher uma imagem para download, o cliente abrirá uma conexão TCP diretamente com o outro cliente (usando o IP:PORTA fornecidos) e solicitará a imagem com o comando `GET <MD5>`. A imagem será salva no diretório do cliente. Caso já exista um arquivo com o mesmo nome, o cliente o renomeará com `_downloaded` para evitar sobrescrita.

4. **Atualizar registro**: Caso o cliente adicione ou remova imagens do seu diretório, ele pode atualizar seu registro junto ao servidor para refletir essas mudanças.

5. **Desconectar do servidor (END)**: O cliente informa ao servidor que não deseja mais compartilhar imagens, removendo-se da lista de clientes.

6. **Sair**: Encerra a execução do cliente.

## Observações

- O servidor não exibirá logs de transferências de imagem, pois não participa delas. Toda transferência de imagem ocorre entre clientes.
- Certifique-se de que o servidor está rodando antes de registrar o cliente.
- Caso o arquivo baixado não abra, verifique se não houve interrupção no meio da transferência ou se o formato é suportado pelo visualizador de imagens do sistema.