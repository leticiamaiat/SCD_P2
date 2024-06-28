from basecode import *
import logging
import threading


class Coordinator:
    def __init__(self, host_addr=("localhost", 12345), n_clients=5):
        """
        Uma thread apenas para receber a conexão de um novo processo,
        uma thread executando o algoritmo de exclusão mútua distribuída
        e a outra atendendo a interface (terminal)

        Args:
        - host_addr (tuple, optional): Endereço e Porta para conexão. Defaults to ("localhost", 12345).
        - n_clients (int, optional): Num de clientes/conexões a serem atendidos. Defaults to 5.
        """

        # Inicializando o logging
        logging.basicConfig(filename='log/coordinator.log', level=logging.INFO,
                            format='%(message)s | %(asctime)s')

        # Fila de pedidos
        self.num_clients = n_clients
        # Estrutura de dados para armazenar os sockets dos processos
        self.conn_sockets = {}
        self.request_queue = queue.Queue()
        self.log = []

        # Início do servidor coordenador
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(host_addr)
        self.server_socket.listen(self.num_clients)

        self.lock = threading.Semaphore()

        # Threads
        self.handle_connection = threading.Thread(
            target=self.handle_new_connection).start()
        self.handle_g_requests = threading.Thread(
            target=self.handle_requests).start()
        self.interface_routine = threading.Thread(
            target=self.terminal_interface).start()

    def handle_new_connection(self):
        # Função para tratar novos processos
        while True:

            # Quando conectar, registra o socket do cliente e o endereço
            client_socket, addr = self.server_socket.accept()

            # Usar a porta como identificador do processo (apenas exemplo) - Melhorar...
            process_id = f"{addr[0]}:{addr[1]}"

            # Adiciona o cliente conectado na lista de sockets conectados
            self.conn_sockets[process_id] = client_socket

            # Criando threads de forma desenfreada? Onde armazenar?
            threading.Thread(target=self.handle_process, args=(client_socket, process_id)).start()
            logging.info(f'Nova conexão estabelecida com o processo {process_id}.')

    def handle_process(self, client_socket, process_id):
        # Função para tratar mensagens de um processo
        """
        O coordenador deve gerar um log com
        todas as mensagens recebidas e enviadas (incluindo o instante da mensagem,
        o tipo de mensagem, e o processo origem ou destino).

        """
        while True:
            try:
                msg = client_socket.recv(package_size).decode()
                if msg.startswith('1|'):  # REQUEST
                    self.request_queue.put(process_id)
                    self.log_message('REQUEST', msg, process_id)

                elif msg.startswith('3|'):  # RELEASE
                    # "Desbloquear" o proximo atendimento => Atender o próximo cliente da queue e enviar "GRANT"
                    self.log_message('RELEASE', msg, process_id)
                    # Notify
                    self.lock.release()
            except Exception as e:
                logging.error(
                    f'Erro ao processar a mensagem do processo {process_id}: {e}')
                break

    def handle_requests(self):
        #  Ideia
        # while True:
        # 	with self.lock:

        # 		while not self.request_queue.empty():
        # 			self.lock.wait()

        # 		process_id = self.request_queue.get()
        # 		grant_msg = f'2|{process_id}|000000'.ljust(package_size).encode()

        # 		self.conn_sockets[process_id].send(grant_msg)
        # 		self.log_message('GRANT', grant_msg, process_id)

        while True:
            if not self.request_queue.empty():
                self.lock.acquire()
                process_id = self.request_queue.get()
                grant_msg = f'2|{process_id}|000000'.ljust(package_size).encode()
                self.conn_sockets[process_id].send(grant_msg)
                self.log_message('GRANT', grant_msg, process_id)

    def log_message(self, msg_type, msg, process_id):
        timestamp = time.time()
        
        log_entry = (timestamp, msg_type, msg, process_id)
        self.log.append(log_entry)
        
        if msg_type == "GRANT":
            logging.info(f'{msg_type} to process {process_id}: {msg}')
        else:
            logging.info(f'{msg_type} from process {process_id}: {msg}')

    def terminal_interface(self):
        # Função para comandos do terminal
        input_msg = """** Interface do Coordenador **\n 1- Listar Pedidos.\n 2- Registro de Atendimentos\n 3- Encerrar Coordenador\nAguardando entrada: """
        while True:
            cmd = input(input_msg)
            if cmd == '1':
                print("Fila de pedidos:", list(self.request_queue.queue))
            elif cmd == '2':
                # count = {pid: self.log.count(('GRANT', pid))
                #  for pid in self.conn_sockets.keys()}
                count = {pid: sum(
                    1 for log in self.log if log[1] == 'GRANT' and log[3] == pid) for pid in self.conn_sockets.keys()}

                print("Contagem de atendimentos:", count)
            elif cmd == '3':
                print("O coordenador morreu.")
                # for client_socket in self.conn_sockets.values():
                # 	client_socket.close()

                self.server_socket.close()
                break
            else:
                print("Comando inválido.")

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


# def handle_process(client_socket, process_id):
# 	# Função para tratar mensagens de um processo
# 	while True:
# 		msg = client_socket.recv(package_size).decode()
# 		if msg.startswith('1|'):  # REQUEST
# 			request_queue.put(process_id)
# 			log.append((time.time(), 'REQUEST', process_id))
# 		elif msg.startswith('2|'):
# 			# TODO: Lidar com o GRANT
# 			print()
# 		elif msg.startswith('3|'):  # RELEASE
# 			log.append((time.time(), 'RELEASE', process_id))


# def exclusion_algorithm():
# 	# Função para executar o algoritmo de exclusão mútua -- ?????
# 	while True:
# 		if not request_queue.empty():
# 			process_id = request_queue.get()
# 			client_socket = process_sockets[process_id]
# 			client_socket.send('2|GRANT'.ljust(package_size).encode())
# 			log.append((time.time(), 'GRANT', process_id))


# def terminal_interface():
# 	# Função para comandos do terminal
# 	while True:
# 		cmd = input("Aguardando entrada: ")
# 		if cmd == '1':
# 			print("Fila de pedidos:", list(request_queue.queue))
# 		elif cmd == '2':
# 			count = {pid: log.count(('GRANT', pid))
# 					 for pid in process_sockets.keys()}
# 			print("Contagem de atendimentos:", count)
# 		elif cmd == '3':
# 			break


# TODO: Não estamos armazenado nenhuma das threads !!
# Threads do coordenador
# threading.Thread(target=handle_new_connection, args=(server_socket,)).start()
# threading.Thread(target=exclusion_algorithm).start()
# threading.Thread(target=terminal_interface).start()

if __name__ == "__main__":
    Coord = Coordinator()
