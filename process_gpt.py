import socket
import time

def access_critical_section(process_id, coordinator_ip, coordinator_port, r, k):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((coordinator_ip, coordinator_port))
    
    for _ in range(r):
        # Envia REQUEST
        client_socket.send('1|{}|000000'.format(process_id).ljust(10).encode())
        grant_msg = client_socket.recv(10).decode()
        if grant_msg.startswith('2|'):  # Recebe GRANT
            with open('resultado.txt', 'a') as f:
                f.write('{}|{}\n'.format(process_id, time.time()))
            time.sleep(k)
            # Envia RELEASE
            client_socket.send('3|{}|000000'.format(process_id).ljust(10).encode())
    
    client_socket.close()

# Exemplo de execução do processo
process_id = 1  # Identificador do processo
coordinator_ip = 'localhost'
coordinator_port = 12345
r = 5  # Número de repetições
k = 2  # Tempo na região crítica

access_critical_section(process_id, coordinator_ip, coordinator_port, r, k)
