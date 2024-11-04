from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from faker import Faker
import sys
import os

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

def random_lat_lng_montevideo():
    # Define the bounding box for Montevideo, Uruguay
    min_lat = -34.927
    max_lat = -34.797
    min_lng = -56.256
    max_lng = -56.053
    
    # Generate random latitude and longitude within the bounding box
    lat = random.uniform(min_lat, max_lat)
    lng = random.uniform(min_lng, max_lng)
    
    return lat, lng

def create_sample_data():
    db = SessionLocal()

    # Create Users
    users = []
    for _ in range(10):
        user = Usuarios(
            email=fake.email(),
            hashed_password=fake.sha256(),
            nombre=fake.name(),
            rol=random.choice(list(m.TipoUsuario))
        )
        db.add(user)
        users.append(user)
    
    # Create Refresh Tokens
    for user in users:
        refresh_token = RefreshToken(
            token=fake.uuid4(),
            user_id=user.id,
            expires_at=datetime.now() + timedelta(days=30)
        )
        db.add(refresh_token)

    # Create Invitations
    for _ in range(5):
        invitation = InvitacionUsuario(
            hash_link=fake.sha256(),
            email=fake.email(),
            nombre=fake.name(),
            rol=random.choice(["admin", "user"])
        )
        db.add(invitation)

    # Create Characteristics
    characteristics = []
    for _ in range(5):
        characteristic = Caracteristicas(nombre=fake.word())
        db.add(characteristic)
        characteristics.append(characteristic)

    # Create Clients
    clients = []
    for _ in range(20):
        client = Clientes(
            documento=fake.unique.random_number(digits=8),
            nombre=fake.first_name(),
            apellido=fake.last_name(),
            direccion=fake.address(),
            telefono=fake.phone_number(),
            email=fake.email(),
            observaciones=fake.text(max_nb_chars=200)
        )
        client.caracteristicas = random.sample(characteristics, k=random.randint(1, 3))
        db.add(client)
        clients.append(client)

    tipoH = TiposParadas(
        nombre='Hospital',    
    )
    db.add(tipoH), #'Particular', 'Mides'])
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
    for client in clients:
        for _ in range(random.randint(1, 10)):
            order = Pedidos(
                cliente_documento=client.documento,
                prioridad=random.randint(1, 5),
                acompañante=random.choice([True, False]),
                tipo=random.choice(list(m.TipoPedido)),
                fecha_programado=(datetime.now() + timedelta(days=random.randint(0, 30))).date(),
                observaciones=fake.text(max_nb_chars=200)
            )
            db.add(order)
            db.flush()
            ventana_init = fake.date_time_this_year()
            threshold_time = datetime.strptime('19:00:00', '%H:%M:%S').time()

            if ventana_init.time() > threshold_time:
                ventana_init = ventana_init.replace(hour=18, minute=59, second=59)
            for pos in range(random.randint(1, 5)):
                ventana_fin = (ventana_init + timedelta(hours=1))
                latitude, longitude = random_lat_lng_montevideo()
                stop = Paradas(
                    tipo = random.choice(tipos).id,
                    id_pedido=order.id,
                    posicion_en_pedido=pos + 1,
                    direccion=fake.address(),
                    latitud=latitude,
                    longitud=longitude,
                    ventana_horaria_inicio=ventana_init.time(),
                    ventana_horaria_fin=ventana_fin.time(),
                    observaciones=fake.text(max_nb_chars=200)
                )
                ventana_init = ventana_fin

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

    # Assign drivers to vehicles
    for vehicle in vehicles:
        vehicle.documento_chofer_habitual = random.choice(drivers).documento

    # Create Common Places
    for _ in range(10):
        place = LugaresComunes(
            nombre=fake.company(),
            direccion=fake.address(),
            latitud=float(fake.latitude()),
            longitud=float(fake.longitude()),
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

if __name__ == "__main__":
    create_sample_data()
    print("Sample data has been generated successfully.")