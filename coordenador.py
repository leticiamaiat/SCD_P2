from coord_basecode import *
import os
import logging
import queue


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
        logging.basicConfig(filename='log/coordinator.log',
                            level=logging.INFO, format='%(message)s - %(asctime)s')
        # Mensagem da interface de comando
        self.input_msg = """** Interface do Coordenador **\n 1- Listar Pedidos.\n 2- Registro de Atendimentos\n 3- Encerrar Coordenador\nAguardando entrada: """

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
            target=self._handle_new_connection).start()
        self.handle_g_requests = threading.Thread(
            target=self._handle_requests).start()
        self.interface_routine = threading.Thread(
            target=self._terminal_interface).start()

    def _handle_new_connection(self):
        # Função para tratar novos processos
        while True:

            # Quando conectar, registra o socket do cliente e o endereço
            client_socket, addr = self.server_socket.accept()

            # Usar a porta como identificador do processo (apenas exemplo) - Melhorar...
            process_id = addr[1]

            # Adiciona o cliente conectado na lista de sockets conectados
            self.conn_sockets[process_id] = client_socket

            # Criando threads de forma desenfreada? Onde armazenar?
            threading.Thread(target=self._handle_process, args=(
                client_socket, process_id)).start()
            # logging.info(f'Nova conexão estabelecida com o processo {process_id}.')

    def _handle_process(self, client_socket, process_id):
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
                    self._log_message('REQUEST', msg, process_id)

                elif msg.startswith('3|'):  # RELEASE
                    # "Desbloquear" o proximo atendimento => Atender o próximo cliente da queue e enviar "GRANT"
                    self._log_message('RELEASE', msg, process_id)
                    # Notify
                    self.lock.release()

            except ConnectionResetError as e:
                # Exceção gerada quando o cliente desconecta..
                logging.error(f'DISCONNECT from {process_id}')

                break
            except Exception as e:
                logging.error(
                    f'Erro ao processar a mensagem do processo {process_id}: {e}')
                break

    def _handle_requests(self):
        while True:
            if not self.request_queue.empty():
                self.lock.acquire()
                process_id = self.request_queue.get()
                grant_msg = f'2|{process_id}|000000'.ljust(
                    package_size).encode()
                self.conn_sockets[process_id].send(grant_msg)
                self._log_message('GRANT', grant_msg.decode(), process_id)

    def _log_message(self, msg_type, msg, process_id):
        timestamp = time.time()

        log_entry = (int(timestamp), msg_type, msg, process_id)
        self.log.append(log_entry)

        if msg_type == "GRANT":
            logging.info(f'{msg_type} to process {process_id}: {msg}')
        else:
            logging.info(f'{msg_type} from process {process_id}: {msg}')

    def _clear_terminal(self):
        input("Pressione Enter para continuar...")
        os.system("cls") if os.name == "nt" else os.system("clear")

    def _terminal_interface(self):
        # Função para comandos do terminal
        while True:
            cmd = input(self.input_msg)

            os.system("cls") if os.name == "nt" else os.system("clear")

            if cmd == '1':

                print(f"Fila de pedidos ({self.request_queue.qsize()}):")
                for i, request in enumerate(self.request_queue.queue):
                    print(f"{i+1}º: {request}")

                self._clear_terminal()

            elif cmd == '2':

                count = {pid: sum(1 for log in self.log if log[1] == 'GRANT' and log[3] == pid) for pid in self.conn_sockets.keys()}
                
                sorted_count = dict(sorted(count.items(), key=lambda item: item[1], reverse=True))

                print(f"Contagem de atendimentos ({len(count)}):")
                for process, freq in sorted_count.items(): print(f"{process}: {freq}")

                self._clear_terminal()
            # elif cmd == '3':
            #     print("O coordenador morreu.")
            #     self.server_socket.close()
            #     break
            else:
                print("Comando inválido.")


if __name__ == "__main__":
    Coord = Coordinator(n_clients=n_clients)