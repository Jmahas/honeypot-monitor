import sqlite3

DB_PATH = "datos/honeypot.db"

# Creamos la base de datos y la tabla para almacenar los intentos de ataque si no existen
def init_db():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS intento_ataques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    IP TEXT,
                    usuario TEXT,
                    password TEXT,
                    ciudad TEXT,
                    lat REAL,
                    lon REAL,
                    fecha DATE)
                    """)

    conexion.commit()
    conexion.close()


# Función para guardar un intento de ataque en la base de datos
def guardar_intento_ataque(e):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute(
        """
        INSERT INTO intento_ataques (ip, usuario, password, ciudad, lat, lon, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ( e["ip"],
          e["usuario"],
          e["password"],
          e["ciudad"],
          e["lat"],
          e["lon"],
          e["fecha"]
        )
    )

    conexion.commit()
    conexion.close()

# Inicializamos la base de datos al cargar este módulo para asegurarnos de que la tabla exista antes de intentar guardar cualquier intento de ataque.
init_db()
