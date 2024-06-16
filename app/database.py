from sqlalchemy import create_engine, Column, ForeignKey,Integer, cast, func, String, Float, DateTime, Boolean, Enum as SQLAEnum # type: ignore
from enum import Enum
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from geoalchemy2 import Geometry # type: ignore
from datetime import datetime
import hashlib
import random
import models as m
from sqlalchemy import CheckConstraint # type: ignore

import autenticacion.autenticacion as aut

SQLALCHEMY_DATABASE_URL = 'postgresql://fernando:123123123@db:5432/mides'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# region Usuarios

class Usuarios(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    nombre = Column(String)
    rol = Column(SQLAEnum(m.TipoUsuario), nullable=False)
    token = Column(String)

class InvitacionUsuario(Base):
    __tablename__ = 'invitaciones_usuarios'

    id = Column(Integer, primary_key=True, index=True)
    hash_link = Column(String, index=True, unique=True, nullable=False)
    email = Column(String, index=True, unique=True, nullable=False)
    used = Column(Boolean, default=False)
    nombre = Column(String)
    rol = Column(String)

def add_usuario_db(usuario): #FIXME: REMOVER SOLO USADO PARA DEVELOPMENT, CREAR USUARIOS RAPIDAMENTE
    with get_db() as db:
        usuario.hashed_password = aut.get_password_hash(usuario.hashed_password)
        usuario_obj = Usuarios(**usuario.dict())
        db.add(usuario_obj)
        db.commit()
        db.refresh(usuario_obj)
        return usuario_obj

def registrar_usuario(usuarioInv, nuevo_user):
    with get_db() as db:
        hashed_password = aut.get_password_hash(nuevo_user.password)
        usuario_obj = Usuarios(rol = usuarioInv.rol, email=usuarioInv.email, #Se usa rol y email de la invitación
                               nombre=nuevo_user.nombre, hashed_password=hashed_password) # el nuevo usuario puede tener un nombre distinto al de la invitación
        db.add(usuario_obj)
        db.query(InvitacionUsuario).filter(InvitacionUsuario.hash_link == usuarioInv.hash_link,
                                          InvitacionUsuario.used==False ).update({"used": True})
        db.commit()
        db.refresh(usuario_obj)
        return usuario_obj
    
def get_usuarios(skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Usuarios).offset(skip).limit(limit).all(), db.query(Usuarios).count()

def get_usuario_db(email):
    with get_db() as db:
        return db.query(Usuarios).filter(Usuarios.email == email).first()
    
def update_usuario_db(email, usuario):
    with get_db() as db:
        db.query(Usuarios).filter(Usuarios.email == email).update(usuario.dict())
        db.commit()
        return usuario

def delete_usuario_db(email):
    with get_db() as db:
        db.query(Usuarios).filter(Usuarios.email == email).delete()
        db.commit()
        return {"message": f"Usuario {email} eliminado correctamente."}

def login(username: str, password: str):
    with get_db() as db:
        user = db.query(Usuarios).filter(Usuarios.email == username).first()
        if not user or not aut.verify_password(password, user.hashed_password):
            return None
        # Si el usuario y la contraseña son válidos, generamos un token JWT
        access_token = aut.generate_token(user.email)
        user.token = access_token
        db.commit()
        return access_token

def user_exists(email: str):
    with get_db() as db:
        user = db.query(Usuarios).filter(Usuarios.email == email).first()
        return user

def logout(email: str):
    with get_db() as db:
        user = user_exists(email)
        if not user:
            return None
        user.token = None
        db.commit()
        return {"message": f"Usuario {email} deslogueado correctamente."}



INVITATION_SUBJECT_TEMPLATE = "Invitación al Sistema de Servicio de transporte accesible"
INVITATION_BODY_TEMPLATE = """ Hola {nombre_usuario}, 
Felicidades has sido invitado a ser un usuario del Sistema de Servicio de transporte accesible, 
ingresa aqui https://mides.com/account/{hash_link} para generar una contraseña y completar tu registro."""

def generate_invitation(usuario_invite: InvitacionUsuario):
    try:
        with get_db() as db:
            counter = 0
            while counter < 10:
                hash_link = hashlib.sha256(f"{usuario_invite.email}{random.random()}".encode()).hexdigest()
                existing_invitation = db.query(InvitacionUsuario).filter(
                    InvitacionUsuario.hash_link == hash_link,
                    InvitacionUsuario.used == False
                ).first()
                if not existing_invitation:
                    break
                counter += 1

            if counter >= 10:
                return None

            new_invitation = InvitacionUsuario(
                hash_link=hash_link,
                email=usuario_invite.email,
                nombre=usuario_invite.nombre,
                rol=usuario_invite.rol
            )
            db.add(new_invitation)
            db.commit()
            db.refresh(new_invitation)
            return hash_link
    except Exception as e:
        print(e)
        return None

def get_invitation(hash_link: str):# id no requerido para el GET, pero si para el POST(mas eficiente y mas seguro)
    with get_db() as db:
        return db.query(InvitacionUsuario).filter(InvitacionUsuario.hash_link == hash_link, 
                                                  InvitacionUsuario.used == False,).first()
# endregion

# region Clientes

class Clientes(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True, index=True)
    documento = Column(Integer, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    telefono = Column(String)
    email = Column(String)
    tipo = Column(SQLAEnum(m.TipoCliente), nullable=False)
    observaciones = Column(String)

def add_cliente_db(cliente):
    with get_db() as db:
        db_cliente = Clientes(**cliente.dict())
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)
        return db_cliente

def get_cliente_db(documento):
    with get_db() as db:
        # Retrieve client from the database based on document
        cliente = db.query(Clientes).filter(Clientes.documento == documento).first()
        return cliente

# Obtiene y devuelve un cliente con sus características y pedidos asociados
def get_cliente_completo(id):
    with get_db() as db:
        # Retrieve client and their associated orders from the database based on document
        cliente = db.query(Clientes).filter(Clientes.id == id).first()
        # Retrieve orders associated with the client
        pedidos = db.query(Pedidos).filter(Pedidos.cliente_documento == cliente.documento).all()
        return cliente, pedidos

# Obtiene los clientes desde skip hasta skip+limit
def get_clientes_db(skip: int = 0, limit: int = 100):
    with get_db() as db:
        # Retrieve clients from the database with pagination
        clientes = db.query(Clientes).offset(skip).limit(limit).all()
        return clientes

# Obtiene los clientes cuyo documento contiene el valor de la variable documento al principio
def get_clientes_by_documento_db(documento: int, skip: int = 0, limit: int = 100):
    with get_db() as db:
        # Retrieve clients from the database whose document starts with the given value
        clientes = db.query(Clientes).filter(cast(Clientes.documento, String).like(f'{documento}%')).offset(skip).limit(limit).all()
        return clientes

# Obtiene los clientes cuyo nombre o apellido contienen el valor de la variable nombre_apellido
def get_clientes_by_nombre_db(nombre: str, skip: int = 0, limit: int = 100):
    with get_db() as db:
        # Retrieve clients from the database whose name or last name contains the given value
        clientes = db.query(Clientes).filter((Clientes.nombre.ilike(f'%{nombre}%')) | (Clientes.apellido.ilike(f'%{nombre}%'))).offset(skip).limit(limit).all()
        return clientes

# Obtiene los clientes de un tipo específico
def get_clientes_by_tipo_db(tipo_persona: str, skip: int = 0, limit: int = 100):
    with get_db() as db:
        # Retrieve clients from the database of a specific type
        clientes = db.query(Clientes).filter(Clientes.tipo_persona == tipo_persona).offset(skip).limit(limit).all()
        return clientes

# Obtiene los clientes con una característica específica
def get_clientes_by_caracteristica_db(caracteristica: str, skip: int = 0, limit: int = 100):
    with get_db() as db:
        # Retrieve clients from the database with a specific characteristic
        clientes = db.query(Clientes).join(ClientesCaracteristicas).filter(ClientesCaracteristicas.caracteristica == caracteristica).offset(skip).limit(limit).all()
        return clientes

def update_cliente_db(documento, cliente):
    with get_db() as db:
        # Update client in the database based on document
        db.query(Clientes).filter(Clientes.documento == documento).update(cliente)
        db.commit()
        return cliente

def delete_cliente_db(documento):
    with get_db() as db:
        # Delete client from the database based on document
        db.query(Clientes).filter(Clientes.documento == documento).delete()
        db.commit()
        return {"message": f"Cliente con documento {documento} eliminado correctamente."}

# endregion

# region ClientesCaracteristicas

class ClientesCaracteristicas(Base):
    __tablename__ = 'clientes_caracteristicas'

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id'))
    caracteristica = Column(String)

def add_cliente_caracteristica(cliente_caracteristica):
    with get_db() as db:
        # Add client characteristic to the database
        db.add(cliente_caracteristica)
        db.commit()
        db.refresh(cliente_caracteristica)
        return cliente_caracteristica
    
def get_cliente_caracteristica(id_cliente):
    with get_db() as db:
        # Retrieve client characteristic from the database based on client id
        cliente_caracteristica = db.query(ClientesCaracteristicas).filter(ClientesCaracteristicas.id_cliente == id_cliente).first()
        return cliente_caracteristica
    
def update_cliente_caracteristica(id_cliente, caracteristica):
    with get_db() as db:
        # Update client characteristic in the database based on client id
        db.query(ClientesCaracteristicas).filter(ClientesCaracteristicas.id_cliente == id_cliente).update(caracteristica)
        db.commit()
        return caracteristica
    
def delete_cliente_caracteristica(id_cliente):
    with get_db() as db:
        # Delete client characteristic from the database based on client id
        db.query(ClientesCaracteristicas).filter(ClientesCaracteristicas.id_cliente == id_cliente).delete()
        db.commit()
        return {"message": f"Características del cliente con ID {id_cliente} eliminadas correctamente."}
# endregion

# region Pedidos

class Pedidos(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    cliente_documento = Column(Integer, ForeignKey('clientes.documento'), nullable=False)
    prioridad = Column(Integer, nullable=False)
    acompañante = Column(Boolean, nullable=False)
    tipo = Column(SQLAEnum(m.TipoPedido), nullable=False)
    fecha_ingresado = Column(DateTime, nullable=False)
    observaciones = Column(String)

def add_pedido_db(pedido):
    with get_db() as db:
        pedido_obj = Pedidos(**pedido.dict())
        db.add(pedido_obj)
        db.commit()
        db.refresh(pedido_obj)
        return pedido_obj

# Obtinene un pedido y todas sus paradas asociadas
def get_pedido_db(id_pedido):
    with get_db() as db:
        pedido = db.query(Pedidos).filter(Pedidos.id_pedido == id_pedido).first()
        pedido.paradas = db.query(Paradas).filter(Paradas.id_pedido == id_pedido).all().order_by(Paradas.posicion_en_pedido)
        return pedido

# Obtiene los pedidos desde skip hasta skip+limit
def get_pedidos_db(skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Pedidos).offset(skip).limit(limit).all()
    
# Obtiene los pedidos creados en un rango de fechas
def get_pedidos_by_rango_fechas_db(fecha_inicio: DateTime, fecha_fin: DateTime, skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Pedidos).filter(Pedidos.hora_ingresado >= fecha_inicio, Pedidos.hora_ingresado <= fecha_fin).offset(skip).limit(limit).all()
    
# Obtiene los pedidos cuyas ventanas de origen y destino son en una fecha específica
def get_pedidos_by_fecha_db(fecha_str: str, skip: int = 0, limit: int = 100):
    with get_db() as db:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        return db.query(Pedidos ,  Clientes.nombre,  Clientes.apellido).\
            join(Clientes, Pedidos.cliente_documento == Clientes.documento).\
            filter(
                func.date(Pedidos.ventana_origen_inicio) == fecha.date(), 
                func.date(Pedidos.ventana_destino_inicio) == fecha.date()
            ).offset(skip).limit(limit).all()

def update_pedido_db(id_pedido, pedido):
    with get_db() as db:
        db.query(Pedidos).filter(Pedidos.id_pedido == id_pedido).update(pedido.dict())
        db.commit()
        return pedido

def delete_pedido_db(id_pedido):
    with get_db() as db:
        db.query(Pedidos).filter(Pedidos.id_pedido == id_pedido).delete()
        db.commit()
        return {"message": f"Pedido con ID {id_pedido} eliminado correctamente."}
    
# endregion

# region Paradas

class Paradas(Base):
    __tablename__ = 'paradas'

    id = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey('pedidos.id'), nullable=False)
    posicion_en_pedido = Column(Integer, nullable=False)
    direccion = Column(String, nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)
    ventana_horaria_inicio = Column(DateTime)
    ventana_horaria_fin = Column(DateTime)
    observaciones = Column(String)

def add_parada_db(parada):
    with get_db() as db:
        parada_obj = Paradas(**parada.dict())
        db.add(parada_obj)
        db.commit()
        db.refresh(parada_obj)
        return parada_obj
    
def get_parada_db(id_parada):
    with get_db() as db:
        return db.query(Paradas).filter(Paradas.id_parada == id_parada).first()
    
def update_parada_db(id_parada, parada):
    with get_db() as db:
        db.query(Paradas).filter(Paradas.id_parada == id_parada).update(parada.dict())
        db.commit()
        return parada
    
def delete_parada_db(id_parada):
    with get_db() as db:
        db.query(Paradas).filter(Paradas.id_parada == id_parada).delete()
        db.commit()
        return {"message": f"Parada con ID {id_parada} eliminada correctamente."}

# endregion

# region Vehiculos
class Vehiculos(Base):
    __tablename__ = 'vehiculos'

    id = Column(Integer, primary_key=True, index=True)
    matricula = Column(String, unique=True, nullable=False)
    descripcion = Column(String)
    documento_chofer_habitual = Column(Integer, ForeignKey('choferes.documento'))
    capacidad_convencional = Column(Integer, nullable=False)
    capacidad_silla_de_ruedas = Column(Integer, nullable=False)
    disponibilidad = Column(Boolean, nullable=False)
    observaciones = Column(String)

    __table_args__ = (
        CheckConstraint('capacidad_convencional > 0', name='capacidad_convencional_check'),
        CheckConstraint('capacidad_silla_de_ruedas > 0', name='capacidad_silla_de_ruedas_check'),
    )

def add_vehiculo_db(vehiculo):
    with get_db() as db:
        vehiculo_obj = Vehiculos(**vehiculo.dict())
        db.add(vehiculo_obj)
        db.commit()
        db.refresh(vehiculo_obj)
        return vehiculo_obj
    
def get_vehiculo_db(id_vehiculo):
    with get_db() as db:
        return db.query(Vehiculos).filter(Vehiculos.id_vehiculo == id_vehiculo).first()

def get_vehiculos_db(skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Vehiculos).offset(skip).limit(limit).all()

def get_vehiculo_by_matricula_db(matricula):
    with get_db() as db:
        return db.query(Vehiculos).filter(Vehiculos.matricula == matricula).first()
    
def update_vehiculo_db(id_vehiculo, vehiculo):
    with get_db() as db:
        db.query(Vehiculos).filter(Vehiculos.id_vehiculo == id_vehiculo).update(vehiculo.dict())
        db.commit()
        return vehiculo
    
def delete_vehiculo_db(id_vehiculo):
    with get_db() as db:
        db.query(Vehiculos).filter(Vehiculos.id_vehiculo == id_vehiculo).delete()
        db.commit()
        return {"message": f"Vehículo con ID {id_vehiculo} eliminado correctamente."}
    
#endregion

# region VehiculosCaracteristicas
class VehiculosCaracteristicas(Base):
    __tablename__ = 'vehiculos_caracteristicas'

    id = Column(Integer, primary_key=True, index=True)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id'))
    caracteristica = Column(String)

def add_vehiculo_caracteristica(vehiculo_caracteristica):
    with get_db() as db:
        vehiculo_caracteristica_obj = VehiculosCaracteristicas(**vehiculo_caracteristica.dict())
        db.add(vehiculo_caracteristica_obj)
        db.commit()
        db.refresh(vehiculo_caracteristica_obj)
        return vehiculo_caracteristica_obj
    
def get_vehiculo_caracteristica(id_vehiculo):
    with get_db() as db:
        return db.query(VehiculosCaracteristicas).filter(VehiculosCaracteristicas.id_vehiculo == id_vehiculo).first()
    
def update_vehiculo_caracteristica(id_vehiculo, caracteristica):
    with get_db() as db:
        db.query(VehiculosCaracteristicas).filter(VehiculosCaracteristicas.id_vehiculo == id_vehiculo).update(caracteristica.dict())
        db.commit()
        return caracteristica
    
def delete_vehiculo_caracteristica(id_vehiculo):
    with get_db() as db:
        db.query(VehiculosCaracteristicas).filter(VehiculosCaracteristicas.id_vehiculo == id_vehiculo).delete()
        db.commit()
        return {"message": f"Características del vehículo con ID {id_vehiculo} eliminadas correctamente."}
    
# endregion

# region Choferes
class Choferes(Base):
    __tablename__ = 'choferes'

    id = Column(Integer, primary_key=True, index=True)
    documento = Column(Integer, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String)
    observaciones = Column(String)

def add_chofer_db(chofer):
    with get_db() as db:
        chofer_obj = Choferes(**chofer.dict())
        db.add(chofer_obj)
        db.commit()
        db.refresh(chofer_obj)
        return chofer_obj
    
def get_chofer_db(documento):
    with get_db() as db:
        return db.query(Choferes).filter(Choferes.documento == documento).first()
    
def get_choferes_db(skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Choferes).offset(skip).limit(limit).all()

def update_chofer_db(documento, chofer):
    with get_db() as db:
        db.query(Choferes).filter(Choferes.documento == documento).update(chofer.dict())
        db.commit()
        return chofer
    
def delete_chofer_db(documento):
    with get_db() as db:
        db.query(Choferes).filter(Choferes.documento == documento).delete()
        db.commit()
        return {"message": f"Chofer con documento {documento} eliminado correctamente."}

# endregion

# region Lugares comunes
class LugaresComunes(Base):
    __tablename__ = 'lugares_comunes'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)
    observaciones = Column(String)

def add_lugar_comun_db(deposito):
    with get_db() as db:
        deposito_obj = LugaresComunes(**deposito.dict())
        db.add(deposito_obj)
        db.commit()
        db.refresh(deposito_obj)
        return deposito_obj
    
def get_lugar_comun_db(id_deposito):
    with get_db() as db:
        return db.query(LugaresComunes).filter(LugaresComunes.id_deposito == id_deposito).first()

def get_lugares_comunes_db(skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(LugaresComunes).offset(skip).limit(limit).all()

def update_lugar_comun_db(id_deposito, deposito):
    with get_db() as db:
        db.query(LugaresComunes).filter(LugaresComunes.id_deposito == id_deposito).update(deposito.dict())
        db.commit()
        return deposito
    
def delete_lugar_comun_db(id_deposito):
    with get_db() as db:
        db.query(LugaresComunes).filter(LugaresComunes.id_deposito == id_deposito).delete()
        db.commit()
        return {"message": f"Depósito con ID {id_deposito} eliminado correctamente."}

# endregion

# region Planificaciones
class Planificaciones(Base):
    __tablename__ = 'planificaciones'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    observaciones = Column(String)

# Crea un planificación y dos turnos asociados
def crear_planificacion(planificacion):
    with get_db() as db:
        planificacion_obj = add_planificacion_db(planificacion)

        # Crea dos turnos por defecto asociados a la planificación
        planificacion_obj.turnos = []
        turno1 = Turnos(id_planificacion=planificacion_obj.id_planificacion, descripcion="Turno mañana", hora_inicio="06:00", hora_fin="14:00")
        turno1 = add_turno_db(turno1)
        planificacion_obj.turnos.append(turno1)
        turno2 = Turnos(id_planificacion=planificacion_obj.id_planificacion, descripcion="Turno tarde", hora_inicio="13:00", hora_fin="21:00")
        turno2 = add_turno_db(turno2)
        planificacion_obj.turnos.append(turno2)

        # Asocia a la planificación los vehículos, choferes y lugares comunes disponibles
        planificacion_obj.vehiculos = get_vehiculos_db()
        planificacion_obj.choferes = get_choferes_db()
        planificacion_obj.lugares_comunes = get_lugares_comunes_db()

        # Asocia a la planificación los pedidos para su fecha
        planificacion_obj.pedios = get_pedidos_by_fecha_db(planificacion_obj.fecha)

        return planificacion_obj

def add_planificacion_db(planificacion):
    with get_db() as db:
        planificacion_obj = Planificaciones(**planificacion.dict())
        db.add(planificacion_obj)
        db.commit()
        db.refresh(planificacion_obj)
        return planificacion_obj
    
def get_planificacion_db(id_planificacion):
    with get_db() as db:
        return db.query(Planificaciones).filter(Planificaciones.id_planificacion == id_planificacion).first()
    
# Obtiene las planificaciones para un determinado día
def get_planificaciones_by_fecha_db(fecha: DateTime, skip: int = 0, limit: int = 100):
    with get_db() as db:
        return db.query(Planificaciones).filter(Planificaciones.fecha == fecha).offset(skip).limit(limit).all()

# Obtiene una planificación con sus turnos asociados

def update_planificacion_db(id_planificacion, planificacion):
    with get_db() as db:
        db.query(Planificaciones).filter(Planificaciones.id_planificacion == id_planificacion).update(planificacion.dict())
        db.commit()
        return planificacion
    
def delete_planificacion_db(id_planificacion):
    with get_db() as db:
        db.query(Planificaciones).filter(Planificaciones.id_planificacion == id_planificacion).delete()
        db.commit()
        return {"message": f"Planificación con ID {id_planificacion} eliminada correctamente."}
    
# endregion

# region Turnos
class Turnos(Base):
    __tablename__ = 'turnos'

    id = Column(Integer, primary_key=True, index=True)
    id_planificacion = Column(Integer, ForeignKey('planificaciones.id'))
    descripcion = Column(String, nullable=False)
    hora_inicio = Column(DateTime, nullable=False)
    hora_fin = Column(DateTime, nullable=False)

def add_turno_db(turno):
    with get_db() as db:
        turno_obj = Turnos(**turno.dict())
        db.add(turno_obj)
        db.commit()
        db.refresh(turno_obj)
        return turno_obj
    
def get_turno_db(id_turno):
    with get_db() as db:
        return db.query(Turnos).filter(Turnos.id_turno == id_turno).first()
    
def update_turno_db(id_turno, turno):
    with get_db() as db:
        db.query(Turnos).filter(Turnos.id_turno == id_turno).update(turno.dict())
        db.commit()
        return turno
    
def delete_turno_db(id_turno):
    with get_db() as db:
        db.query(Turnos).filter(Turnos.id_turno == id_turno).delete()
        db.commit()
        return {"message": f"Turno con ID {id_turno} eliminado correctamente."}
    
# endregion

# region Rutas
class Rutas(Base):
    __tablename__ = 'rutas'

    id = Column(Integer, primary_key=True, index=True)
    id_turno = Column(Integer, ForeignKey('turnos.id'))
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id'))
    id_chofer = Column(Integer, ForeignKey('choferes.id'))
    hora_inicio = Column(DateTime, nullable=False)
    hora_fin = Column(DateTime, nullable=False)
    geometria = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    observaciones = Column(String)

def add_ruta_db(ruta):
    with get_db() as db:
        ruta_obj = Rutas(**ruta.dict())
        db.add(ruta_obj)
        db.commit()
        db.refresh(ruta_obj)
        return ruta_obj
    
def get_ruta_db(id_ruta):
    with get_db() as db:
        return db.query(Rutas).filter(Rutas.id_ruta == id_ruta).first()
    
def update_ruta_db(id_ruta, ruta):
    with get_db() as db:
        db.query(Rutas).filter(Rutas.id_ruta == id_ruta).update(ruta.dict())
        db.commit()
        return ruta
    
def delete_ruta_db(id_ruta):
    with get_db() as db:
        db.query(Rutas).filter(Rutas.id_ruta == id_ruta).delete()
        db.commit()
        return {"message": f"Ruta con ID {id_ruta} eliminada correctamente."}
    
# endregion

# region Visitas

class Visitas(Base):
    __tablename__ = 'visitas'

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey('rutas.id'))
    id_item = Column(Integer, nullable=False)
    tipo_item = Column(SQLAEnum(m.TipoItemVisita), nullable=False)
    estado = Column(SQLAEnum(m.EstadoVisita), nullable=False)
    hora_llegada = Column(DateTime, nullable=False)
    hora_salida = Column(DateTime, nullable=False)
    observaciones = Column(String)
    
def add_visita_db(visita):
    with get_db() as db:
        visita_obj = Visitas(**visita.dict())
        db.add(visita_obj)
        db.commit()
        db.refresh(visita_obj)
        return visita_obj
    
def get_visita_db(id_visita):
    with get_db() as db:
        return db.query(Visitas).filter(Visitas.id_visita == id_visita).first()
    
def update_visita_db(id_visita, visita):
    with get_db() as db:
        db.query(Visitas).filter(Visitas.id_visita == id_visita).update(visita.dict())
        db.commit()
        return visita
    
def delete_visita_db(id_visita):
    with get_db() as db:
        db.query(Visitas).filter(Visitas.id_visita == id_visita).delete()
        db.commit()
        return {"message": f"Visita con ID {id_visita} eliminada correctamente."}
    
# endregion
