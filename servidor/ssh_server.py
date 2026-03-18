"""
Este script implementa un servidor SSH honeypot utilizando la biblioteca Paramiko. El honeypot escucha en el puerto 2222 y simula un servidor SSH real, pero en realidad no permite autenticaciones válidas. Cada vez que un atacante intenta autenticarse, el honeypot registra el intento, obtiene la geolocalización del atacante a partir de su IP, guarda el intento en una base de datos SQLite, y envía un evento a la interfaz gráfica para mostrarlo en un mapa en tiempo real. El objetivo es atraer a los atacantes y registrar sus intentos sin permitirles acceder realmente al sistema, lo que ayuda a monitorear y analizar los ataques SSH que se reciben.
"""


import socket      # Librería estándar para trabajar con sockets (red, conexiones TCP/IP)
import threading   # Permite ejecutar múltiples hilos (varios clientes a la vez)
import paramiko    # Biblioteca para implementar el protocolo SSH en Python
import time        # Para manejar tiempos y fechas
from servidor.geoip import get_geo   # Función personalizada para obtener la geolocalización de una IP
from compartir.eventos import event_queue   # Cola de eventos compartida para comunicar el servidor con la interfaz gráfica (mapa)
from servidor.databases import guardar_intento_ataque   # Función personalizada para guardar los intentos de ataque en la base de datos SQLite


HOST = "0.0.0.0"   # Escuchar en todas las interfaces de red disponibles (permite recibir conexiones desde cualquier IP)
PORT = 2222        # Puerto personalizado para el honeypot (no es el puerto SSH estándar 22, para evitar conflictos con un servidor SSH real que pueda estar corriendo en la máquina)
KEY_FILE = "key"   # Archivo de clave privada para el servidor SSH (se genera con ssh-keygen y se coloca en el mismo directorio que este script)

class Honeypot(paramiko.ServerInterface):   # Clase que implementa la interfaz de servidor de Paramiko para manejar las conexiones SSH entrantes. Esta clase define cómo se autentican los usuarios, qué tipo de autenticación se permite, y cómo se manejan las solicitudes de canal (como abrir una sesión).

    def __init__(self, ip):    
        self.ip = ip                        # Guardamos la IP del cliente para usarla en la geolocalización y en los registros de ataques
        self.event = None                   # Inicializamos un atributo para almacenar el evento de ataque que se generará cuando un atacante intente autenticarse. Este evento se enviará a la interfaz gráfica para mostrarlo en el mapa.     


    def check_auth_password(self, username, password):   # Método que se llama cuando un cliente intenta autenticarse con un nombre de usuario y contraseña. Aquí es donde se registra el intento de ataque, se obtiene la geolocalización del atacante, se guarda el intento en la base de datos, y se envía el evento a la interfaz gráfica. Finalmente, siempre se devuelve AUTH_FAILED para simular que el honeypot no acepta ninguna autenticación válida, lo que hace que los atacantes sigan intentando y generen más eventos para el mapa.

        time.sleep(1)                                    # Simulamos un pequeño retraso para que el atacante no reciba una respuesta instantánea (lo que podría parecer sospechoso). Esto hace que el honeypot se comporte de manera más realista, ya que los servidores SSH reales suelen tardar un poco en responder a los intentos de autenticación. 

        geo = get_geo(self.ip)                           # Obtenemos la geolocalización del atacante a partir de su IP utilizando la función get_geo. Esta función devuelve un diccionario con la ciudad, país, latitud y longitud asociados a la IP. Esta información se usará para mostrar el ataque en el mapa y para guardar un registro detallado del intento de ataque en la base de datos.

        print(f"[!] Intento -> {username}:{password} desde {self.ip}") 

        event = {                                        # Creamos un evento con toda la información relevante del intento de ataque, incluyendo la IP del atacante, el nombre de usuario y contraseña que intentó usar, la ciudad y país obtenidos de la geolocalización, las coordenadas (latitud y longitud) para mostrarlo en el mapa, y la fecha y hora del intento. Este evento se guardará en la base de datos y se enviará a la interfaz gráfica para que se muestre en el mapa en tiempo real.
            "ip": self.ip,
            "usuario": username,
            "password": password,
            "pais": geo.get("pais", "Desconocido"),
            "ciudad": geo["ciudad"],
            "lat": geo["lat"],
            "lon": geo["lon"],
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        guardar_intento_ataque(event)                    # Guardamos el intento de ataque en la base de datos SQLite utilizando la función guardar_intento_ataque. Esta función se encarga de insertar un nuevo registro en la tabla intento_ataques con toda la información del evento.
        event_queue.put(event)                           # Enviamos el evento a la cola de eventos compartida (event_queue) para que la interfaz gráfica pueda recibirlo y mostrarlo en el mapa en tiempo real. La interfaz gráfica estará escuchando esta cola y cada vez que reciba un nuevo evento, actualizará el mapa con la nueva información del ataque.

        return paramiko.AUTH_FAILED                      # Devolvemos AUTH_FAILED para simular que el honeypot no acepta ninguna autenticación válida, lo que hace que los atacantes sigan intentando y generen más eventos para el mapa. Esto es fundamental para que el honeypot cumpla su función de atraer a los atacantes y registrar sus intentos sin permitirles acceder realmente al sistema.
    
    
    def get_allowed_auths(self, username):  # Método que se llama para determinar qué métodos de autenticación se permiten para un usuario dado. En este caso, devolvemos "password" para indicar que solo se permite la autenticación por contraseña, lo que es común en muchos servidores SSH y es el método que queremos simular para atraer a los atacantes. Esto hace que el honeypot se comporte de manera más realista, ya que muchos atacantes intentan autenticarse utilizando contraseñas comunes.
        return "password"  


    def check_channel_request(self, kind, chanid):  # Método que se llama cuando un cliente intenta abrir un canal (por ejemplo, para iniciar una sesión interactiva). En este caso, solo permitimos canales de tipo "session", que es el tipo de canal que se utiliza para las sesiones SSH normales. Si el cliente intenta abrir un canal de otro tipo, devolvemos OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED para simular que el servidor no permite ese tipo de canal. Esto ayuda a mantener el honeypot simple y enfocado en registrar los intentos de autenticación sin permitir otras interacciones más complejas.
        if kind == "session":                       # Permitimos solo sesiones SSH normales. 
            return paramiko.OPEN_SUCCEEDED          # Devolvemos OPEN_SUCCEEDED para indicar que el canal se ha abierto correctamente, aunque en realidad no haremos nada con ese canal.
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED # Devolvemos OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED para simular que el servidor no permite abrir canales de otros tipos.



def handle_client(client,addr):   # Función que maneja cada cliente que se conecta.

    print(f"[+] Conexion desde {addr}")  

    transport = None              # Inicializamos para el bloque finally que se encargará de cerrar la conexión correctamente.   

    try:
        transport = paramiko.Transport(client) # Creamos un objeto Transport de Paramiko para manejar la conexión SSH con el cliente. El objeto Transport se encarga de gestionar la comunicación SSH, incluyendo la autenticación, el cifrado y el manejo de canales. Al pasarle el socket del cliente, el Transport se prepara para negociar la conexión SSH con ese cliente.

        transport.auth_timeout = 300 # Establecemos un tiempo de espera para la autenticación de 300 segundos (5 minutos). Esto significa que si el cliente no completa el proceso de autenticación dentro de ese tiempo, la conexión se cerrará automáticamente. Esto ayuda a evitar que las conexiones se queden abiertas indefinidamente si un atacante se conecta pero no intenta autenticarse, lo que podría consumir recursos del sistema.

        transport.add_server_key( # Agregamos la clave privada del servidor SSH al objeto Transport para que pueda usarla durante el proceso de autenticación.
            paramiko.RSAKey.from_private_key_file(KEY_FILE) 
        )

        ip = addr[0]              # Obtenemos la IP del cliente a partir de la dirección (addr) que es una tupla. La IP se usará para la geolocalización y para registrar el intento de ataque.

        # Simular IP extranjera para pruebas en localhost  
        if ip == "127.0.0.1":
            import random
            ips_mundo = [
                "1.116.0.0",        # China
                "108.62.211.172",   # New York
                "95.161.220.1",     # Rusia
                "200.16.42.1",      # Brasil
                "158.69.0.0",       # Canadá
                "123.123.123.123",  # Vietnam
                "5.62.60.61",       # Burundi
                "41.194.33.0",      # Comoros
                "5.62.61.153",      # Sri-Lanka
                "5.62.60.253",      # Malawi
                "2.59.193.0"        # Colombia
            ]
            ip = random.choice(ips_mundo)     # Elegimos un IP aleatoria
            print(f"[DEBUG] IP Simulada para mapa: {ip}")

        server = Honeypot(ip)                    # Creamos una instancia de la clase Honeypot, pasando la IP del cliente. 
        transport.start_server(server=server)    # Iniciamos el servidor SSH 

        while transport.is_active():             # Esperamos mientras la conexion siga activa.
            time.sleep(1)

    except Exception as e:                       # Capturamos cualquier excepción que ocurra durante el manejo de la conexión con el cliente 
        print(f"[!] Error con {addr}: {e}")

    finally:
        if transport:                            # Aseguramos cerrar la conexión correctamente para liberar recursos.
            transport.close()
        client.close()                           # Cerramos socket del cliente para liberar recursos y evitar conexiones colgadas.



def start_server():  # Función principal para iniciar el servidor SSH. Configura el socket para escuchar en el puerto especificado y acepta conexiones entrantes. Por cada conexión, crea un nuevo hilo para manejar al cliente utilizando la función handle_client.
    print(f"[*] Honeypot escuchando en {HOST}:{PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creamos un socket TCP/IP (AF_INET para IPv4, SOCK_STREAM para TCP)
    sock.bind((HOST, PORT))                                  # Enlazamos el socket a la dirección y puerto especificados para que pueda recibir conexiones en esa dirección y puerto. 
    sock.listen(100)                                         # Máximo 100 conexiones en cola antes de rechazar nuevas conexiones.

    while True:
        client, addr = sock.accept() # Esperamos a que un cliente se conecte. Cuando un cliente se conecta, accept() devuelve un nuevo socket para comunicarse con ese cliente y la dirección del cliente (IP y puerto). Este es el punto donde el servidor acepta una nueva conexión entrante.
                
        thread = threading.Thread(   # Creamos un hilo por cadda cliente para manejar la conexión de manera concurrente. 
            target=handle_client,
            args=(client, addr)
        )
        thread.daemon = True         # Marcamos el hilo como daemon para que se cierre automáticamente cuando el programa principal termine. 
        thread.start()      # Iniciamos el hilo para que ejecute la función handle_client, que se encargará de manejar toda la interacción con ese cliente específico (autenticación, registro de ataques, etc.) sin bloquear el hilo principal del servidor, lo que permite que el servidor siga aceptando nuevas conexiones mientras maneja las existentes.



if __name__ == "__main__": # Punto de entrada del programa. Si este script se ejecuta directamente, se llamará a la función start_server() para iniciar el servidor SSH honeypot.
    start_server()


