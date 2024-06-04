from basecode import *
import random

# TODO: Rever esse papel todo - Muito confuso
def access_critical_section(process_id, coordinator_ip, r, k):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(coordinator_ip)

    for _ in range(r):
        # Envia REQUEST
        client_socket.send('1|{}|000000'.format(
            process_id).ljust(package_size).encode())

        # Escuta a resposta
        grant_msg = client_socket.recv(package_size).decode()

        # Caso recebeu um GRANT
        if grant_msg.startswith('2|'):  # Recebe GRANT
            # TODO: Isso não deve fazer parte do papel do processo, quem vai gerenciar isso é o coord
            with open('resultado.txt', 'a') as f:
                f.write('{}|{}\n'.format(process_id, int(time.time())))

            # "Utilização" do serviço
            time.sleep(k*random.randint(1, 3))

            # Após, envia o RELEASE
            client_socket.send('3|{}|000000'.format(
                process_id).ljust(process_id).encode())

    client_socket.close()


# Exemplo de execução do processo
process_id = 7  # Identificador do processo
# coordinator_ip = 'localhost'
# coordinator_port = 12345
r = 25  # Número de repetições
k = 2  # Tempo na região crítica

access_critical_section(process_id, host_addr, r, k)
