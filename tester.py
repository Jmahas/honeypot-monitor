""" import paramiko

def atacar_honeypot():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    password_list = ["1234", "admin", "password", "root", "qwerty", "test1", "login", "secret", "guest", "superman"]
    
    print("[*] Iniciando ataque de fuerza bruta...")
    
    for pwd in password_list:
        try:
            # Intentamos conectar
            client.connect('127.0.0.1', port=2222, username='test', password=pwd, timeout=5)
        except paramiko.AuthenticationException:
            print(f"[-] Intento fallido con: {pwd}")
        except Exception as e:
            print(f"[!] Error: {e}")
            break
    
    client.close()

if __name__ == "__main__":
    atacar_honeypot() """

import paramiko
import threading
import time
import random

def atacar_hilo(id_atacante, num_intentos):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    users = ["admin", "root", "user", "guest", "test"]
    passwords = ["1234", "admin", "password", "12345", "root"]
    
    print(f"[+] Atacante {id_atacante} iniciando sesión...")
    
    for i in range(num_intentos):
        user = random.choice(users)
        pwd = random.choice(passwords)
        try:
            # El honeypot registrará esto y activará la animación en el mapa
            client.connect('127.0.0.1', port=2222, username=user, password=pwd, timeout=5)
        except:
            # Ignoramos el fallo de conexión porque el Honeypot siempre rechaza
            pass
        
        # Pequeña espera aleatoria para que los proyectiles no salgan todos a la vez
        time.sleep(random.uniform(0.3, 1.5))
    
    client.close()

def ataque_global(total_hilos):
    hilos = []
    print(f"[*] LANZANDO ATAQUE SIMULTÁNEO CON {total_hilos} HILOS...")
    
    for i in range(total_hilos):
        # Cada hilo hará 10 intentos
        t = threading.Thread(target=atacar_hilo, args=(i, 10))
        hilos.append(t)
        t.start()
        time.sleep(0.1) # Escalonar ligeramente el inicio

    for t in hilos:
        t.join()

if __name__ == "__main__":
    # Prueba con 5 hilos para ver el mapa lleno de acción
    ataque_global(5)
    print("[*] Ataque finalizado.")