import os
import logging
import queue
import socket
import threading
import time


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Coordinator:
    def __init__(self, n_clients=5, host_addr=("localhost", 12345), package_size=10, logdir=f"{os.path.curdir}/log", coord_logfilename="coordinator.log", client_logfilename="resultado.txt"):
        """
        Uma thread apenas para receber a conexão de um novo processo,
        uma thread executando o algoritmo de exclusão mútua distribuída
        e a outra atendendo a interface (terminal)

        Args:
        - n_clients (int, optional): Num de clientes/conexões a serem atendidos. Defaults to 5.
        - host_addr (tuple, optional): Endereço e Porta para conexão. Defaults to ("localhost", 12345).
        - package_size: 
        - logdir:
        - coord_filename:
        - client_filename:
        """

        # Criação do diretório de log, caso o diretório de log não exista, crie.
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Para cada arquivo de log, caso o arquivo não exista, crie.
        for logfile in [coord_logfilename, client_logfilename]:
            if not os.path.isfile(logdir + logfile):
                with open(f"{logdir}/{logfile}", "w") as f:
                    pass

        # Inicializando o logging
        logging.basicConfig(filename=f"{logdir}/{coord_logfilename}",
                            level=logging.INFO, format='%(message)s - %(asctime)s')

        # Mensagem da interface de comando
        self.input_msg = """** Interface do Coordenador **\n 1- Listar Pedidos.\n 2- Registro de Atendimentos\n 3- Encerrar Coordenador\nAguardando entrada: """

        # Fila de pedidos
        self.num_clients = n_clients
        
        # Tamanho da mensagem de comunicação 
        self.package_size = package_size
        

        # Estrutura de dados para armazenar os sockets dos processos
        self.conn_sockets = {}

        #
        self.thread_list = []

        # Fila de atendimento
        self.request_queue = queue.Queue()
        self.log = []

        # Início do servidor coordenador
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(host_addr)
        self.server_socket.listen(self.num_clients)
        # Semaforo utilizado para gerenciar a exclusão mútua
        self.lock = threading.Semaphore()

        # Threads
        self.handle_connection = StoppableThread(
            target=self._handle_new_connection)
        self.handle_g_requests = StoppableThread(target=self._handle_requests)
        self.interface_routine = StoppableThread(
            target=self._terminal_interface)

        self.handle_connection.start()
        self.handle_g_requests.start()
        self.interface_routine.start()

    def _handle_new_connection(self):
        # Função para tratar novos processos
        while not self.handle_connection.stopped():  # Verifica se a thread foi parada
            client_socket, addr = self.server_socket.accept()

            process_id = addr[1]

            self.conn_sockets[process_id] = client_socket

            thread = StoppableThread(
                target=self._handle_process, args=(client_socket, process_id))
            thread.start()

            self.thread_list.append(thread)

    def _handle_process(self, client_socket, porta_tcp):
        while True:
            try:
                msg = client_socket.recv(self.package_size).decode()
                if msg.startswith('1|'):  # REQUEST
                    
                    processId = msg.split("|")[1]
                    obj_aux = self.conn_sockets.pop(porta_tcp,  None)
                    
                    if obj_aux is not None:
                        self.conn_sockets[processId] = obj_aux
                     
                    self.request_queue.put(processId)
                    self._log_message('REQUEST', msg, processId)

                elif msg.startswith('3|'):  # RELEASE
                    self.lock.release()
                    self._log_message('RELEASE', msg, processId)

            except ConnectionResetError:
                # Exceção gerada quando o cliente desconecta
                logging.error(f'DISCONNECT from {porta_tcp}')
                # # Remove o processo da lista de conexões
                # self.conn_sockets.pop(process_id, None)
                break
            except Exception as e:
                logging.error(f'Erro ao processar a mensagem do processo {porta_tcp}: {e}')
                break

    def _handle_requests(self):
        while True:
            if not self.request_queue.empty():
                # Aguarda um sinal de liberação caso o lock está em utilização
                self.lock.acquire()
                process_id = self.request_queue.get()
                grant_msg = f'2|{process_id}|000000'.ljust(
                    self.package_size).encode()
                self.conn_sockets[process_id].send(grant_msg)
                self._log_message('GRANT', grant_msg.decode(), process_id)

    def _terminal_interface(self):
        # Função para comandos do terminal
        while True:
            cmd = input(self.input_msg)

            os.system("cls") if os.name == "nt" else os.system("clear")

            if cmd == '1':
                print(f"Fila de pedidos ({self.request_queue.qsize()}):")
                [print(f"{i+1}º: {request}")
                 for i, request in enumerate(self.request_queue.queue)]
                self._clear_terminal()

            elif cmd == '2':
                # TODO: Buscar o registro de atendimentos baseado no log e não no conn_sockets
                count = {pid: sum(
                    1 for log in self.log if log[1] == 'GRANT' and log[3] == pid) for pid in self.conn_sockets.keys()}
                sorted_count = dict(
                    sorted(count.items(), key=lambda item: item[1], reverse=True))

                print(f"Contagem de atendimentos ({len(count)}):")
                for process, freq in sorted_count.items():
                    print(f"{process}: {freq}")

                self._clear_terminal()

            elif cmd == '3':
                self._shutdown_coordinator()
                break

            else:
                print("Comando inválido.")

    def _shutdown_coordinator(self):
        """Encerra todas as threads e fecha o socket do coordenador."""

        self.handle_g_requests.stop()
        self.handle_connection.stop()
        self.interface_routine.stop()

        [thread.stop() for thread in self.thread_list]

        self.server_socket.close()

        print("Todos os processos finalizaram. Encerrando o Coordenador.")
        os._exit(0)

    def _log_message(self, msg_type, msg, process_id):
        # Registra o timestamp
        timestamp = time.time()

        # Cria o registro de log e add ao log
        self.log.append((int(timestamp), msg_type, msg, process_id))

        # Formata e registra a mensagem no log do coordenador
        log_message = f"{msg_type} " + ("to" if msg_type == "GRANT" else "from") + f' process {process_id}: {msg}'
        logging.info(log_message)

    def _clear_terminal(self):
        input("Pressione Enter para continuar...")
        os.system("cls") if os.name == "nt" else os.system("clear")


if __name__ == "__main__":
    n_clients = int(input("Digite o numero de clientes que o coordenador atenderá:"))

    if n_clients > 0:
        os.system("cls") if os.name == "nt" else os.system("clear")
        Coord = Coordinator(n_clients=n_clients)
    else:
        print("Número de clientes inválido. Abortando coordenador...")
        exit(0)
