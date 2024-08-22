from socket import SHUT_RD
from coord_basecode import *
import os
import logging
import queue

# Quero que a thread _handle_new_connection possam ser interrompida a qualquer momento

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
    def __init__(self, host_addr=("localhost", 12345), n_clients=5):
        """
        Uma thread apenas para receber a conexão de um novo processo,
        uma thread executando o algoritmo de exclusão mútua distribuída
        e a outra atendendo a interface (terminal)

        Args:
        - host_addr (tuple, optional): Endereço e Porta para conexão. Defaults to ("localhost", 12345).
        - n_clients (int, optional): Num de clientes/conexões a serem atendidos. Defaults to 5.
        """
        logdir = os.path.curdir + "/log"
        logfiles = ["coordinator.log" , "resultado.txt"]
        if not os.path.exists(logdir): os.makedirs(logdir)
        for logfile in logfiles:
            if not os.path.isfile(logdir + logfile):
                f = open(logdir + "/" + logfile, 'w')
                f.close()
            

        # Inicializando o logging
        logging.basicConfig(filename=logdir+"/"+logfiles[0], level=logging.INFO, format='%(message)s - %(asctime)s')

        # Mensagem da interface de comando
        self.input_msg = """** Interface do Coordenador **\n 1- Listar Pedidos.\n 2- Registro de Atendimentos\n 3- Encerrar Coordenador\nAguardando entrada: """

        # Fila de pedidos
        self.num_clients = n_clients

        # Estrutura de dados para armazenar os sockets dos processos
        self.conn_sockets = {}

        self.thread_list = []

        self.request_queue = queue.Queue()
        self.log = []

        # Início do servidor coordenador
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(host_addr)
        self.server_socket.listen(self.num_clients)

        self.lock = threading.Semaphore()

        # Threads
        self.handle_connection = StoppableThread(target=self._handle_new_connection)
        self.handle_g_requests = StoppableThread(target=self._handle_requests)
        self.interface_routine = StoppableThread(target=self._terminal_interface)

        self.handle_connection.start()
        self.handle_g_requests.start()
        self.interface_routine.start()

    def _handle_new_connection(self):
        # Função para tratar novos processos
        while not self.handle_connection.stopped():  # Verifica se a thread foi parada
            client_socket, addr = self.server_socket.accept()

            process_id = addr[1]

            self.conn_sockets[process_id] = client_socket

            thread = StoppableThread(target=self._handle_process, args=(client_socket, process_id))
            thread.start()

            self.thread_list.append(thread)

    def _handle_process(self, client_socket, process_id):
        while True:
            try:
                msg = client_socket.recv(package_size).decode()
                if msg.startswith('1|'):  # REQUEST
                    self.request_queue.put(process_id)
                    self._log_message('REQUEST', msg, process_id)

                elif msg.startswith('3|'):  # RELEASE
                    self._log_message('RELEASE', msg, process_id)
                    self.lock.release()

            except ConnectionResetError:
                # Exceção gerada quando o cliente desconecta
                logging.error(f'DISCONNECT from {process_id}')
                self.conn_sockets.pop(process_id, None)  # Remove o processo da lista de conexões
                break
            except Exception as e:
                logging.error(f'Erro ao processar a mensagem do processo {process_id}: {e}')
                break

        # Verifica se todas as conexões foram fechadas
        # if not self.conn_sockets:
        #     self._shutdown_coordinator()

    def _shutdown_coordinator(self):
        """Encerra todas as threads e fecha o socket do coordenador."""

        print("Todos os processos finalizaram. Encerrando o Coordenador.")

        self.handle_g_requests.stop()
        self.handle_connection.stop()
        self.interface_routine.stop()

        for thread in self.thread_list:
            thread.stop()

        self.server_socket.close()
        os._exit(0)

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
                [print(f"{i+1}º: {request}") for i, request in enumerate(self.request_queue.queue)]
                self._clear_terminal()

            elif cmd == '2':
                # TODO: Buscar o registro de atendimentos baseado no log e não no conn_sockets 
                count = {pid: sum(1 for log in self.log if log[1] == 'GRANT' and log[3] == pid) for pid in self.conn_sockets.keys()}
                sorted_count = dict(sorted(count.items(), key=lambda item: item[1], reverse=True))

                print(f"Contagem de atendimentos ({len(count)}):")
                for process, freq in sorted_count.items():
                    print(f"{process}: {freq}")

                self._clear_terminal()

            elif cmd == '3':
                self._shutdown_coordinator()
                break

            else:
                print("Comando inválido.")



if __name__ == "__main__":
    Coord = Coordinator(n_clients=n_clients)
