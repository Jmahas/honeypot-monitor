"""
Este módulo contiene la implementación de la interfaz gráfica de usuario (GUI) para el sistema de monitoreo de ataques SSH. Utiliza PyQt5 para crear una ventana que muestra un mapa interactivo con los ataques en tiempo real y una tabla con detalles de cada intento de ataque. Además, arranca el servidor SSH honeypot y un servidor web para servir el mapa.
La GUI se actualiza cada 500 ms para mostrar los nuevos ataques que llegan a través de una cola de eventos compartida. Cada ataque se muestra en el mapa con su ubicación geográfica y se registra en la tabla con información como IP, país, ciudad, usuario, contraseña y fecha del intento.
"""


from PyQt5.QtWidgets import *                           # Componentes graficos de PyQt5 para crear la interfaz de usuario, como ventanas, botones, tablas, etc.
from PyQt5.QtWebEngineWidgets import QWebEngineView     # Componente de PyQt5 para mostrar contenido web (HTML, JavaScript) dentro de la aplicación. Se utiliza para mostrar el mapa interactivo que visualiza los ataques en tiempo real (mapa.html).
from PyQt5.QtCore import QTimer, QUrl                   # QTimer se utiliza para crear un temporizador que actualiza la GUI cada cierto intervalo (500 ms) para mostrar los nuevos ataques. 
from compartir.eventos import event_queue               # Importa la cola de eventos compartida entre el servidor SSH y la GUI. El servidor SSH coloca los ataques en esta cola, y la GUI los consume para actualizar el mapa y la tabla en tiempo real.    
from servidor.ssh_server import start_server            # Importa la función start_server del módulo ssh_server, que inicia el servidor SSH honeypot. 
import threading                                        # Permite ejecutar el servidor SSH y el servidor web en hilos separados para que ambos puedan funcionar simultáneamente. 
import sys, os                                          # sys se utiliza para manejar la salida del programa y la ejecución de la aplicación PyQt. os se utiliza para manejar rutas de archivos.
from flask import Flask, send_file, jsonify             # Flask es un microframework de Python para desarrollar aplicaciones web. Se utiliza aquí para crear un servidor web que sirve el mapa interactivo (mapa.html) y una API para enviar los eventos de ataques al frontend. send_file se utiliza para servir archivos estáticos (mapa.html) y jsonify se utiliza para convertir los datos de eventos en formato JSON para que puedan ser consumidos por el frontend.



# -----------------------------
# Servidor web para el mapa
# -----------------------------

web_app = Flask(__name__)                                   # Creamos una instancia de la aplicación Flask que se encargará de servir el mapa interactivo. 

events_buffer = []                                          # Buffer temporal para almacenar los eventos de ataques que llegan a través de la cola de eventos.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       # Ruta base del directorio actual.

@web_app.route("/")                                         # Ruta principal del servidor web.
                    
def mapa():
    return send_file(os.path.join(BASE_DIR, "mapa.html"))   # Devuelve el archivo mapa.html cuando se accede a la ruta principal. 

@web_app.route("/events")                                   # Endpoint que devuelve los eventos al frontend. El frontend hará peticiones periódicas a este endpoint para obtener los nuevos ataques y actualizar el mapa y la tabla en tiempo real.
def events():
    global events_buffer
    data = events_buffer.copy()                             # Copiamos el buffer de eventos para enviarlo al frontend.
    events_buffer.clear()                                   # Limpiamos el buffer después de copiarlo para que solo se envíen los eventos nuevos en la próxima petición.                          
    return jsonify(data)                                    # Devolvemos los eventos en formato JSON para que el frontend pueda procesarlos y mostrarlos en el mapa y la tabla.


def start_web():                                            # Funcion que inicia el servidor web Flask en un hilo separado para que pueda funcionar simultáneamente con el servidor SSH. 
    web_app.run(host="0.0.0.0", port=5000)                  # Iniciamos el servidor web en todas las interfaces.


class GUI(QMainWindow):                                     # Clase principal de la interfaz gráfica de usuario. Esta clase se encarga de configurar la ventana, iniciar el servidor SSH y el servidor web, y actualizar la interfaz con los eventos de ataques en tiempo real.
    def __init__(self):
        super().__init__()                                  # Llamamos al constructor de la clase base QMainWindow para inicializar la ventana principal de la aplicación.

        self.setWindowTitle("SSH Honeypot - Monitor de Ciudad y País")  # Titulo de la ventana.
        self.resize(1300, 850)                              # Tamaño inicial de la ventana.


        #-----------------------------------
        # Arrancar el servidor en segundo plano
        #-----------------------------------

        server_thread = threading.Thread(target=start_server)  # Creamos un hilo para ejecutar la función start_server, que inicia el servidor SSH honeypot. 
        server_thread.daemon = True                            # Marcamos el hilo como daemon para que se cierre automáticamente cuando el programa principal termine. 
        server_thread.start()                                  # Iniciamos el hilo para que ejecute el servidor SSH en segundo plano, permitiendo que la GUI siga funcionando y actualizándose con los ataques en tiempo real.



        # Visual estilo T-POT (CSS)

        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QTableWidget { 
                background-color: #262626; color: #00ff41; 
                gridline-color: #444; border: none; font-family: 'Consolas';
            }
            QHeaderView::section { background-color: #333; color: white; padding: 5px; }
            QLabel { color: #00ff41; font-size: 18px; font-weight: bold; }
        """)

        layout = QVBoxLayout()

        # Título y Estadísticas rápidas
        self.label_info = QLabel("SISTEMA DE MONITOREO DE ATAQUES (TIEMPO REAL)")
        layout.addWidget(self.label_info)

        # Mapa (Ocupa la parte superior)
        self.web = QWebEngineView()
        base_path = os.path.dirname(os.path.abspath(__file__)) 
        mapa_path = os.path.join(base_path, "mapa.html")
        self.web.load(QUrl.fromLocalFile(mapa_path))                                # Cargamos mapa.html en el navegador embebido para mostrar el mapa interactivo. 
        layout.addWidget(self.web, 3)                                               # El mapa ocupa más espacio que la tabla para darle mayor protagonismo visual.

        # Tabla de eventos (Ocupa la parte inferior)
        self.table = QTableWidget(0, 6)                                                                  # Creamos una tabla con 0 filas y 6 columnas
        self.table.setHorizontalHeaderLabels(["IP", "País", "Ciudad", "Usuario", "Password", "Fecha"])   # Cabeceras de la tabla para mostrar la información de cada ataque.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)                          # Ajustamos el tamaño de las columnas para que se distribuyan uniformemente y ocupen todo el ancho disponible.
        layout.addWidget(self.table, 2)                                                                  # La tabla ocupa menos espacio que el mapa para darle un rol secundario pero complementario, mostrando los detalles de cada ataque.

        container = QWidget()                                                                            # Creamos un widget contenedor para colocar el layout vertical que contiene el mapa y la tabla. 
        container.setLayout(layout)                                                                      # Asignamos el layout al contenedor para organizar los widgets dentro de la ventana.
        self.setCentralWidget(container)                                                                 # Establecemos el widget contenedor como el widget central de la ventana principal.

        self.timer = QTimer()                                                                            # Creamos un temporizador que se ejecutará cada 500 ms para actualizar la GUI con los nuevos eventos de ataques que llegan a través de la cola de eventos.
        self.timer.timeout.connect(self.update_events)                                                   # Conectamos la señal timeout del temporizador a la función update_events, que se encargará de procesar los nuevos eventos y actualizar el mapa y la tabla en la GUI.
        self.timer.start(500)                                                                            # Iniciamos el temporizador para que comience a emitir señales cada 500 ms, lo que hará que la GUI se actualice con los nuevos ataques en tiempo real.                               



    def update_events(self):                                                                        # Función que se llama cada vez que el temporizador emite una señal (cada 500 ms). Esta función procesa los nuevos eventos de ataques que han llegado a través de la cola de eventos y actualiza la tabla y el mapa en la GUI.
        try:
            # Procesamos todos los eventos nuevos que han llegado a través de la cola de eventos. Usamos un bucle while para seguir procesando hasta que la cola esté vacía.
            while not event_queue.empty(): 
                e = event_queue.get_nowait()                                                        # Obtenemos un evento de la cola sin bloquear (get_nowait) para procesarlo. 
                events_buffer.append(e)                                                             # Agregamos el evento al buffer temporal que se enviará al frontend a través del endpoint /events para actualizar el mapa en tiempo real.

                r = self.table.rowCount()                                                           # Obtenemos el número actual de filas en la tabla para saber dónde insertar la nueva fila con la información del ataque.
                self.table.insertRow(r)                                                             # Insertamos una nueva fila al final de la tabla para mostrar el nuevo ataque.                                         

                # Insertamos la información del ataque en cada columna de la nueva fila. Usamos get con valores por defecto para evitar errores si alguna clave falta en el evento.
                self.table.setItem(r, 0, QTableWidgetItem(str(e.get("ip", "0.0.0.0"))))
                self.table.setItem(r, 1, QTableWidgetItem(str(e.get("pais", "Detectando..."))))
                self.table.setItem(r, 2, QTableWidgetItem(str(e.get("ciudad", "Desconocido"))))
                self.table.setItem(r, 3, QTableWidgetItem(str(e.get("usuario", "admin"))))
                self.table.setItem(r, 4, QTableWidgetItem(str(e.get("password", ""))))
                self.table.setItem(r, 5, QTableWidgetItem(str(e.get("fecha", ""))))

                # Marcamos el punto en el mapa llamando a la funcion JS de mapa.html
                lat = e.get("lat", 0)
                lon = e.get("lon", 0)

                ciudad_info = f"{e.get('ciudad')} ({e.get('pais')})"                                # Creamos una cadena con la ciudad y el país para mostrar en el mapa al hacer clic en el punto del ataque.
                ip = e.get("ip", "0.0.0.0")                                                         # Obtenemos la IP del ataque para mostrarla en el mapa al hacer clic en el punto del ataque.

                self.web.page().runJavaScript(f"addAttack({lat}, {lon}, '{ip}', '{ciudad_info}')")  # Llamamos a la función JavaScript addAttack definida en mapa.html para agregar un nuevo punto en el mapa con la latitud, longitud, IP y ciudad del ataque. Esto hará que el mapa se actualice visualmente con cada nuevo ataque que llegue.

        except Exception as err:
            print(f"Error en la actualizacion de la GUI: {err}")


# Punto de entrada del programa. 
if __name__ == "__main__":
    app = QApplication(sys.argv)                                            # Creamos una instancia de QApplication, que es necesaria para cualquier aplicación PyQt. Esta instancia maneja la configuración global de la aplicación y el ciclo de eventos.

    try:
        window = GUI()                                                      # Creamos una instancia de la clase GUI, que configura la ventana principal, inicia el servidor SSH y el servidor web, y prepara la interfaz para mostrar los ataques en tiempo real.
        window.show()                                                       # Mostramos la ventana principal de la aplicación. 
        print("[*] Interfaz iniciada correctamente.")
        print("[*] Honeypot SSH escuchando en puerto 2222")
        print("[*] Dashboard web en http://localhost:5000")

        sys.exit(app.exec_())                                               # Iniciamos el ciclo de eventos de la aplicación PyQt. Esto hará que la aplicación se mantenga abierta y responda a las interacciones del usuario y a los eventos del sistema. La función exec_() bloquea la ejecución hasta que la aplicación se cierre, momento en el cual devuelve un código de salida que se pasa a sys.exit() para finalizar el programa correctamente.

    except Exception as e:
        print(f"Fallo crítico al iniciar la App: {e}")
