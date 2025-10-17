import socket
from utils import verify_packet, make_ack, should_drop, corrupt_packet

# Implementação do servidor (responsável por receber os pacotes e confirmar seu recebimento)
def run_server(host='127.0.0.1', port=5001, prob_loss=0.1, prob_corrupt=0.1):
    """
    Inicia o servidor RDT 3.0, agora com verificação de checksum unificada.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print(f"Servidor RDT escutando em {host}:{port}")

        expected_seq_num = 0

        while True:
            packet, addr = s.recvfrom(1024)
            
            # ETAPA 1: VERIFICAR INTEGRIDADE E DESEMPACOTAR
            unpacked_pkt = verify_packet(packet)

            if unpacked_pkt is None:
                print(f"Pacote recebido de {addr} está CORROMPIDO. Descartando.")
                continue

            # O servidor deve ignorar pacotes de ACK recebidos
            if unpacked_pkt.get('ack', False):
                # Isso pode acontecer em cenários de rede complexos, é seguro ignorar.
                continue

            # Se chegou aqui, é um pacote de dados válido
            seq_num = unpacked_pkt['seq_num']
            data = unpacked_pkt['data']
            
            print(f"Pacote de dados íntegro recebido de {addr} com seq={seq_num}.")

            # ETAPA 2: VERIFICAR NÚMERO DE SEQUÊNCIA
            if seq_num == expected_seq_num:
                print(f"Pacote com seq={seq_num} é o esperado. Enviando ACK={seq_num}.")
                print(f"Dados: {data.decode('utf-8')}")
                
                # Envia ACK para o pacote recebido
                ack_packet = make_ack(seq_num)
                if should_drop(prob_loss):
                    print(f"Simulando PERDA do ACK seq={seq_num}. ACK não enviado.")
                else:
                    # Simula corrupção de ACK
                    ack_to_send = corrupt_packet(ack_packet, prob_corrupt)
                    print(f"Enviando ACK seq={seq_num} (pode estar corrompido)...")
                    s.sendto(ack_to_send, addr)
                
                expected_seq_num = 1 - expected_seq_num
            else:
                # Pacote de dados duplicado
                print(f"Pacote duplicado com seq={seq_num}. Reenviando ACK para o último pacote correto (ACK={1 - expected_seq_num}).")
                last_ack_seq = 1 - expected_seq_num
                ack_packet = make_ack(last_ack_seq)
                if should_drop(prob_loss):
                    print(f"Simulando PERDA do ACK seq={last_ack_seq}. ACK não enviado.")
                else:
                    ack_to_send = corrupt_packet(ack_packet, prob_corrupt)
                    print(f"Enviando ACK seq={last_ack_seq} (pode estar corrompido)...")
                    s.sendto(ack_to_send, addr)

if __name__ == "__main__":
    run_server()