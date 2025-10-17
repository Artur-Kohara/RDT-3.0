import socket
import time
import sys
from utils import make_pkt, verify_packet, should_drop, corrupt_packet

# Implementação de classe para cálculo de vazão
class ThroughputCalculator:
    def __init__(self):
        self.start_time = None
        self.total_bytes = 0

    def start(self):
        """Inicia o cronômetro."""
        self.start_time = time.time()
        print("Cronômetro de vazão iniciado.")

    def add_bytes(self, num_bytes):
        """Adiciona o número de bytes de dados úteis transferidos."""
        self.total_bytes += num_bytes

    def calculate(self):
        """Para o cronômetro e calcula a vazão em Mbps."""
        if self.start_time is None:
            return 0
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        if duration == 0:
            return float('inf') # Evita divisão por zero
            
        # Vazão = (Total de Bytes * 8) / Duração -> em bits por segundo (bps)
        throughput_bps = (self.total_bytes * 8) / duration
        # Converte para Megabits por segundo (Mbps)
        throughput_mbps = throughput_bps / 1_000_000
        
        print("\n--- Relatório de Vazão (RDT 3.0) ---")
        print(f"Total de Dados Enviados: {self.total_bytes / 1024:.2f} KB")
        print(f"Tempo Total de Transferência: {duration:.4f} segundos")
        print(f"Vazão Calculada: {throughput_mbps:.6f} Mbps")
        print("--------------------------------------")
        
        return throughput_mbps

# Implementação do Cliente (responsável por enviar os pacotes de dados e verificar ACKs)
class RDTClient:
    def __init__(self, server_host='127.0.0.1', server_port=5001, alpha=0.125, beta=0.25, prob_loss=0.1, prob_corrupt=0.1):
        self.server_addr = (server_host, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Parâmetros para cálculo do Timeout
        self.alpha = alpha
        self.beta = beta
        self.estimated_rtt = None # Começa sem estimativa
        self.dev_rtt = None       # Começa sem estimativa
        self.timeout_interval = 1.0 # Timeout inicial de 1 segundo
        self.prob_loss = prob_loss
        self.prob_corrupt = prob_corrupt

        # Estado do cliente
        self.seq_num = 0
    
    def _update_timeout(self, sample_rtt):
        """
        Atualiza o intervalo de timeout usando as fórmulas EWMA.
        """
        if self.estimated_rtt is None:
            # Primeira medição
            self.estimated_rtt = sample_rtt
            self.dev_rtt = sample_rtt / 2
        else:
            # Atualização do EstimatedRTT
            self.estimated_rtt = (1 - self.alpha) * self.estimated_rtt + self.alpha * sample_rtt
            
            # Atualização do DevRTT
            rtt_diff = abs(sample_rtt - self.estimated_rtt)
            self.dev_rtt = (1 - self.beta) * self.dev_rtt + self.beta * rtt_diff

        # Cálculo final do timeout
        self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt
        
        print(f"--- RTT Stats ---")
        print(f"SampleRTT: {sample_rtt:.4f}s")
        print(f"EstimatedRTT: {self.estimated_rtt:.4f}s")
        print(f"DevRTT: {self.dev_rtt:.4f}s")
        print(f"TimeoutInterval: {self.timeout_interval:.4f}s")
        print(f"-----------------")

    def send(self, data):
        pkt = make_pkt(self.seq_num, data)

        while True:
            # Simula perda
            if should_drop(self.prob_loss):
                print(f"Simulando PERDA do pacote seq={self.seq_num}. Pacote não enviado.")
            else:
                # Simula corrupção
                pkt_to_send = corrupt_packet(pkt, self.prob_corrupt)
                print(f"Enviando pacote seq={self.seq_num} (pode estar corrompido)...")
                self.sock.sendto(pkt_to_send, self.server_addr)
            
            send_time = time.time()
            self.sock.settimeout(self.timeout_interval)
            
            try:
                ack_packet, _ = self.sock.recvfrom(1024)
                
                # VERIFICA A INTEGRIDADE DO PACOTE RECEBIDO
                unpacked_ack = verify_packet(ack_packet)
                
                # Verifica se é um ACK, se não é corrompido, e se o seq_num é o esperado
                if unpacked_ack and unpacked_ack.get('ack', False) and unpacked_ack['seq_num'] == self.seq_num:
                    reception_time = time.time()
                    sample_rtt = reception_time - send_time
                    
                    print(f"ACK íntegro recebido para seq={self.seq_num}.")
                    self._update_timeout(sample_rtt)
                    
                    self.seq_num = 1 - self.seq_num
                    break
                else:
                    # O pacote recebido é corrompido, não é um ACK, ou é um ACK para o seq_num errado.
                    if unpacked_ack:
                         details = f"ACK para seq={unpacked_ack['seq_num']}"
                    else:
                         details = "pacote CORROMPIDO"
                    
                    print(f"Resposta inválida recebida (esperado ACK para seq={self.seq_num}, mas recebido {details}). Ignorando.")
                    # Continua no loop e espera o timeout expirar.

            except socket.timeout:
                print(f"TIMEOUT! Retransmitindo pacote com seq={self.seq_num}.")

    def close(self):
        """
        Fecha o socket do cliente.
        """
        self.sock.close()
        print("Conexão do cliente fechada.")

if __name__ == "__main__":
    PACKET_SIZE = 1024 # bytes
    NUM_PACKETS = 100    # Quantidade de pacotes a enviar

    client = RDTClient()
    calculator = ThroughputCalculator()
    
    # Cria dados de exemplo para enviar
    message_data = b'X' * PACKET_SIZE

    # Inicia o cálculo da vazão
    calculator.start()

    for i in range(NUM_PACKETS):
        print(f"\n--- Enviando Pacote {i+1}/{NUM_PACKETS} ---")
        client.send(message_data)
        calculator.add_bytes(len(message_data)) # Adiciona o tamanho do DADO ÚTIL

    # Calcula e exibe a vazão final
    calculator.calculate()
    client.close()