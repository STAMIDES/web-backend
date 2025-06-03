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
    "User-Agent": "FING-Tesis-TransportApp/1.0 (universidad.edu.uy; contact@example.edu.uy)"
}


NAME_ALIAS_LIST = [
    {"name": "Alejandro",                 "alias": "Persona_01", "direction": None},
    {"name": "Sandra Zapata",             "alias": "Persona_02", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Sandra Da Cruz",            "alias": "Persona_03", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Graciela Alegre",           "alias": "Persona_04", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Nelson Pereira",            "alias": "Persona_05", "direction": "ETNA 5958", "coords": (-34.8907642,-56.151988)},
    {"name": "José Enrique Dos Santos",   "alias": "Persona_06", "direction": "ALBANIA 3680", "coords": (-34.8384248,-56.1303124)},
    {"name": "Martín González",           "alias": "Persona_07", "direction": "SECCO ILLA 2818", "coords": (-34.8878782,-56.1569264)},
    {"name": "Matías Nuñez",              "alias": "Persona_08", "direction": "25 DE MAYO 177 AP2"},
    {"name": "Sheila Casuriaga",          "alias": "Persona_09", "direction": "J.CASTRO 4424"},
    {"name": "Lucía Vega",                "alias": "Persona_10", "direction": "L. BATLLE BERRES 3975"},
    {"name": "Cecilia Casanova",          "alias": "Persona_11", "direction": "PASAJE DENIS 3444", "coords": (-34.8721728,-56.2117647)},
    {"name": "Andrés",                    "alias": "Persona_12", "direction": None},
    {"name": "Marta Trujillo",            "alias": "Persona_13", "direction": "LAFONE 2261", "coords": (-34.8676117,-56.2660573)},
    {"name": "Jorge Silvera",             "alias": "Persona_14", "direction": "EUSEBIO CABRAL 4250", "coords": (-34.8067564,-56.1405338)},
    {"name": "Pablo Chavat",              "alias": "Persona_15", "direction": "BUSTAMANTE Y GUERRA 2666", "coords": (-34.847555,-56.1917605)},
    {"name": "Ari Castillo",              "alias": "Persona_16", "direction": "Dufort y Álvarez 3217", "coords": (-34.8714755,-56.2016308)},
    {"name": "José Perovich",             "alias": "Persona_17", "direction": "FRAGUOSO DE RIVERA 1447"},
    {"name": "Miguel Almeida",            "alias": "Persona_18", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "Leticia Anesetti",          "alias": "Persona_19", "direction": "BATLLE Y ORDOÑEZ 2462"},
    {"name": "Néstor Hernández",          "alias": "Persona_20", "direction": "TEOFILO DIAZ 1624", "coords": (-34.8124901,-56.2242052)},
]

# Define request entries for each persona
REQUESTS = [
    # Solo ida entries:
   {"anon_id": "Persona_15", "tipo": "solo_ida", "name": "Pablo Chavat", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "BUSTAMANTE Y GUERRA 2666", "coords": (-34.847555,-56.1917605), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA", "coords": (-34.8862235,-56.049549),  "ventana_inicio": "08:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_16", "tipo": "solo_ida", "name": "Ari Castillo", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Dufort y Álvarez 3217", "coords": (-34.8714755,-56.2016308), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA", "coords": (-34.8862235,-56.049549),  "coords": (-34.8862235,-56.049549),                   "ventana_inicio": "08:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_19", "tipo": "solo_ida", "name": "Leticia Anesetti", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ESCUELA ROOSEVELT", "coords": (-34.84776542, -56.1993598),         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": " BATLLE Y ORDOÑEZ 2462", "coords": (-34.8842043,-56.1409093), "ventana_inicio": "16:00", "ventana_fin": None},
    ]},
    {"anon_id": "Persona_20", "tipo": "solo_ida", "name": "Néstor Hernández", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "MAR DEL PLATA ", "coords": (-34.8862235,-56.049549), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "TEOFILO DIAZ 1624", "coords": (-34.8124901,-56.2242052),    "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    # Ida y vuelta entries:

    {"anon_id": "Persona_02", "tipo": "ida_y_vuelta", "name": "Sandra Zapata", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS", "coords": (-34.8907642,-56.151988),         "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_03", "tipo": "ida_y_vuelta", "name": "Sandra Da Cruz", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS", "coords": (-34.8907642,-56.151988),     "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_04", "tipo": "ida_y_vuelta", "name": "Graciela Alegre", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS", "coords": (-34.8907642,-56.151988),         "ventana_inicio": "09:00", "ventana_fin": "10:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_05", "tipo": "ida_y_vuelta", "name": "Nelson Pereira", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ETNA 5958", "coords": (-34.8907642,-56.151988),           "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MEC", "coords": (-34.9088357,-56.2036013),                 "ventana_inicio": "08:00", "ventana_fin": "14:00"},
        {"pos": 3, "coords": (None, None), "direction": "ETNA 5958", "coords": (-34.8907642,-56.151988),           "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_06", "tipo": "ida_y_vuelta", "name": "José Enrique Dos Santos", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "ALBANIA 3680", "coords": (-34.8384248,-56.1303124), "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "RINCON 575", "coords": (-34.9059757,-56.2037552), "ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "ALBANIA 3680", "coords": (-34.8384248,-56.1303124), "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_07", "tipo": "ida_y_vuelta", "name": "Martín González", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "SECCO ILLA 2818", "coords": (-34.8878782,-56.1569264),     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "RINCON 640", "coords": (-34.9058095,-56.2024165),      "ventana_inicio": "09:00", "ventana_fin": "17:00"},
        {"pos": 3, "coords": (None, None), "direction": "SECCO ILLA 2818", "coords": (-34.8878782,-56.1569264),     "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_08", "tipo": "ida_y_vuelta", "name": "Matías Nuñez", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "25 DE MAYO 177", "coords": (-34.9058556,-56.2055855),   "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENATT", "coords": (-34.8559056, -56.2111829), "ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "25 DE MAYO 177", "coords": (-34.9058556,-56.2055855),   "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_09", "tipo": "ida_y_vuelta", "name": "Sheila Casuriaga", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "JOSE CASTRO 4424", "coords": (-34.863964,-56.2374515),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENATT", "coords": (-34.8559056, -56.2111829),      "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "JOSE CASTRO 4424", "coords": (-34.863964,-56.2374515),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_10", "tipo": "ida_y_vuelta", "name": "Lucía Vega", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "LUIS BATLLE BERRES 3975", "coords": (-34.8631794,-56.2189609),"ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENATT", "coords": (-34.8559056, -56.2111829),      "ventana_inicio": "09:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "LUIS BATLLE BERRES 3975", "coords": (-34.8631794,-56.2189609),"ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_11", "tipo": "ida_y_vuelta", "name": "Cecilia Casanova", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "PASAJE DENIS 3444", "coords": (-34.8721728,-56.2117647),  "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MEC", "coords": (-34.9088357,-56.2036013),          "ventana_inicio": "10:00", "ventana_fin": "16:00"},
        {"pos": 3, "coords": (None, None), "direction": "PASAJE DENIS 3444", "coords": (-34.8721728,-56.2117647),  "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_13", "tipo": "ida_y_vuelta", "name": "Marta Trujillo", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "LAFONE 2261", "coords": (-34.8676117,-56.2660573),         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "HOSPITAL CLINICAS", "coords": (-34.8907642,-56.151988),          "ventana_inicio": "08:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "LAFONE 2261", "coords": (-34.8676117,-56.2660573),         "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_14", "tipo": "ida_y_vuelta", "name": "Jorge Silvera", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "EUSEBIO CABRAL 4250", "coords": (-34.8067564,-56.1405338),"ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MAR DEL PLATA", "coords": (-34.8862235,-56.049549),  "coords": (-34.8862235,-56.049549),       "ventana_inicio": "19:00", "ventana_fin": "18:00"},
        {"pos": 3, "coords": (None, None), "direction": "EUSEBIO CABRAL 4250", "coords": (-34.8067564,-56.1405338),"ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_17", "tipo": "ida_y_vuelta", "name": "José Perovich", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "FRAGOSO DE RIVERA 1447", "coords": (-34.900863,-56.1427272),"ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENATT", "coords": (-34.8559056, -56.2111829),       "ventana_inicio": "11:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "FRAGOSO DE RIVERA 1447", "coords": (-34.900863,-56.1427272),"ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"anon_id": "Persona_18", "tipo": "ida_y_vuelta", "name": "Miguel Almeida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Hospital PASTEUR", "coords": (-34.874641349, -56.13815964),         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),     "ventana_inicio": "12:00", "ventana_fin": "13:30"},
        {"pos": 3, "coords": (None, None), "direction": "Hospital PASTEUR", "coords": (-34.874641349, -56.13815964),         "ventana_inicio": None,   "ventana_fin": None},
    ]},
]

NOASIGNADOS_NAME_ALIAS_LIST = [
    {"name": "Dolores Cedrani",           "alias": "Persona_21", "direction": "MILLAN 3135", "coords": (-34.8691288,-56.1917533)},
    {"name": "Manuel Acevedo",            "alias": "Persona_22", "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738)},
    {"name": "María Fernanda Fernández",  "alias": "Persona_23", "direction": "ESTEBAN GARINO 4035"},
    {"name": "Lucas Adán Mazza",          "alias": "Persona_24", "direction": "TUCAN SOLAR 2"},
    {"name": "Graciela Saavedra",         "alias": "Persona_25", "direction": "P. CASTELINO 1590"},
    {"name": "Leonardo Fernández",        "alias": "Persona_26", "direction": "SANTA LUCIA 4451", "coords": (-34.8517945,-56.2259483)},
    {"name": "Washington González",       "alias": "Persona_27", "direction": "CEIBAL Y PANDO"},
    {"name": "Lucía Barboza",             "alias": "Persona_28", "direction": "CARLOS DE LA VEGA 5514", "coords": (-34.843499,-56.2475771)},
    {"name": "Agustín Villavedra Ferrari","alias": "Persona_29", "direction": "MICHIGAN 1538", "coords": (-34.8932961,-56.0995063)},
    {"name": "Felisa González",           "alias": "Persona_30", "direction": "L.A.DE HERRERA 1975/001"},
    {"name": "Mateo Techera",             "alias": "Persona_31", "direction": "MIDES 18 DE JULIO PJE H 1681"},
]

# Define requests for non-asignados
NO_ASIGNADOS_REQUESTS = [
    # Ida y vuelta (appear twice):
    {"name": "Dolores Cedrani",           "anon_id": "Persona_21", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "MILLAN 3135", "coords": (-34.8691288,-56.1917533),            "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "OSORIO 1370", "coords": (-34.9030399,-56.1432635),           "ventana_inicio": "08:00", "ventana_fin": "11:30"},
        {"pos": 3, "coords": (None, None), "direction": "MILLAN 3135", "coords": (-34.8691288,-56.1917533),            "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Manuel Acevedo",            "anon_id": "Persona_22", "tipo": "ida_y_vuelta", "paradas": [ #-34.86224133547303, -56.17270809445308
        {"pos": 1, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "CENTRO CACHON", "coords": (-34.8622413, -56.1727080),        "ventana_inicio": "09:00", "ventana_fin": "12:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cno. Maldonado 5745", "coords": (-34.8413565,-56.1241738),       "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "María Fernanda Fernández",  "anon_id": "Persona_23", "tipo": "ida_y_vuelta", "paradas": [ 
        {"pos": 1, "coords": (None, None), "direction": "ESTEBAN GARINO 4035", "coords": (-34.8220761, -56.1111872),   "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "ERNESTO HERRERA 802 ESCULA 200", "coords": (-34.8485410, -56.2016107),    "ventana_inicio": "12:00", "ventana_fin": "15:00"},
        {"pos": 3, "coords": (None, None), "direction": "ESTEBAN GARINO 4035", "coords": (-34.8220761, -56.1111872),   "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Lucas Adán Mazza",          "anon_id": "Persona_24", "tipo": "ida_y_vuelta", "paradas": [ #-34.821819712754696, -56.09655532768871
        {"pos": 1, "coords": (None, None), "direction": "Cam. Guerra & Pje. Tucan", "coords": (-34.8218197, -56.0965553),         "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644", "coords": (-34.8682487,-56.1164326),        "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "Cam. Guerra & Pje. Tucan", "coords": (-34.8218197, -56.0965553),         "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Graciela Saavedra",         "anon_id": "Persona_25", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "Dr. Pedro Castellino 1590", "coords": (-34.8728843,-56.2493801),    "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644", "coords": (-34.8682487,-56.1164326),         "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "Dr. Pedro Castellino 1590", "coords": (-34.8728843,-56.2493801),    "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Leonardo Fernández",        "anon_id": "Persona_26", "tipo": "ida_y_vuelta", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "SANTA LUCIA 4451", "coords": (-34.8517945,-56.2259483),     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MURILLO 2644", "coords": (-34.8682487,-56.1164326), "ventana_inicio": "10:00", "ventana_fin": "13:00"},
        {"pos": 3, "coords": (None, None), "direction": "SANTA LUCIA 4451", "coords": (-34.8517945,-56.2259483),     "ventana_inicio": None,   "ventana_fin": None},
    ]},
    {"name": "Felisa González",           "anon_id": "Persona_30", "tipo": "ida_y_vuelta", "paradas": [ #-34.90009435616584, -56.17199949600856
        {"pos": 1, "coords": (None, None), "direction": "LUIS ALBERTO DE HERRERA 1975", "coords": (-34.8909472,-56.1463869),"ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "18 DE JULIO Y PABLO DE MARIA (IGLESIA)", "coords": (-34.9000944,-56.1719995),"ventana_inicio": "14:30", "ventana_fin": "16:30"},
        {"pos": 3, "coords": (None, None), "direction": "LUIS ALBERTO DE HERRERA 1975", "coords": (-34.8909472,-56.1463869),"ventana_inicio": None,   "ventana_fin": None},
    ]},

    # Solo ida (appear once):
    {"name": "Washington González",       "anon_id": "Persona_27", "tipo": "solo_ida", "paradas": [ #-34.877647300528196, -56.101099947513475
        {"pos": 1, "coords": (None, None), "direction": "CEIBAL Y PANDO",  "coords": (-34.8743719, -56.1814490),     "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "COOPERATIVA ZUNFELDE", "coords": (-34.8776473, -56.1010999),  "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"name": "Lucía Barboza",             "anon_id": "Persona_28", "tipo": "solo_ida", "paradas": [
        {"pos": 1, "coords": (None, None), "direction": "CARLOS DE LA VEGA 5514", "coords": (-34.843499,-56.2475771),"ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "JOAQUIN REQUENA 3010", "coords": (-34.8719449,-56.173083),   "ventana_inicio": "19:20", "ventana_fin": None},
    ]},
    {"name": "Agustín Villavedra Ferrari","anon_id": "Persona_29", "tipo": "solo_ida", "paradas": [#-34.891740000536004, -56.06200370935419
        {"pos": 1, "coords": (None, None), "direction": "FERRARI", "coords": (-34.8919893,-56.0626356),        "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "MICHIGAN 1538", "coords": (-34.8932961,-56.0995063),            "ventana_inicio": "18:00", "ventana_fin": None},
    ]},
    {"name": "Mateo Techera",             "anon_id": "Persona_31", "tipo": "solo_ida", "paradas": [ #-34.8093014397971, -56.23183956826869
        {"pos": 1, "coords": (None, None), "direction": "MIDES 18 DE JULIO", "coords": (-34.9049807,-56.1851187),  "ventana_inicio": None,   "ventana_fin": None},
        {"pos": 2, "coords": (None, None), "direction": "PJE H 1681 E A SARAVIA Y ALBENIZ",  "coords": (-34.8093014,-56.2318396),    "ventana_inicio": "17:00", "ventana_fin": None},
    ]},
]

# Cache for storing geocoded addresses to avoid redundant requests
geocode_cache = {}
# Try to load existing cache from file
try:
    with open("geocode_cache.pkl", "rb") as f:
        geocode_cache = pickle.load(f)
    print(f"Loaded {len(geocode_cache)} cached addresses")
except FileNotFoundError:
    print("No existing geocode cache found, creating new cache")

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
    # Check if address is already in cache
    if address in geocode_cache:
        print(f"Using cached coordinates for: {address}")
        return geocode_cache[address]
    
    print(f"Geocoding address: {address}")
    formatted_address = address.replace(" ", "+")
    url = f"https://nominatim.openstreetmap.org/search.php?street={formatted_address}&city=Montevideo&country=Uruguay&format=jsonv2"
    
    try:
        # Add delay to respect Nominatim usage policy (maximum 1 request per second)
        time.sleep(1.1)  # Slightly more than 1 second to be safe
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
                
                # Save to cache
                result = (lat, lng, display_name)
                geocode_cache[address] = result
                
                # Save updated cache to file
                with open("geocode_cache.pkl", "wb") as f:
                    pickle.dump(geocode_cache, f)
                
                print("Data is © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright")
                return result
            else:
                print(f"No coordinates found for address: {address}")
                return None
        else:
            print(f"Error in geocoding request: {response.status_code}")
            if response.status_code == 403:
                print("Received 403 Forbidden - Check your User-Agent and ensure you're not exceeding rate limits")
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

def save_coords_to_file(direction, lat, lng, filename=None):
    """
    Update the coordinates directly in this script file
    
    Args:
        direction: Address that was geocoded
        lat: Latitude
        lng: Longitude
        filename: Ignored (kept for compatibility)
    """
    # Get the path to this script file
    script_path = os.path.abspath(__file__)
    
    try:
        # Read the current file content
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the address in the file and update coordinates
        # Pattern for address without coords
        pattern1 = f'\"direction\": \"{direction}\"'
        pattern2 = f'\"direction\": \"{direction}\", \"coords\":'
        
        # If we find the pattern with no coords, add them
        if pattern1 in content and pattern2 not in content:
            updated_content = content.replace(
                f'\"direction\": \"{direction}\"', 
                f'\"direction\": \"{direction}\", \"coords\": ({lat},{lng})'
            )
        # If we find the pattern with existing coords, update them
        elif pattern2 in content:
            # Use regex to find and replace the coordinates
            import re
            coords_pattern = f'\"direction\": \"{direction}\", \"coords\": \\([^)]+\\)'
            replacement = f'\"direction\": \"{direction}\", \"coords\": ({lat},{lng})'
            updated_content = re.sub(coords_pattern, replacement, content)
        # If neither pattern is found, no changes are made
        else:
            print(f"Warning: Could not find the address \"{direction}\" in the script file.")
            return
        
        # Write the updated content back to the file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Successfully updated coordinates for \"{direction}\" in the script file.")
    except Exception as e:
        print(f"Error updating coordinates in script file: {e}")
        # Fallback to the original behavior
        with open("geocoded_addresses.txt", 'a', encoding='utf-8') as f:
            f.write(f"{direction},{lat},{lng}\n")
        print(f"Saved coordinates to geocoded_addresses.txt instead")

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