"""

"""

from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl
from compartir.eventos import event_queue
from servidor.ssh_server import start_server
import threading
import sys, os
from flask import Flask, send_file, jsonify




# -----------------------------
# Servidor web para el mapa
# -----------------------------

web_app = Flask(__name__)

events_buffer = []
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@web_app.route("/")
def mapa():
    return send_file(os.path.join(BASE_DIR, "mapa.html"))

@web_app.route("/events")
def events():
    global events_buffer
    data = events_buffer.copy()
    events_buffer.clear()
    return jsonify(data)

def start_web():
    web_app.run(host="0.0.0.0", port=5000)


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SSH Honeypot - Monitor de Ciudad y País")
        self.resize(1300, 850)

        # Arrancar el servidor SSH en Thread
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()


        # -----------------------------
        # Arrancar servidor web
        # -----------------------------

        web_thread = threading.Thread(target=start_web)
        web_thread.daemon = True
        web_thread.start()


        # ESTILO T-POT (CSS)

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

        # 1. Mapa (Ocupa la parte superior)
        self.web = QWebEngineView()
        base_path = os.path.dirname(os.path.abspath(__file__)) 
        mapa_path = os.path.join(base_path, "mapa.html")
        self.web.load(QUrl.fromLocalFile(mapa_path))
        layout.addWidget(self.web, 3)

        # 2. Tabla (Ahora con Ciudad y País para mayor control)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["IP", "País", "Ciudad", "Usuario", "Password", "Fecha"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_events)
        self.timer.start(500)


    def update_events(self):
        try:
            # Procesamos todos los ataques que hayan llegado a la cola
            while not event_queue.empty():
                e = event_queue.get_nowait() # Usamos get_nowait para que no se bloquee
                events_buffer.append(e)
                
                #print("Evento recibido:", e)

                r = self.table.rowCount()
                self.table.insertRow(r)

                self.table.setItem(r, 0, QTableWidgetItem(str(e.get("ip", "0.0.0.0"))))
                self.table.setItem(r, 1, QTableWidgetItem(str(e.get("pais", "Detectando..."))))
                self.table.setItem(r, 2, QTableWidgetItem(str(e.get("ciudad", "Desconocido"))))
                self.table.setItem(r, 3, QTableWidgetItem(str(e.get("usuario", "admin"))))
                self.table.setItem(r, 4, QTableWidgetItem(str(e.get("password", ""))))
                self.table.setItem(r, 5, QTableWidgetItem(str(e.get("fecha", ""))))

                # Marcamos el punto en el mapa llamando a la funcion JS de mapa.html
                lat = e.get("lat", 0)
                lon = e.get("lon", 0)

                ciudad_info = f"{e.get('ciudad')} ({e.get('pais')})"
                ip = e.get("ip", "0.0.0.0")

                self.web.page().runJavaScript(f"addAttack({lat}, {lon}, '{ip}', '{ciudad_info}')")

        except Exception as err:
            print(f"Error en la actualizacion de la GUI: {err}")



if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        window = GUI()
        window.show()
        print("[*] Interfaz iniciada correctamente.")
        print("[*] Honeypot SSH escuchando en puerto 2222")
        print("[*] Dashboard web en http://localhost:5000")

        sys.exit(app.exec_())

    except Exception as e:
        print(f"Fallo crítico al iniciar la App: {e}")
