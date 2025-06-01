from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from faker import Faker
import sys
import os
import argparse
import requests
import time
from shapely.geometry import Point, shape, Polygon
import json
import pickle
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Usuarios, RefreshToken, InvitacionUsuario, Clientes, Caracteristicas, Pedidos, Paradas, TiposParadas,Vehiculos, Choferes, LugaresComunes, Planificaciones, Turnos, Rutas, Visitas

import models as m

# Initialize Faker
fake = Faker()

# Database connection
DATABASE_URL = 'postgresql://fernando:123123123@db:5432/mides'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# URL to get Montevideo boundary as GeoJSON
OSM_BOUNDARY_URL = "https://nominatim.openstreetmap.org/search.php?q=Montevideo,Uruguay&polygon_geojson=1&format=json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# File paths for boundary data
BOUNDARY_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "montevideo_boundary.pickle")

def fetch_montevideo_boundary():
    """Fetch Montevideo's boundary polygon from OpenStreetMap"""
    print("Fetching Montevideo boundary from OpenStreetMap...")
    response = requests.get(OSM_BOUNDARY_URL, headers=HEADERS)

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch boundary: {response.status_code} - {response.text}")
    data = response.json()
    # Extract GeoJSON polygon from the response
    for item in data:
        if 'geojson' in item:
            boundary = shape(item['geojson'])  # Convert to Shapely polygon
            # Save to file
            with open(BOUNDARY_CACHE_FILE, 'wb') as f:
                pickle.dump(boundary, f)
            return boundary

    raise ValueError("Could not retrieve Montevideo's boundary")

def get_montevideo_boundary():
    """Get Montevideo boundary, loading from file if available or fetching from API if not"""
    if os.path.exists(BOUNDARY_CACHE_FILE):
        print("Loading Montevideo boundary from cache file...")
        try:
            with open(BOUNDARY_CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading boundary from file: {e}")
            # If there's an error loading, fetch from API
            return fetch_montevideo_boundary()
    else:
        return fetch_montevideo_boundary()

montevideo_boundary = get_montevideo_boundary()

def is_inside_montevideo(lat, lng):
    """Check if a coordinate is inside Montevideo"""
    point = Point(lng, lat)  # Shapely uses (lng, lat)
    return montevideo_boundary.contains(point)


def random_lat_lng_montevideo():
    """Generate random lat/lng inside Montevideo"""
    min_lat, max_lat = -34.927, -34.797
    min_lng, max_lng = -56.256, -56.053

    while True:
        lat = random.uniform(min_lat, max_lat)
        lng = random.uniform(min_lng, max_lng)

        if is_inside_montevideo(lat, lng):
            return lat, lng 
        else:
            print(f"Generated point ({lat}, {lng}) is outside Montevideo. Retrying...")


NAME_ALIAS_LIST = [
    {"name": "Alejandro",                 "alias": "Persona_01", "direction": None},
    {"name": "Sandra Zapata",             "alias": "Persona_02", "direction": "CENTRO ARTIGAS"},
    {"name": "Sandra Da Cruz",            "alias": "Persona_03", "direction": "CENTRO ARTIGAS"},
    {"name": "Graciela Alegre",           "alias": "Persona_04", "direction": "CENTRO ARTIGAS"},
    {"name": "Nelson Pereira",            "alias": "Persona_05", "direction": "ETNA 5958"},
    {"name": "José Enrique Dos Santos",   "alias": "Persona_06", "direction": "ALBANIA 3680"},
    {"name": "Martín González",           "alias": "Persona_07", "direction": "SECCO ILLA 2818"},
    {"name": "Matías Nuñez",              "alias": "Persona_08", "direction": "25 DE MAYO 177 AP2"},
    {"name": "Sheila Casuriaga",          "alias": "Persona_09", "direction": "J.CASTRO 4424"},
    {"name": "Lucía Vega",                "alias": "Persona_10", "direction": "L. BATLLE BERRES 3975"},
    {"name": "Cecilia Casanova",          "alias": "Persona_11", "direction": "PASAJE DENIS 3444"},
    {"name": "Andrés",                    "alias": "Persona_12", "direction": None},
    {"name": "Marta Trujillo",            "alias": "Persona_13", "direction": "LAFONE 2261"},
    {"name": "Jorge Silvera",             "alias": "Persona_14", "direction": "EUSEBIO CABRAL 4250"},
    {"name": "Pablo Chavat",              "alias": "Persona_15", "direction": "BUSTAMANTE Y GUERRA 2666 AP 1"},
    {"name": "Ari Castillo",              "alias": "Persona_16", "direction": "A. DUFORT Y ALVAREZ 3217 AP 2"},
    {"name": "José Perovich",             "alias": "Persona_17", "direction": "FRAGUOSO DE RIVERA 1447 AP 2"},
    {"name": "Miguel Almeida",            "alias": "Persona_18", "direction": "CENTRO ARTIGAS"},
    {"name": "Leticia Anesetti",          "alias": "Persona_19", "direction": "BATLLE Y ORDOÑEZ 2462 E AZARA"},
    {"name": "Néstor Hernández",          "alias": "Persona_20", "direction": "TEOFILO DIAZ 1624  E AP. SARAVIA"},
]

# Define request entries for each persona
REQUESTS = [
    # Solo ida entries:
   {"anon_id": "Persona_15", "tipo": "solo_ida", "name": "Pablo Chavat", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "BUSTAMANTE Y GUERRA 2666 AP 1", "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA Y PEDRO FIGARI", "ventana_inicio": "08:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_16", "tipo": "solo_ida", "name": "Ari Castillo", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "A. DUFORT Y ALVAREZ 3217 AP 2", "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA",                   "ventana_inicio": "08:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_19", "tipo": "solo_ida", "name": "Leticia Anesetti", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ESCUELA ROOSEVELT", "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": " BATLLE Y ORDOÑEZ 2462 E AZARA", "ventana_inicio": "16:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_20", "tipo": "solo_ida", "name": "Néstor Hernández", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "MAR DEL PLATA ", "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "TEOFILO DIAZ 1624 E AP. SARAVIA",    "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    # Ida y vuelta entries:

    {"anon_id": "Persona_02", "tipo": "ida_y_vuelta", "name": "Sandra Zapata", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "H. CLINICAS",         "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_03", "tipo": "ida_y_vuelta", "name": "Sandra Da Cruz", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "H. CLINICAS INT",     "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_04", "tipo": "ida_y_vuelta", "name": "Graciela Alegre", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "H. CLINICAS",         "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "CENTRO ARTIGAS",       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_05", "tipo": "ida_y_vuelta", "name": "Nelson Pereira", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ETNA 5958",           "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MEC",                 "ventana_inicio": "08:00", "ventana_fin": "14:00"},
        {"pos": 3, "coords": (None, None), "direction": "ETNA 5958",           "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_06", "tipo": "ida_y_vuelta", "name": "José Enrique Dos Santos", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "RINCON 575 TRABAJO",  "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "E. ALSACIA Y C. NERY", "ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "RINCON 575 TRABAJO",  "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_07", "tipo": "ida_y_vuelta", "name": "Martín González", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "SECCO ILLA 2818",     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "RINCON 640 BID",      "ventana_inicio": "09:00", "ventana_fin": "17:00"},
        {"pos": 3, "coords": (None, None), "direction": "SECCO ILLA 2818",     "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_08", "tipo": "ida_y_vuelta", "name": "Matías Nuñez", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "25 DE MAYO 177 AP2 E MACIEL",   "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": " CASTRO Y PENA","ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "25 DE MAYO 177 AP2 E MACIEL",   "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_09", "tipo": "ida_y_vuelta", "name": "Sheila Casuriaga", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "J.CASTRO 4424",       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CASTRO Y PENA",       "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "J.CASTRO 4424",       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_10", "tipo": "ida_y_vuelta", "name": "Lucía Vega", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "L. BATLLE BERRES 3975 E LUIS DE LA PEÑA","ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CASTRO Y PENA",       "ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "L. BATLLE BERRES 3975 E LUIS DE LA PEÑA","ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_11", "tipo": "ida_y_vuelta", "name": "Cecilia Casanova", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "PASAJE DENIS 3444 e CAPURRO",  "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MEC",          "ventana_inicio": "10:00", "ventana_fin": "16:00"},
        {"pos": 3, "coords": (None, None), "direction": "PASAJE DENIS 3444 e CAPURRO",  "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_13", "tipo": "ida_y_vuelta", "name": "Marta Trujillo", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "LAFONE 2261 E. CIBILS",         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "H. CLINICAS",          "ventana_inicio": "08:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "LAFONE 2261 E. CIBILS",         "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_14", "tipo": "ida_y_vuelta", "name": "Jorge Silvera", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "EUSEBIO CABRAL 4250 E F MAGARIÑOS","ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA",       "ventana_inicio": "19:00", "ventana_fin": "18:00"},
        {"pos": 3, "coords": (None, None), "direction": "EUSEBIO CABRAL 4250 E F MAGARIÑOS","ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_17", "tipo": "ida_y_vuelta", "name": "José Perovich", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "FRAGUOSO DE RIVERA 1447 e BAUZA","ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENATT",        "ventana_inicio": "11:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "FRAGUOSO DE RIVERA 1447 e BAUZA","ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_18", "tipo": "ida_y_vuelta", "name": "Miguel Almeida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "H. PASTEUR",         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENTRO ARTIGAS",     "ventana_inicio": "12:00", "ventana_fin": "13:30"},
        {"pos": 3, "coords": (None, None), "direction": "H. PASTEUR",         "ventana_inicio": None,   "ventana_fin": None},
    ]},
]

# List of clients with placeholders for DB insertion
for c in NAME_ALIAS_LIST
    CLIENT = [
        {
            "documento": fake.unique.random_number(digits=8),
            "nombre": c["alias"].split("_")[0],
            "apellido": c["alias"].split("_")[1],
            "direccion": c["direction"]
        }
    ]
    for p in REQUESTS:
        if p['anon_id'] == c["alias"]:
            PEDIDO = [
                {
                    'cliente_documento': CLIENT[0]["documento"],
                    'prioridad':0,
                    'acompañante':random.choice([True, False]),
                    'tipo':p.tipo,
                    'fecha_programado': '2025-11-18 00:00:00',
                    'paradas': [
                        {
                            'posicion_en_pedido':pp['pos'],
                            'direccion': c["direction"] if c["direction"] else fake.address(),
                            'latitud': None,
                            'longitud': None,
                            'ventana_horaria_inicio':pp['ventana_inicio'],
                            'ventana_horaria_fin':pp['ventana_fin'],
                            'tipo': 'Hospital',
                            'observaciones': None
                        } 
                        for pp in p
                    ]
                }
            ]

            
NOASIGNADOS_NAME_ALIAS_LIST = [
    {"name": "Dolores Cedrani",           "alias": "Persona_21", "direction": "MILLAN 3135"},
    {"name": "Manuel Acevedo",            "alias": "Persona_22", "direction": "CENTRO ARTIGAS"},
    {"name": "María Fernanda Fernández",  "alias": "Persona_23", "direction": "ESTEBAN GARINO 4035"},
    {"name": "Lucas Adán Mazza",          "alias": "Persona_24", "direction": "TUCAN SOLAR 2"},
    {"name": "Graciela Saavedra",         "alias": "Persona_25", "direction": "P. CASTELINO 1590"},
    {"name": "Leonardo Fernández",        "alias": "Persona_26", "direction": "SANTA LUCIA 4451"},
    {"name": "Washington González",       "alias": "Persona_27", "direction": "CEIBAL Y PANDO"},
    {"name": "Lucía Barboza",             "alias": "Persona_28", "direction": "CARLOS DE LA VEGA 5514"},
    {"name": "Agustín Villavedra Ferrari","alias": "Persona_29", "direction": "MICHIGAN 1538"},
    {"name": "Felisa González",           "alias": "Persona_30", "direction": "L.A.DE HERRERA 1975/001"},
    {"name": "Mateo Techera",             "alias": "Persona_31", "direction": "MIDES 18 DE JULIO PJE H 1681"},
]

# List of non-asigned clients
NO_ASIGNADOS_CLIENTS = [
    {
        "documento": fake.unique.random_number(digits=8),
        "nombre": c["alias"].split("_")[0],
        "apellido": c["alias"].split("_")[1],
        "direccion": c["direction"]
    }
    for c in NOASIGNADOS_NAME_ALIAS_LIST
]

# Define requests for non-asignados
NO_ASIGNADOS_REQUESTS = [
    # Ida y vuelta (appear twice):
    {"anon_id": "Persona_21", "tipo": "ida_y_vuelta", "paradas": [  # Dolores Cedrani
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "08:00", "ventana_fin": "11:30"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_22", "tipo": "ida_y_vuelta", "paradas": [  # Manuel Acevedo
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_23", "tipo": "ida_y_vuelta", "paradas": [  # María Fernanda Fernández
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "12:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_24", "tipo": "ida_y_vuelta", "paradas": [  # Lucas Adán Mazza
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_25", "tipo": "ida_y_vuelta", "paradas": [  # Graciela Saavedra
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_26", "tipo": "ida_y_vuelta", "paradas": [  # Leonardo Fernández
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_30", "tipo": "ida_y_vuelta", "paradas": [  # Felisa González
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "14:30", "ventana_fin": "16:30"},
        {"pos": 3, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
    ]},

    # Solo ida (appear once):
    {"anon_id": "Persona_27", "tipo": "solo_ida", "paradas": [  # Washington González
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_28", "tipo": "solo_ida", "paradas": [  # Lucía Barboza
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "19:20", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_29", "tipo": "solo_ida", "paradas": [  # Agustín Villavedra Ferrari
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_31", "tipo": "solo_ida", "paradas": [  # Mateo Techera
        {"pos": 1, "coords": (None, None), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "ventana_inicio": "17:00", "ventana_fin": None},
    ]},
]