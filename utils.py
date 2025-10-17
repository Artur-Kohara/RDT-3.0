import pickle
import hashlib
import random

def make_pkt(seq_num, data=b''):
    """
    Cria um pacote de DADOS com número de sequência, dados e um checksum MD5 dos dados.
    """
    checksum = hashlib.md5(data).hexdigest()
    packet = {'seq_num': seq_num, 'data': data, 'checksum': checksum}
    return pickle.dumps(packet)

def make_ack(seq_num):
    """
    Cria um pacote de ACK com número de sequência e um checksum.
    """
    # O checksum é calculado sobre uma representação consistente do conteúdo do ACK
    ack_content = f"ack:{seq_num}".encode('utf-8')
    checksum = hashlib.md5(ack_content).hexdigest()
    packet = {'seq_num': seq_num, 'ack': True, 'checksum': checksum}
    return pickle.dumps(packet)

def verify_packet(packet):
    """
    Verifica a integridade de QUALQUER pacote (dados ou ACK) e o desempacota.
    
    Retorna:
    - O dicionário do pacote desempacotado, se íntegro.
    - None, se o pacote estiver corrompido (falha no checksum, formato inválido ou erro ao desempacotar).
    """
    try:
        pkt = pickle.loads(packet)
        
        # Obter os componentes essenciais
        seq_num = pkt['seq_num']
        received_checksum = pkt['checksum']
        is_an_ack = pkt.get('ack', False)

        # Determinar sobre qual conteúdo o checksum deve ser verificado
        if is_an_ack:
            # Para ACKs, o checksum é sobre 'ack:<seq_num>'
            content_to_check = f"ack:{seq_num}".encode('utf-8')
        elif 'data' in pkt:
            # Para pacotes de dados, o checksum é sobre os dados
            content_to_check = pkt['data']
        else:
            # Formato de pacote desconhecido/inválido
            return None

        # Calcular o checksum esperado e comparar
        calculated_checksum = hashlib.md5(content_to_check).hexdigest()

        if received_checksum == calculated_checksum:
            return pkt  # Pacote íntegro, retorna dicionário
        else:
            return None  # Checksum incorreto -> corrompido

    except Exception:
        # Qualquer erro no desempacotamento ou na estrutura do pacote significa corrupção
        return None
    
def should_drop(prob_loss):
    """
    Retorna True se o pacote deve ser perdido, com probabilidade prob_loss (0.0 a 1.0).
    """
    return random.random() < prob_loss

def corrupt_packet(packet, prob_corrupt):
    """
    Com probabilidade prob_corrupt, corrompe o pacote (bit flip simples).
    """
    if random.random() < prob_corrupt:
        # Bit flip: altera um byte aleatório do pacote serializado
        packet_bytes = bytearray(packet)
        if packet_bytes:
            idx = random.randint(0, len(packet_bytes) - 1)
            packet_bytes[idx] ^= 0xFF  # Inverte todos os bits do byte
        return bytes(packet_bytes)
    else:
        return packet