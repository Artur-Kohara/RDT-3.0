# RDT-3.0

## Objetivo

Desenvolver, em Python, uma implementação robusta do protocolo RDT 3.0 (Reliable Data Transfer), baseado no livro de Kurose & Ross. A versão clássica do protocolo é do tipo stop-and-wait, utiliza números de sequência (0 ou 1) e ACKs/NAKs para confirmação de pacotes, sendo tolerante à perda de pacotes e erros de bits.

## Requisitos implementados

1. RDT 3.0 com timeout dinâmico: - O timeout deve ser ajustado com base em uma estimativa do RTT (Round Trip Time), usando média exponencial
   suavizada (Exponential Weighted Moving Average – EWMA).
2. Checksum para detecção de erros: - Os pacotes enviados devem conter um checksum simples. - Ao detectar um pacote corrompido, o receptor deve
   descartá-lo e não enviar ACK.
3. Simulação de perdas e corrupção: - Adicionar um módulo/função que simule: - Perda de pacotes - Corrupção de pacotes (bit flip simples) - Essas
   simulações devem ocorrer com uma probabilidade configurável (ex: 10%).
4. Prevenção de duplicatas: - O receptor deve usar o número de sequência e o ACK correspondente para evitar a entrega duplicada de dados em caso de
   retransmissões.
5. Logs e observação: - A aplicação deve imprimir logs com os seguintes eventos: - Envio de pacotes - Recebimento de ACKs - Retransmissões - Perda ou
   corrupção detectada - Tempo estimado de RTT e timeout - Taxa de transferência (vazão do protocolo) - Uso do IPERF para testes de vazão e comparação
   com o que seu protocolo obteve.
