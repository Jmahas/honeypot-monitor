"""
Este script es un simulador de ataques SSH que se conecta al honeypot en el puerto 2222.
Cada hilo simula un atacante diferente, intentando varias combinaciones de usuario y contraseña.
El objetivo es generar tráfico de ataque realista para probar la funcionalidad del honeypot y la visualización en el mapa."""

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
        # Cada hilo hará 5 intentos
        t = threading.Thread(target=atacar_hilo, args=(i, 5))
        hilos.append(t)
        t.start()
        time.sleep(0.1) # Escalonar ligeramente el inicio

    for t in hilos:
        t.join()

if __name__ == "__main__":
    # Prueba con 5 hilos para ver el mapa lleno de acción
    ataque_global(5)
    print("[*] Ataque finalizado.")