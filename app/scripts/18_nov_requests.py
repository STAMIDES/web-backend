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


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


NAME_ALIAS_LIST = [
    {"name": "Alejandro",                 "alias": "Persona_01", "direction": None},
    {"name": "Sandra Zapata",             "alias": "Persona_02", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Sandra Da Cruz",            "alias": "Persona_03", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Graciela Alegre",           "alias": "Persona_04", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
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
    {"name": "Miguel Almeida",            "alias": "Persona_18", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
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
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS",         "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_03", "tipo": "ida_y_vuelta", "name": "Sandra Da Cruz", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS",     "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_04", "tipo": "ida_y_vuelta", "name": "Graciela Alegre", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS",         "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
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
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS",          "ventana_inicio": "08:00", "ventana_fin": "12:00"},
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
        {"pos": 2, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),     "ventana_inicio": "12:00", "ventana_fin": "13:30"},
        {"pos": 3, "coords": (None, None), "direction": "H. PASTEUR",         "ventana_inicio": None,   "ventana_fin": None},
    ]},
]

NOASIGNADOS_NAME_ALIAS_LIST = [
    {"name": "Dolores Cedrani",           "alias": "Persona_21", "direction": "MILLAN 3135"},
    {"name": "Manuel Acevedo",            "alias": "Persona_22", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
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

# Define requests for non-asignados
NO_ASIGNADOS_REQUESTS = [
    # Ida y vuelta (appear twice):
    {"name": "Dolores Cedrani",           "anon_id": "Persona_21", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "MILLAN 3135",            "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "OSORIO 1370",           "ventana_inicio": "08:00", "ventana_fin": "11:30"},
        {"pos": 3, "coords": (None, None), "direction": "MILLAN 3135",            "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Manuel Acevedo",            "anon_id": "Persona_22", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENTRO CACHON",        "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "María Fernanda Fernández",  "anon_id": "Persona_23", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ESTEBAN GARINO 4035",   "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "ERNESTO CANTERO 802 ESCULA 200",    "ventana_inicio": "12:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "ESTEBAN GARINO 4035",   "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Lucas Adán Mazza",          "anon_id": "Persona_24", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "TUCAN SOLAR 2",         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644",        "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "TUCAN SOLAR 2",         "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Graciela Saavedra",         "anon_id": "Persona_25", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "P. CASTELINO 1590",    "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644",         "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "P. CASTELINO 1590",    "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Leonardo Fernández",        "anon_id": "Persona_26", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "SANTA LUCIA 4451",     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644 E CAPOAMOR","ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "SANTA LUCIA 4451",     "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Felisa González",           "anon_id": "Persona_30", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "L.A.DE HERRERA 1975/001","ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "I18 DE JULIO Y PABLO DE MARIA (IGLESIA)","ventana_inicio": "14:30", "ventana_fin": "16:30"},
        {"pos": 3, "coords": (None, None), "direction": "L.A.DE HERRERA 1975/001","ventana_inicio": None,   "ventana_fin": None},
    ]},

    # Solo ida (appear once):
    {"name": "Washington González",       "anon_id": "Persona_27", "tipo": "solo_ida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CEIBAL Y PANDO",     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "COOPERATIVA ZUNFELDE","ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"name": "Lucía Barboza",             "anon_id": "Persona_28", "tipo": "solo_ida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CARLOS DE LA VEGA 5514","ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "JOAQUIN REQUENA 3010",   "ventana_inicio": "19:20", "ventana_fin": None},
    ]},
    {"name": "Agustín Villavedra Ferrari","anon_id": "Persona_29", "tipo": "solo_ida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "FERRARI",        "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MICHIGAN 1538 E DECROLLI",            "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"name": "Mateo Techera",             "anon_id": "Persona_31", "tipo": "solo_ida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "MIDES 18 DE JULIO", "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "PJE H 1681 E A SARAVIA Y ALBENIZ",    "ventana_inicio": "17:00", "ventana_fin": None},
    ]},
]

def process_requests(name_alias_list, requests_list, db_session):
    """
    Process a list of clients and their corresponding requests
    
    Args:
        name_alias_list: List of client data with name, alias, and direction
        requests_list: List of request data with stops
        db_session: SQLAlchemy database session
    """
    clients = []
    # Create clients
    for c in name_alias_list:
        documento = fake.unique.random_number(digits=8)
        nombre = c["alias"].split("_")[0]
        apellido = c["alias"].split("_")[1]
        
        # Create client
        client = Clientes(
            documento=documento,
            nombre=nombre,
            apellido=apellido,
            direccion=c["direction"] if c["direction"] else fake.address(),
            observaciones=f"Client created from {c['name']}"
        )
        
        # Add client to session
        db_session.add(client)
        db_session.flush()
        clients.append(client)
        
        # Find matching requests for this client
        for p in requests_list:
            if p['anon_id'] == c["alias"]:
                # Create pedido (request)
                pedido = Pedidos(
                    cliente_documento=documento,
                    prioridad=0,
                    acompañante=random.choice([True, False]),
                    tipo=p['tipo'],
                    fecha_programado=datetime.strptime('2025-11-18', '%Y-%m-%d').date(),
                    observaciones=f"Request for {c['name']}"
                )
                db_session.add(pedido)
                db_session.flush()
                
                # Create paradas (stops)
                for parada_data in p['paradas']:
                    # Get coordinates if needed
                    lat, lng = None, None
                    if parada_data['coords'][0] is None:
                        # Try to get real coordinates for the address
                        try:
                            if parada_data['direction']:
                                # Here you could add a geocoding service to get lat/lng
                                # For now, just generate random coords in Montevideo
                                lat, lng = geocode()
                            else:
                                lat, lng = geocode()
                        except Exception as e:
                            print(f"Error geocoding address: {e}")
                            lat, lng = geocode()
                    else:
                        lat, lng = parada_data['coords']
                    
                    # Find or create tipo parada
                    tipo_id = db_session.query(TiposParadas).filter_by(nombre='Hospital').first().id
                    
                    # Create parada
                    parada = Paradas(
                        id_pedido=pedido.id,
                        posicion_en_pedido=parada_data['pos'],
                        direccion=parada_data.get('direction', c["direction"]) or fake.address(),
                        latitud=lat,
                        longitud=lng,
                        ventana_horaria_inicio=parada_data['ventana_inicio'],
                        ventana_horaria_fin=parada_data['ventana_fin'],
                        tipo=tipo_id,
                        observaciones=None
                    )
                    db_session.add(parada)
    
    db_session.commit()
    return clients

def geocode_address(address):
    """
    Geocode an address using Nominatim OpenStreetMap API (similar to geocoder.jsx)
    
    Args:
        address: Address string to geocode
        
    Returns:
        tuple: (latitude, longitude, display_name) or None if geocoding fails
    """
    print(f"Geocoding address: {address}")
    formatted_address = address.replace(" ", "+")
    url = f"https://nominatim.openstreetmap.org/search.php?street={formatted_address}&city=Montevideo&country=Uruguay&format=jsonv2"
    
    try:
        # Add delay to respect Nominatim usage policy
        time.sleep(1)  
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Return the first result
                lat = float(data[0]['lat'])
                lng = float(data[0]['lon'])
                display_name = data[0]['display_name']
                print(f"Found coordinates: {lat}, {lng}")
                print(f"Location: {display_name}")
                return (lat, lng, display_name)
            else:
                print(f"No coordinates found for address: {address}")
                return None
        else:
            print(f"Error in geocoding request: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during geocoding: {e}")
        return None

def geocode():
    """Generate random coordinates in Montevideo area (fallback)"""
    # Montevideo approximate bounding box
    lat = random.uniform(-34.94, -34.80)
    lng = random.uniform(-56.22, -56.05)
    return (lat, lng)

def save_coords_to_file(direction, lat, lng, filename="geocoded_addresses.txt"):
    """
    Append geocoded coordinates to a file
    
    Args:
        direction: Address that was geocoded
        lat: Latitude
        lng: Longitude
        filename: Output filename
    """
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{direction},{lat},{lng}\n")
    print(f"Saved coordinates for {direction} to {filename}")

def process_requests_interactive(name_alias_list, requests_list, db_session=None):
    """
    Process requests interactively, asking user to confirm geocoded coordinates
    
    Args:
        name_alias_list: List of client data with name, alias, and direction
        requests_list: List of request data with stops
        db_session: Optional SQLAlchemy database session for database operations
    """
    should_process_db = db_session is not None
    
    for c in name_alias_list:
        # Find matching requests for this client
        for p in requests_list:
            if p['anon_id'] == c["alias"]:
                print(f"\nProcessing request for {p['name']} ({c['alias']})")
                
                # Create pedido (request) if we're processing the database
                if should_process_db:
                    documento = fake.unique.random_number(digits=8)
                    nombre = c["alias"].split("_")[0]
                    apellido = c["alias"].split("_")[1]
                    
                    # Create client
                    client = Clientes(
                        documento=documento,
                        nombre=nombre,
                        apellido=apellido,
                        direccion=c["direction"] if c["direction"] else fake.address(),
                        observaciones=f"Client created from {c['name']}"
                    )
                    
                    db_session.add(client)
                    db_session.flush()
                    
                    pedido = Pedidos(
                        cliente_documento=documento,
                        prioridad=0,
                        acompañante=random.choice([True, False]),
                        tipo=p['tipo'],
                        fecha_programado=datetime.strptime('2025-11-18', '%Y-%m-%d').date(),
                        observaciones=f"Request for {c['name']}"
                    )
                    db_session.add(pedido)
                    db_session.flush()
                
                # Process each parada
                for parada_data in p['paradas']:
                    direction = parada_data['direction']
                    if not direction:
                        direction = c["direction"]
                        if not direction:
                            print(f"Warning: No direction available for parada {parada_data['pos']}")
                            if should_process_db:
                                direction = fake.address()
                            else:
                                continue
                    
                    # If coords are None, geocode the address
                    if parada_data['coords'][0] is None:
                        result = geocode_address(direction)
                        
                        if result:
                            lat, lng, display_name = result
                            
                            # Ask user for confirmation
                            print(f"\nFor {p['name']}, parada {parada_data['pos']}:")
                            print(f"Direction: {direction}")
                            print(f"Geocoded to: {lat}, {lng}")
                            print(f"Location: {display_name}")
                            
                            confirm = input("Are these coordinates correct? (y/n): ")
                            
                            if confirm.lower() in ['y', 'yes']:
                                # Save the confirmed coordinates to file
                                save_coords_to_file(direction, lat, lng)
                                
                                # Update parada_data with the new coordinates
                                parada_data['coords'] = (lat, lng)
                                
                                # Create parada in database if we're processing it
                                if should_process_db:
                                    tipo_id = db_session.query(TiposParadas).filter_by(nombre='Hospital').first().id
                                    
                                    parada = Paradas(
                                        id_pedido=pedido.id,
                                        posicion_en_pedido=parada_data['pos'],
                                        direccion=direction,
                                        latitud=lat,
                                        longitud=lng,
                                        ventana_horaria_inicio=parada_data['ventana_inicio'],
                                        ventana_horaria_fin=parada_data['ventana_fin'],
                                        tipo=tipo_id,
                                        observaciones=None
                                    )
                                    db_session.add(parada)
                            else:
                                print("Coordinates not confirmed. Exiting.")
                                return False
                        else:
                            print(f"Failed to geocode: {direction}")
                            print("Coordinates not provided. Exiting.")
                            return False
                    else:
                        # Coords already exist
                        lat, lng = parada_data['coords']
                        if should_process_db:
                            tipo_id = db_session.query(TiposParadas).filter_by(nombre='Hospital').first().id
                            
                            parada = Paradas(
                                id_pedido=pedido.id,
                                posicion_en_pedido=parada_data['pos'],
                                direccion=direction,
                                latitud=lat,
                                longitud=lng,
                                ventana_horaria_inicio=parada_data['ventana_inicio'],
                                ventana_horaria_fin=parada_data['ventana_fin'],
                                tipo=tipo_id,
                                observaciones=None
                            )
                            db_session.add(parada)
    
    if should_process_db:
        db_session.commit()
    
    return True

def main():
    db = SessionLocal()
    
    # Check if TiposParadas exists, if not create them
    if db.query(TiposParadas).count() == 0:
        print("Creating TiposParadas...")
        tipos = [
            TiposParadas(nombre='Hospital'),
            TiposParadas(nombre='Particular'),
            TiposParadas(nombre='Mides')
        ]
        db.add_all(tipos)
        db.commit()
    
    # Process regular requests
    print("Processing regular requests...")
    process_requests(NAME_ALIAS_LIST, REQUESTS, db)
    
    # Process non-assigned requests
    print("Processing non-assigned requests...")
    process_requests(NOASIGNADOS_NAME_ALIAS_LIST, NO_ASIGNADOS_REQUESTS, db)
    
    print("All requests processed successfully!")
    db.close()

def interactive_main():
    """Main function for interactive geocoding"""
    # Create geocoded_addresses.txt file or clear it if it exists
    with open("geocoded_addresses.txt", 'w', encoding='utf-8') as f:
        f.write("direction,latitude,longitude\n")
    
    print("Starting interactive geocoding process...")
    
    # Process without database operations first to confirm all geocodes
    print("\nGathering and confirming coordinates...")
    success = process_requests_interactive(NAME_ALIAS_LIST, REQUESTS)
    
    if not success:
        print("Geocoding process interrupted.")
        return
    
    success = process_requests_interactive(NOASIGNADOS_NAME_ALIAS_LIST, NO_ASIGNADOS_REQUESTS)
    
    if not success:
        print("Geocoding process interrupted.")
        return
    
    # Ask if user wants to proceed with database operations
    proceed = input("\nAll coordinates confirmed. Proceed with database operations? (y/n): ")
    
    if proceed.lower() in ['y', 'yes']:
        db = SessionLocal()
        
        # Check if TiposParadas exists, if not create them
        if db.query(TiposParadas).count() == 0:
            print("Creating TiposParadas...")
            tipos = [
                TiposParadas(nombre='Hospital'),
                TiposParadas(nombre='Particular'),
                TiposParadas(nombre='Mides')
            ]
            db.add_all(tipos)
            db.commit()
        
        # Process with database operations
        print("Processing requests for database...")
        process_requests_interactive(NAME_ALIAS_LIST, REQUESTS, db)
        process_requests_interactive(NOASIGNADOS_NAME_ALIAS_LIST, NO_ASIGNADOS_REQUESTS, db)
        
        print("All requests processed successfully!")
        db.close()
    else:
        print("Database operations skipped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process requests with geocoding')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode with geocoding')
    args = parser.parse_args()
    
    if args.interactive:
        interactive_main()
    else:
        main()