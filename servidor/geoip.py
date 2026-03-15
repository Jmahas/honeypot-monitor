"""
Convertimos la IP en la localizacion mediante la latitud y la longitud
"""

import geoip2.database
import atexit   #Permite al programador definir múltiples funciones de salida que se ejecutarán al finalizar el programa. Se definen dos funciones públicas: registrar y anular registro.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "datos", "GeoLite2-City.mmdb")
DB_PATH = os.path.abspath(DB_PATH)

print("Abriendo base GeoIP en:", os.path.abspath(DB_PATH))

reader = geoip2.database.Reader(DB_PATH)

# Cerrar correctamente al terminar el programa
atexit.register(reader.close)

def get_geo(ip):
    try:
        r = reader.city(ip)

        ciudad = r.city.name
        pais = r.country.name

        return {
            "ciudad": ciudad if ciudad else pais if pais else "Unknown",
            "pais": r.country.name if r.country.name else "Desconocido",
            "lat": r.location.latitude if r.location.latitude else 0,
            "lon": r.location.longitude if r.location.longitude else 0
        }
    
    except Exception as e:
        print("Error GeoIP:", e)
        return {"ciudad": "Unknown", "pais": "Unknown", "lat": 0, "lon": 0}