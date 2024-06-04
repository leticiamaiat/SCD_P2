import socket
import threading
import queue
import time

# Fila de pedidos
request_queue = queue.Queue()
log = []

# Estrutura de dados para armazenar os sockets dos processos
process_sockets = {}

# Função para tratar novos processos
def handle_new_connection(server_socket):
    while True:
        client_socket, addr = server_socket.accept()
        process_id = addr[1]  # Usar a porta como identificador do processo (apenas exemplo)
        process_sockets[process_id] = client_socket
        threading.Thread(target=handle_process, args=(client_socket, process_id)).start()

# Função para tratar mensagens de um processo
def handle_process(client_socket, process_id):
    while True:
        msg = client_socket.recv(10).decode()
        if msg.startswith('1|'):  # REQUEST
            request_queue.put(process_id)
            log.append((time.time(), 'REQUEST', process_id))
        elif msg.startswith('3|'):  # RELEASE
            log.append((time.time(), 'RELEASE', process_id))

# Função para executar o algoritmo de exclusão mútua
def exclusion_algorithm():
    while True:
        if not request_queue.empty():
            process_id = request_queue.get()
            client_socket = process_sockets[process_id]
            client_socket.send('2|GRANT'.ljust(10).encode())
            log.append((time.time(), 'GRANT', process_id))

# Função para comandos do terminal
def terminal_interface():
    while True:
        cmd = input()
        if cmd == '1':
            print("Fila de pedidos:", list(request_queue.queue))
        elif cmd == '2':
            count = {pid: log.count(('GRANT', pid)) for pid in process_sockets.keys()}
            print("Contagem de atendimentos:", count)
        elif cmd == '3':
            break

# Início do servidor coordenador
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))
server_socket.listen(5)

# Threads do coordenador
threading.Thread(target=handle_new_connection, args=(server_socket,)).start()
threading.Thread(target=exclusion_algorithm).start()
threading.Thread(target=terminal_interface).start()
