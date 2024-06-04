from basecode import *
import random

# TODO: Rever esse papel todo - Muito confuso
def access_critical_section(process_id, coordinator_ip, r, k):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(coordinator_ip)

    for _ in range(r):
        # Envia REQUEST
        request_message = f'1|{process_id}|000000'.ljust(package_size).encode()
        client_socket.send(request_message)
        print(f'Processo {process_id} enviou REQUEST')

        while True:
            grant_msg = client_socket.recv(package_size).decode()
            if grant_msg.startswith('2|'):  # Recebe GRANT
                print(f'Processo {process_id} recebeu GRANT')
                break
        
        #Seção crítica
        current_time = time.time()
        with open('resultado.txt', 'a') as f:
            f.write(f'{process_id}|{current_time}\n')

        # "Utilização" do serviço
        time.sleep(k * random.randint(1, 3))

        # Após, envia o RELEASE
        realease_message = f'3|{process_id}|000000'.ljust(package_size).encode()
        client_socket.send(realease_message)
        print(f'Processo {process_id} enviou RELEASE')

    client_socket.close()
    print(f'Processo {process_id}: Conexão fechada')

if __name__ == '__main__':
    # Exemplo de execução do processo
    process_id = 7  # Identificador do processo
    # coordinator_ip = 'localhost'
    # coordinator_port = 12345
    r = 25  # Número de repetições
    k = 2  # Tempo na região crítica
    
    access_critical_section(process_id, host_addr, r, k)
    

