import hashlib
import json

def validar_mensagem(data):
    """Valida se a mensagem está no formato correto."""
    try:
        mensagem = json.loads(data.decode())
        if "command" not in mensagem:
            return False, None
        return True, mensagem
    except json.JSONDecodeError:
        return False, None