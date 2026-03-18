Honeypot SSH - Proyecto de Monitorización
=========================================

Este proyecto es un honeypot SSH educativo desarrollado en Python. 
Su objetivo es simular un servidor SSH vulnerable para recibir y 
registrar intentos de conexión, sin comprometer sistemas reales.

Características
---------------
- Simula un servidor SSH utilizando Paramiko.
- Registra intentos de conexión, usuarios y comandos enviados.
- Permite pruebas locales con IPs simuladas para testing seguro.
- Compatible con túneles TCP (ej. mediante ngrok) para exponer 
  el honeypot a Internet sin exponer tu máquina real.
- Preparado para guardar logs de actividad y realizar análisis posteriores.

Requisitos
----------
- Python 3.10+
- Librerías Python necesarias:
    paramiko
    flask
- Opcional: ngrok si quieres exponer tu honeypot a Internet.

Instalación
-----------
1. Clona el repositorio:
    git clone https://github.com/tu_usuario/honeypot-monitor.git
    cd honeypot-monitor

2. Instala las dependencias:
    pip install -r requirements.txt

3. Coloca tu clave privada SSH en el archivo definido en KEY_FILE
   en el código (requerida por Paramiko).

Uso
---
Ejecuta el honeypot con:
    python -m interface.app

Si usas ngrok para exponer tu servicio TCP:
    ngrok tcp 2222

Observa las conexiones en consola y, si quieres, en el panel web 
de ngrok: http://127.0.0.1:4040

Estructura del proyecto
-----------------------
/honeypot-monitor
│
├─ interface/        # Módulo principal del proyecto
│   └─ app.py        # Archivo de entrada (ejecutar con python -m interface.app)
├─ KEY_FILE          # Clave privada SSH utilizada por Paramiko
├─ README.txt        # Este archivo
├─ static/           # Archivos JS/CSS (si hubiera frontend)
└─ templates/        # Archivos HTML (si hubiera frontend)

Seguridad
---------
- Este proyecto no debe ser usado en producción con credenciales reales.
- Las IPs remotas pueden ser simuladas si se ejecuta en localhost con un archivo tester que simula un ataque de fuerza bruta o 
  detrás de ngrok.
- Mantén siempre tu honeypot aislado de tu red interna real.

Licencia
--------
MIT License © 2026
Puedes usar y modificar este proyecto con fines educativos.
