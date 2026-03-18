"""
Convertimos la IP en la localizacion mediante la latitud y la longitud
"""

import geoip2.database  # Biblioteca para trabajar con bases de datos GeoIP2, que permiten obtener información geográfica a partir de direcciones IP.
import atexit           # Permite al programador definir múltiples funciones de salida que se ejecutarán al finalizar el programa. Se definen dos funciones públicas: registrar y anular registro.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))                   # Obtenemos el directorio actual del archivo geoip.py para construir la ruta a la base de datos GeoIP de manera relativa, lo que mejora la portabilidad del código.
DB_PATH = os.path.join(BASE_DIR, "..", "datos", "GeoLite2-City.mmdb")   # Construimos la ruta completa a la base de datos GeoIP2, que se encuentra en el directorio "datos" y se llama "GeoLite2-City.mmdb". Esta base de datos es proporcionada por MaxMind y contiene información geográfica detallada sobre las direcciones IP, incluyendo ciudad, país, latitud y longitud.
DB_PATH = os.path.abspath(DB_PATH)                                      # Convertimos la ruta a una ruta absoluta para asegurarnos de que el programa pueda encontrar la base de datos sin importar desde dónde se ejecute. Esto es especialmente útil si el programa se ejecuta desde un directorio diferente al del archivo geoip.py.

print("Abriendo base GeoIP en:", os.path.abspath(DB_PATH))

reader = geoip2.database.Reader(DB_PATH)                                # Creamos una instancia de Reader, que es la clase principal para acceder a la base de datos GeoIP. 

# Cerrar correctamente al terminar el programa
atexit.register(reader.close)

def get_geo(ip):
    try:
        r = reader.city(ip)                                             # Obtenemos la información de la ciudad a partir de la dirección IP utilizando el método city() del Reader. 

        ciudad = r.city.name
        pais = r.country.name

        return {                                                        # Devolvemos un diccionario con la información geográfica obtenida. Si la ciudad no está disponible, se usará el país, y si el país tampoco está disponible, se usará "Unknown". La latitud y longitud se obtienen de la ubicación, pero si no están disponibles, se asignan a 0.
            "ciudad": ciudad if ciudad else pais if pais else "Unknown",
            "pais": r.country.name if r.country.name else "Desconocido",
            "lat": r.location.latitude if r.location.latitude else 0,
            "lon": r.location.longitude if r.location.longitude else 0
        }
    
    except Exception as e:
        print("Error GeoIP:", e)
        return {"ciudad": "Unknown", "pais": "Unknown", "lat": 0, "lon": 0}