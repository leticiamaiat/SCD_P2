import socket
import time
import random
import threading
from basecode import host_addr
from process_gpt import process_routine


def start_process(num_processes, coordinator_ip, r, k):
    processes = []

    for process_id in range(1, num_processes + 1):
        t = threading.Thread(target=process_routine, args=(process_id, coordinator_ip, r, k))
        processes.append(t)

    for p in processes:
        p.start()

    for p in processes:
        p.join()


if __name__ == "__main__":
    num_processes = 5
    r = 10
    k = 2

    start_process(num_processes, host_addr, r, k)
