from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from faker import Faker
import sys
import os
import argparse
import requests
from shapely.geometry import Point, shape
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Usuarios, RefreshToken, InvitacionUsuario, Clientes, Caracteristicas, Pedidos, Paradas, TiposParadas,Vehiculos, Choferes, LugaresComunes, Planificaciones, Turnos, Rutas, RutasTurnos, Visitas

import models as m

# Initialize Faker
fake = Faker()

# Database connection
DATABASE_URL = 'postgresql://fernando:123123123@db:5432/mides'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


## GET COORDS EN MONTEVIDEO

# URL to get Montevideo boundary as GeoJSON
OSM_BOUNDARY_URL = "https://nominatim.openstreetmap.org/search.php?q=Montevideo,Uruguay&polygon_geojson=1&format=json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_montevideo_boundary():
    """Fetch Montevideo's boundary polygon from OpenStreetMap"""
    response = requests.get(OSM_BOUNDARY_URL, headers=HEADERS)

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch boundary: {response.status_code} - {response.text}")
    data = response.json()
    # Extract GeoJSON polygon from the response
    for item in data:
        if 'geojson' in item:
            return shape(item['geojson'])  # Convert to Shapely polygon

    raise ValueError("Could not retrieve Montevideo's boundary")

# Fetch boundary once
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
# Generate random lat/lng inside Montevideo

def create_sample_data():
    db = SessionLocal()

    # # Create Users
    # users = []
    # for _ in range(10):
    #     user = Usuarios(
    #         email=fake.email(),
    #         hashed_password=fake.sha256(),
    #         nombre=fake.name(),
    #         rol=random.choice(list(m.TipoUsuario))
    #     )
    #     db.add(user)
    #     users.append(user)
    
    # Create Refresh Tokens
    # for user in users:
    #     refresh_token = RefreshToken(
    #         token=fake.uuid4(),
    #         user_id=user.id,
    #         expires_at=datetime.now() + timedelta(days=30)
    #     )
    #     db.add(refresh_token)

    # # Create Invitations
    # for _ in range(5):
    #     invitation = InvitacionUsuario(
    #         hash_link=fake.sha256(),
    #         email=fake.email(),
    #         nombre=fake.name(),
    #         rol=random.choice(["admin", "user"])
    #     )
    #     db.add(invitation)

    # Create Characteristics
    #check if characteristics already exist
    characteristics_db = db.query(Caracteristicas).all()
    if characteristics_db:
        print("Characteristics already exist, skiping creation")
    else:
        characteristics = ["rampa_electrica", "silla_de_ruedas", "ciego", "sordo", "mudo", "torpe", "traste", "testarudo"]
        for c in characteristics:
            characteristic = Caracteristicas(nombre=c)
            db.add(characteristic)
        db.commit()  # commit to ensure they are available for next query
        characteristics_db = db.query(Caracteristicas).all()

    # Create Clients
    clients = []
    for _ in range(20):
        lat, lng = random_lat_lng_montevideo()
        client = Clientes(
            documento=fake.unique.random_number(digits=8),
            nombre=fake.first_name(),
            latitud=lat,
            longitud=lng,
            apellido=fake.last_name(),
            direccion=fake.address(),
            telefono=fake.phone_number(),
            email=fake.email(),
            observaciones=fake.text(max_nb_chars=200)
        )
        client.caracteristicas = random.sample(characteristics_db, k=random.randint(1, 3))
        db.add(client)
        clients.append(client)

    #check if tipos_paradas already exist
    tipos = db.query(TiposParadas).all()
    if tipos:
        print("Tipos Paradas already exist, skiping creation")
    else:
        tipoH = TiposParadas(
            nombre='Hospital',    
        )
        db.add(tipoH),
        tipoP = TiposParadas(
            nombre='Particular',
        )
        db.add(tipoP)
        tipoM = TiposParadas(
            nombre='Mides',
        )
        db.add(tipoM)
        tipos = [tipoH, tipoP, tipoM]
        db.flush()
    # Create Orders
    tipos_pedido = list(m.TipoPedido)
    for client in clients:
        for tipo_pedido in tipos_pedido:
            for _ in range(2):  # Each client gets 2 of each type
                order = Pedidos(
                    cliente_documento=client.documento,
                    prioridad=random.randint(1, 5),
                    acompañante=random.choice([True, False]),
                    tipo=tipo_pedido,
                    fecha_programado=(datetime.now() + timedelta(days=random.randint(0, 30))).date(),
                    observaciones=tipo_pedido  # Using observaciones for type
                )
                db.add(order)
                db.flush()
                
                # Generate stops
                if tipo_pedido in [m.TipoPedido.solo_ida, m.TipoPedido.solo_vuelta]:
                    num_paradas = 2
                else:  # 'ida y vuelta'
                    num_paradas = random.randint(3, 5)
                
                first_lat, first_lng = random_lat_lng_montevideo()
                ventana_init = fake.date_time_this_year()
                threshold_time = datetime.strptime('19:00:00', '%H:%M:%S').time()
                if ventana_init.time() > threshold_time:
                    ventana_init = ventana_init.replace(hour=18, minute=59, second=59)
                
                for pos in range(num_paradas):
                    if pos == 0 or (pos == num_paradas - 1 and tipo_pedido == m.TipoPedido.ida_y_vuelta):
                        latitude, longitude = first_lat, first_lng
                    else:
                        latitude, longitude = random_lat_lng_montevideo()

                    if tipo_pedido == m.TipoPedido.solo_ida:
                        if pos == 0:
                            ventana_horaria_inicio, ventana_horaria_fin = None, None
                        else:
                            ventana_horaria_inicio, ventana_horaria_fin = ventana_init.time(), None
                    elif tipo_pedido == m.TipoPedido.solo_vuelta:
                        if pos == 0:
                            ventana_horaria_inicio, ventana_horaria_fin = ventana_init.time(), None
                        else:
                            ventana_horaria_inicio, ventana_horaria_fin = None, None
                    else:  # 'ida y vuelta'
                        if pos == 0 or pos == num_paradas - 1:
                            ventana_horaria_inicio, ventana_horaria_fin = None, None
                        else:
                            if not ventana_horaria_fin: 
                                ventana_horaria_inicio = ventana_init.time() 
                            else:
                                ventana_init += timedelta(minutes=random.randint(30, 90))
                                ventana_horaria_inicio = ventana_init.time()
                            ventana_init += timedelta(minutes=random.randint(30, 90))
                            ventana_horaria_fin = ventana_init.time()
                    
                    stop = Paradas(
                        tipo=random.choice(tipos).id,
                        id_pedido=order.id,
                        posicion_en_pedido=pos,
                        direccion=fake.address(),
                        latitud=latitude,
                        longitud=longitude,
                        ventana_horaria_inicio=ventana_horaria_inicio,
                        ventana_horaria_fin=ventana_horaria_fin,
                        observaciones=fake.text(max_nb_chars=200)
                    )
                    db.add(stop)


    # Create Vehicles
    vehicles = []
    for _ in range(10):
        vehicle = Vehiculos(
            matricula=fake.license_plate(),
            descripcion=fake.text(max_nb_chars=50),
            capacidad_convencional=random.randint(4, 8),
            capacidad_silla_de_ruedas=random.randint(1, 2),
            activo=random.choice([True, False]),
            observaciones=fake.text(max_nb_chars=200)
        )
        vehicle.caracteristicas = random.sample(characteristics_db, k=random.randint(1, 3))
        db.add(vehicle)
        vehicles.append(vehicle)

    # Create Drivers
    drivers = []
    for _ in range(15):
        driver = Choferes(
            documento=fake.unique.random_number(digits=8),
            nombre=fake.first_name(),
            apellido=fake.last_name(),
            telefono=fake.phone_number(),
            observaciones=fake.text(max_nb_chars=200)
        )
        db.add(driver)
        drivers.append(driver)

    # Create Common Places
    for _ in range(10):
        lat, lng = random_lat_lng_montevideo()
        place = LugaresComunes(
            nombre=fake.company(),
            direccion=fake.address(),
            latitud=lat,
            longitud=lng,
            observaciones=fake.text(max_nb_chars=200)
        )
        db.add(place)
    db.commit()
    db.close
    return
    # Create Planifications
    planifications = []
    for _ in range(5):
        planification = Planificaciones(
            nombre=fake.catch_phrase(),
            fecha=fake.date_this_year(before_today=False, after_today=True),
            fecha_creacion=fake.date_time_this_year(before_now=True, after_now=False),
            observaciones=fake.text(max_nb_chars=200)
        )
        db.add(planification)
        db.flush()
        planifications.append(planification)

        # Create Turns for each Planification
        for _ in range(random.randint(1, 3)):
            turn = Turnos(
                id_planificacion=planification.id,
                descripcion=fake.sentence(),
                hora_inicio=fake.time(),
                hora_fin=fake.time()
            )
            db.add(turn)
        db.commit()
        db.close
        return
        # Create Routes for each Planification
        for _ in range(random.randint(1, 5)):
            route = Rutas(
                id_planificacion=planification.id,
                id_vehiculo=random.choice(vehicles).id,
                hora_inicio=fake.time(),
                hora_fin=fake.time(),
                geometria="LINESTRING(0 0, 1 1, 2 2)",  # Simplified geometry
                observaciones=fake.text(max_nb_chars=200)
            )
            db.add(route)
            db.flush()
            # Create Route-Turn associations
            route_turn = RutasTurnos(
                id_ruta=route.id,
                id_turno=turn.id,
                id_chofer=random.choice(drivers).id
            )
            db.add(route_turn)

            # Create Visits for each Route
            for _ in range(random.randint(1, 5)):
                visit = Visitas(
                    id_ruta=route.id,
                    id_item=random.randint(1, 100),  # Simplified, should be a valid id
                    tipo_item=random.choice(list(m.TipoItemVisita)),
                    estado=random.choice(list(m.EstadoVisita)),
                    hora_llegada=fake.time_object(),
                    hora_salida=fake.time_object(),
                    observaciones=fake.text(max_nb_chars=200)
                )
                db.add(visit)
    db.commit()

    db.close()

def run_sql_script(session, sql_file_path):
    with open(sql_file_path, 'r') as f:
        sql_script = f.read()
    session.execute(text(sql_script))  # wrap in sqlalchemy.text()
    session.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean_db", action="store_true", help="Clean the DB before adding sample data")
    args = parser.parse_args()

    db = SessionLocal()

    if args.clean_db:
        print("Cleaning database...")
        run_sql_script(db, "./delete_all_db.sql")
        print("Database cleaned.")
    else:
        print("Database not cleaned, adding more data..., run it with --clean_db to clean the database")

    db.close()
    create_sample_data()
    print("Sample data has been generated successfully.")