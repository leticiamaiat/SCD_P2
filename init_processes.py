from coord_basecode import *
import random
import argparse

def start_process(num_processes, coordinator_ip, tentativas, tempo_espera):
    processes = []

    for process_id in range(1, num_processes + 1):
        t = threading.Thread(target=process_routine, args=(process_id, coordinator_ip, tentativas, tempo_espera))
        processes.append(t)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

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
			current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
			with open('log/resultado.txt', 'a') as f:
				f.write(f'{process_id} | GRANTED | {current_time}\n')

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


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Código que utiliza de um coordenador de processos para gerenciar requisições críticas em condição de corrida.\nEsse código gera N processos que irão requisitar em loop o serviço crítico.")
    
    parser.add_argument('-r', '--requests', type=int, required=True, help="Numero de loops que cada processo executará.")
    parser.add_argument('-w', '--wait', type=int, required=True, help="Tempo de espera MINIMO que os processos passa dentro da região crítica, em segundos")
    parser.add_argument('-o', '--over', type=int, default=0, help="Numero de processo A MAIS. Objetivo de simular um numero superior de clientes")

    args = parser.parse_args()

    qntd_de_requests = args.requests
    tempo_de_espera = args.wait
    over_clients = args.over
    
    start_process(n_clients + over_clients, host_addr, qntd_de_requests, tempo_de_espera)
