import socket
import threading
import paramiko
import time
from servidor.geoip import get_geo
from compartir.eventos import event_queue
from servidor.databases import guardar_intento_ataque


HOST = "0.0.0.0"
PORT = 2222
KEY_FILE = "key"

class Honeypot(paramiko.ServerInterface):

    def __init__(self, ip):
        self.ip = ip


    def check_auth_password(self, username, password):

        time.sleep(1)

        geo = get_geo(self.ip)

        print(f"[!] Intento -> {username}:{password} desde {self.ip}")

        event = {
            "ip": self.ip,
            "usuario": username,
            "password": password,
            "pais": geo.get("pais", "Desconocido"),
            "ciudad": geo["ciudad"],
            "lat": geo["lat"],
            "lon": geo["lon"],
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        guardar_intento_ataque(event)
        event_queue.put(event)

        return paramiko.AUTH_FAILED
    
    
    def get_allowed_auths(self, username):
        return "password"


    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED



def handle_client(client,addr):

    print(f"[+] Conexion desde {addr}")

    transport = None # inicializamos para el bloque finally

    try:
        transport = paramiko.Transport(client)

        transport.auth_timeout = 300

        transport.add_server_key(
            paramiko.RSAKey.from_private_key_file(KEY_FILE)
        )

        ip = addr[0]

        # MODO DESARROLLO (simular IP extranjera)
        if ip == "127.0.0.1":
            import random
            ips_mundo = [
                "1.116.0.0",    # China
                "108.62.211.172", # New York
                "95.161.220.1",   # Rusia
                "200.16.42.1",    # Brasil
                "158.69.0.0",     # Canadá
                "123.123.123.123" # Vietnam
            ]
            ip = random.choice(ips_mundo)
            print(f"[DEBUG] IP Simulada para mapa: {ip}")

        server = Honeypot(ip)
        transport.start_server(server=server) # Iniciamos el servidor

         # Esperar autenticación
        while transport.is_active():
            time.sleep(1)
       
        #server = Honeypot(addr[0])
        #transport.start_server(server=server)

    except Exception as e:
        print(f"[!] Error con {addr}: {e}")

    finally:
        if transport:
            transport.close()
        client.close()



def start_server():
    print(f"[*] Honeypot escuchando en {HOST}:{PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(100)

    while True:
        client, addr = sock.accept()
                
        # Thread por conexión (TFG = mejor diseño)
        thread = threading.Thread(
            target=handle_client,
            args=(client, addr)
        )
        thread.daemon = True
        thread.start()



if __name__ == "__main__":
    start_server()


