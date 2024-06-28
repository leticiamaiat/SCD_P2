from basecode import *
import random

# TODO: Rever esse papel todo - Muito confuso


def process_routine(process_id, coordinator_ip, n_tries, min_time_consuming):

	try:
		# Inicialmente conecta ao socket do coordenador
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client_socket.connect(coordinator_ip)

		# Repetirá a rotina n_tries vezes
		for _ in range(n_tries):

			# Envia REQUEST
			request_message = f'1|{process_id}|000000'.ljust(package_size).encode()
			client_socket.send(request_message)

			print(f'Processo {process_id} enviou REQUEST')

			# Passa a "ouvir" a resposta do coordenador --- Ideia: Criar uma thread para isso?
			while True:
				grant_msg = client_socket.recv(package_size).decode()
				if grant_msg.startswith('2|'):  # Recebe GRANT
					print(f'Processo {process_id} recebeu GRANT')
					break

			# A partir daqui o processo deve estar na região critíca com exclusão mutua
			# Seção crítica
			current_time = time.time()
			with open('log/resultado.txt', 'a') as f:
				f.write(f'{process_id}|{current_time}\n')

			# "Utilização" do serviço
			time.sleep(min_time_consuming * random.randint(1, 3))

			# Saida da região crítica

			# Após, monta a mensagem e envia o RELEASE
			realease_message = f'3|{process_id}|000000'.ljust(package_size).encode()
			client_socket.send(realease_message)
			print(f'Processo {process_id} enviou RELEASE')

		client_socket.close()
		print(f'Processo {process_id}: Conexão fechada')
	except ConnectionRefusedError:
		print("A conexão com o Coordenador foi recusada, verifique se o Coordenador está ativo e tente novamente mais tarde.")


if __name__ == '__main__':
    # Exemplo de execução do processo
    process_id = "192.168.0.5"  # Identificador do processo
    # coordinator_ip = 'localhost'
    # coordinator_port = 12345
    r = 5  # Número de repetições
    k = 2  # Tempo na região crítica

    process_routine(process_id, host_addr, r, k)
