
import socket
import paramiko
import threading


def handle_connection():
    pass



def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', 2222))
    server_sock.listen(223)

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"Connection from {client_addr[0]}:{client_addr[1]}")
        t = threading.Thread(target=handle_connection, args=(client_sock,))
        t.start()

        transport = paramiko.Transport(client_sock)
        server_key =paramiko.RSAKey.from_private_key_file('key')
        transport.add_server_key(server_key)
        ssh = paramiko.ServerInterface()
        transport.start_server(server=ssh)


if __name__ == "__main__":
    main()