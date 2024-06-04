from basecode import *


class Coordinator:
    def __init__(self, host_addr=("localhost", 12345), n_clients=5):
        """
		Uma thread apenas para receber a conexão de um novo processo, 
		uma thread executando o algoritmo de exclusão mútua distribuída,
  		e a outra atendendo a interface (terminal)

		Args:
		host_addr (tuple, optional): Endereço e Porta para conexão. Defaults to ("localhost", 12345).
		n_clients (int, optional): Num de clientes/conexões a serem atendidos. Defaults to 5.
  
		"""

        # Fila de pedidos
        self.num_clients = n_clients

        # Estrutura de dados para armazenar os sockets dos processos
        self.process_sockets = {}
        self.request_queue = queue.Queue()
        self.log = []

        # Início do servidor coordenador
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(host_addr)
        self.server_socket.listen(self.num_clients)

        # Threads
        pass

    def handle_new_connection(self, server_socket):
        # Função para tratar novos processos
        while True:
            client_socket, addr = server_socket.accept()
            # Usar a porta como identificador do processo (apenas exemplo)
            process_id = addr[1]
            # Adiciona o cliente conectado na lista de sockets conectados
            self.process_sockets[process_id] = client_socket

            # Criando threads de forma desenfreada? Onde armazenar?
            threading.Thread(target=handle_process, args=(client_socket, process_id)).start()


# TODO: Converter essas funções em métodos de uma classe
# def handle_new_connection(server_socket):
#     # Função para tratar novos processos
#     while True:
#         client_socket, addr = server_socket.accept()
#         # Usar a porta como identificador do processo (apenas exemplo)
#         process_id = addr[1]
#         process_sockets[process_id] = client_socket
#         threading.Thread(target=handle_process, args=(
#             client_socket, process_id)).start()


def handle_process(client_socket, process_id):
    # Função para tratar mensagens de um processo
    while True:
        msg = client_socket.recv(package_size).decode()
        if msg.startswith('1|'):  # REQUEST
            request_queue.put(process_id)
            log.append((time.time(), 'REQUEST', process_id))
        elif msg.startswith('2|'):
            # TODO: Lidar com o GRANT
            print()
        elif msg.startswith('3|'):  # RELEASE
            log.append((time.time(), 'RELEASE', process_id))


def exclusion_algorithm():
    # Função para executar o algoritmo de exclusão mútua -- ?????
    while True:
        if not request_queue.empty():
            process_id = request_queue.get()
            client_socket = process_sockets[process_id]
            client_socket.send('2|GRANT'.ljust(package_size).encode())
            log.append((time.time(), 'GRANT', process_id))


def terminal_interface():
    # Função para comandos do terminal
    while True:
        cmd = input("Aguardando entrada: ")
        if cmd == '1':
            print("Fila de pedidos:", list(request_queue.queue))
        elif cmd == '2':
            count = {pid: log.count(('GRANT', pid))
                     for pid in process_sockets.keys()}
            print("Contagem de atendimentos:", count)
        elif cmd == '3':
            break


# TODO: Não estamos armazenado nenhuma das threads !!
# Threads do coordenador
threading.Thread(target=handle_new_connection, args=(server_socket,)).start()
threading.Thread(target=exclusion_algorithm).start()
threading.Thread(target=terminal_interface).start()
