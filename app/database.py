from sqlite3 import Date
from sqlalchemy import create_engine, Column, ForeignKey,Integer, cast, func, String, Float, DateTime, Time, Boolean, Enum as SQLAEnum, or_ # type: ignore
from enum import Enum
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker, joinedload, relationship # type: ignore
from geoalchemy2 import Geometry # type: ignore
from datetime import datetime, timedelta
from shapely.geometry import LineString
from geoalchemy2 import WKTElement

from fastapi import HTTPException # type: ignore
import hashlib
import random
import models as m
import logging
log = logging.getLogger(__name__)

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
    refresh_tokens = relationship("RefreshToken", back_populates="user")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"))
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    user = relationship("Usuarios", back_populates="refresh_tokens")
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

# Obtiene los usuarios desde offset hasta offset+limit, devuelve también la cantidad total de usuarios   
def get_usuarios(offset: int = 0, limit: int = 100):
    with get_db() as db:
        usuarios = db.query(Usuarios).offset(offset).limit(limit).all()
        public_users_full = []
        for user in usuarios:
            public_users_full.append({
                'id': user.id,
                'email': user.email,
                'nombre': user.nombre,
                'rol': user.rol
            })
        cantidad = db.query(Usuarios).count()
        return public_users_full, cantidad

def get_usuario_db(id_usuario):
    with get_db() as db:
        usuario= db.query(Usuarios).filter(Usuarios.id == id_usuario).first()
        return {
            'id': usuario.id,
            'email': usuario.email,
            'nombre': usuario.nombre,
            'rol': usuario.rol
        }
    
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
            return None, None
        # Si el usuario y la contraseña son válidos, generamos un token JWT
        access_token = aut.create_access_token(data={"sub": user.email, "user_id": user.id})
        refresh_token = aut.create_refresh_token(data={"sub": user.email, "user_id": user.id})
        user.token = access_token
        new_ref_token = RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.utcnow() + timedelta(days=aut.REFRESH_TOKEN_EXPIRE_DAYS))
        db.add(new_ref_token)
        db.commit()
        return access_token, refresh_token

def get_user_by_email(email: str):
    with get_db() as db:
        user = db.query(Usuarios).filter(Usuarios.email == email).first()
        return user

def logout(refresh_token: str, email: str):
    with get_db() as db:
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail=f"User with email {email} not found")
        
        db_token = get_refresh_token(refresh_token)
        if db_token:
            db_token.is_revoked = True
        else:
            log.error(f"Warning: Refresh token not found for user {email}")

        user.token = None
        
        db.commit()
        return {"message": f"User {email} successfully logged out."}


def get_refresh_token(token: str):
    with get_db() as db:
        return db.query(RefreshToken).filter(RefreshToken.token == token).first()


def is_refresh_token_valid(user_id: int, refresh_token: str):
    with get_db() as db:
        token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()
        return token is not None

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
    direccion = Column(String)
    telefono = Column(String)
    email = Column(String)
    observaciones = Column(String)
    activo = Column(Boolean, default=True)

    caracteristicas = relationship(
        'Caracteristicas',
        secondary='clientes_caracteristicas',
        backref='clientes'
    )

    pedidos = relationship('Pedidos', back_populates='cliente')

# Agrega un cliente y sus características asociadas
def add_cliente_db(cliente):
    try:
        with get_db() as db:
            cliente_obj = cliente.dict()
            caracteristicas = cliente_obj.pop('caracteristicas', [])
            cliente_obj = Clientes(**cliente_obj)
            db.add(cliente_obj)
            db.flush()
            caracteristicas_obj = []
            if caracteristicas:
                for caracteristica in caracteristicas:
                    caracteristica_obj = ClientesCaracteristicas(id_cliente=cliente_obj.id, id_caracteristica=caracteristica)
                    db.add(caracteristica_obj)
                    db.flush()
                    caracteristicas_obj.append(caracteristica_obj)
            db.commit()
            db.refresh(cliente_obj)
            return cliente_obj
    except Exception as e:
        db.rollback()  
        raise e
    finally:
        db.close() 

def get_cliente(id):
    with get_db() as db:
        cliente = db.query(Clientes).filter(Clientes.id == id).first()
        return cliente

def get_cliente_by_doc(documento):
    with get_db() as db:
        cliente = db.query(Clientes).filter(Clientes.documento == documento).first()
        return cliente
     
def get_cliente_completo(id):
    with get_db() as db:
        cliente = db.query(Clientes).options(
            joinedload(Clientes.caracteristicas),  
            joinedload(Clientes.pedidos).joinedload(Pedidos.paradas)
        ).filter(Clientes.id == id).first()

        if cliente and cliente.pedidos:
            now = datetime.now() #FIXME VALIDAR FECHA ACTUAL TIMEZONE
            log.info(f"Fecha actual: {now}")
            cliente.pedidos = [pedido for pedido in cliente.pedidos if pedido.fecha_programado >= now]
        return cliente

# Obtiene los clientes desde offset hasta offset+limit
def get_clientes_db(limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        search_func = Clientes.activo == True
        if search:
            search_func = search_func & (
                or_(
                    Clientes.nombre.ilike(f'%{search}%'),
                    Clientes.apellido.ilike(f'%{search}%'),
                    cast(Clientes.documento, String).ilike(f'%{search}%'),
                    cast(Clientes.tipo, String).ilike(f'%{search}%')
                )
            )
        clientes = db.query(Clientes).filter(search_func).offset(offset).limit(limit).all()
        log.info(f"Clientes: {clientes}")
        cantidad = db.query(Clientes).filter(search_func).count()
        return clientes, cantidad

# Obtiene los clientes cuyo documento contiene el valor de la variable documento al principio
def get_clientes_by_documento_db(documento: int, limit: int = 100, offset: int = 0):
    with get_db() as db:
        clientes = db.query(Clientes).filter(cast(Clientes.documento, String).like(f'{documento}%')).offset(offset).limit(limit).all()
        cantidad = db.query(Clientes).filter(cast(Clientes.documento, String).like(f'{documento}%')).count()
        return clientes, cantidad

# Obtiene los clientes cuyo nombre o apellido contienen el valor de la variable nombre_apellido
def get_clientes_by_nombre_db(nombre: str, limit: int = 100, offset: int = 0):
    with get_db() as db:
        clientes = db.query(Clientes).filter((Clientes.nombre.ilike(f'%{nombre}%')) | (Clientes.apellido.ilike(f'%{nombre}%'))).offset(offset).limit(limit).all()
        cantidad = db.query(Clientes).filter((Clientes.nombre.ilike(f'%{nombre}%')) | (Clientes.apellido.ilike(f'%{nombre}%'))).count()
        return clientes, cantidad

# Obtiene los clientes de un tipo específico
def get_clientes_by_tipo_db(tipo_persona: str, limit: int = 100, offset: int = 0):
    with get_db() as db:
        clientes = db.query(Clientes).filter(Clientes.tipo_persona == tipo_persona).offset(offset).limit(limit).all()
        cantidad = db.query(Clientes).filter(Clientes.tipo_persona == tipo_persona).count()
        return clientes, cantidad

# Obtiene los clientes con una característica específica
def get_clientes_by_caracteristica_db(caracteristica: str, limit: int = 100, offset: int = 0):
    with get_db() as db:
        clientes = db.query(Clientes).join(ClientesCaracteristicas).filter(ClientesCaracteristicas.caracteristica == caracteristica).offset(offset).limit(limit).all()
        cantidad = db.query(Clientes).join(ClientesCaracteristicas).filter(ClientesCaracteristicas.caracteristica == caracteristica).count()
        return clientes, cantidad

def update_cliente_db(documento, cliente):
    with get_db() as db:
        # Update client in the database based on document
        db.query(Clientes).filter(Clientes.documento == documento).update(cliente)
        db.commit()
        return cliente

def delete_cliente_db(id):
    with get_db() as db:
        # Delete client from the database based on document
        db.query(Clientes).filter(Clientes.id == id).update({"activo": False})
        db.commit()
        return {"message": f"Cliente eliminado correctamente."}

# endregion

# region ClientesCaracteristicas

class ClientesCaracteristicas(Base):
    __tablename__ = 'clientes_caracteristicas'

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id'))
    id_caracteristica = Column(Integer, ForeignKey('caracteristicas.id'))

def add_cliente_caracteristica(cliente_caracteristica):
    with get_db() as db:
        # Add client characteristic to the database
        cliente_caracteristica_obj = ClientesCaracteristicas(**cliente_caracteristica.dict())
        db.add(cliente_caracteristica_obj)
        db.commit()
        db.refresh(cliente_caracteristica_obj)
        return cliente_caracteristica_obj
    
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

# region Caracteristicas

class Caracteristicas(Base):
    __tablename__ = 'caracteristicas'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)

def get_caracteristicas_db(limit: int = 100, offset: int = 0):
    with get_db() as db:
        caracteristicas = db.query(Caracteristicas).offset(offset).limit(limit).all()
        return caracteristicas

def add_caracteristica_db(nombre):
    with get_db() as db:
        caracteristica = Caracteristicas(nombre=nombre)
        db.add(caracteristica)
        db.commit()
        db.refresh(caracteristica)
        return caracteristica
# endregion

# region Pedidos

class Pedidos(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    cliente_documento = Column(Integer, ForeignKey('clientes.documento'), nullable=False)
    prioridad = Column(Integer, nullable=False)
    acompañante = Column(Boolean, nullable=False)
    tipo = Column(SQLAEnum(m.TipoPedido), nullable=False)
    fecha_ingresado = Column(DateTime, default=datetime.now())
    fecha_programado = Column(DateTime, nullable=False)
    estado = Column(SQLAEnum(m.EstadoPedido), default=m.EstadoPedido.pendiente)
    observaciones = Column(String)
    cliente = relationship('Clientes', back_populates='pedidos')
    paradas = relationship('Paradas', back_populates='pedido', cascade="all, delete-orphan")

# Crea un pedido y sus paradas asociadas
def add_pedido_db(pedido):
    with get_db() as db:
        pedido_obj = pedido.dict()
        paradas = pedido_obj.pop('paradas', [])
        pedido_obj = Pedidos(**pedido_obj)
        db.add(pedido_obj)
        db.flush()
        paradas_obj = []
        for parada in paradas:           
            parada_obj = Paradas(**parada)
            parada_obj.id_pedido = pedido_obj.id
            db.add(parada_obj)
            db.flush()
            paradas_obj.append(parada_obj)
        db.commit()
        pedido_obj.paradas = paradas_obj
        return pedido_obj

def get_pedido_db(id_pedido):
    with get_db() as db:
        pedido = db.query(Pedidos).options(
            joinedload(Pedidos.cliente),
            joinedload(Pedidos.paradas)
        ).filter(Pedidos.id == id_pedido).first()
        return pedido

# Obtiene los pedidos desde offset hasta offset+limit
def get_pedidos_db(limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        search_func = True
        if search:
            search_func = search_func & (
                or_(
                    cast(Pedidos.cliente_documento, String).ilike(f'%{search}%'),
                    cast(Pedidos.prioridad, String).ilike(f'%{search}%'),
                    cast(Pedidos.tipo, String).ilike(f'%{search}%'),
                    Pedidos.fecha_programado.ilike(f'%{search}%')
                )
            )
        pedidos = db.query(Pedidos).filter(search_func).offset(offset).limit(limit).all()
        cantidad = db.query(Pedidos).filter(search_func).count()
        return pedidos, cantidad

def get_pedidos_by_cliente_db(documento: int, limit: int = 100, offset: int = 0):
    with get_db() as db:
        pedidos = db.query(Pedidos).filter(Pedidos.cliente_documento == documento).offset(offset).limit(limit).all()
        cantidad = db.query(Pedidos).filter(Pedidos.cliente_documento == documento).count()
        return pedidos, cantidad
    
# Obtiene los pedidos creados en un rango de fechas
def get_pedidos_by_rango_fechas_db(fecha_inicio: DateTime, fecha_fin: DateTime, limit: int = 100, offset: int = 0):
    with get_db() as db:
        pedidos = db.query(Pedidos).filter(Pedidos.fecha_ingresado >= fecha_inicio, Pedidos.fecha_ingresado <= fecha_fin).offset(offset).limit(limit).all()
        cantidad = db.query(Pedidos).filter(Pedidos.fecha_ingresado >= fecha_inicio, Pedidos.fecha_ingresado <= fecha_fin).count()
        return pedidos, cantidad
    
# Obtiene los pedidos tales que su fecha de programación sea igual a la fecha dada
def get_pedidos_by_fecha_db(fecha_str: str, limit: int = 100, offset: int = 0):
    with get_db() as db:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        pedidos = db.query(Pedidos).options(
            joinedload(Pedidos.cliente).joinedload(Clientes.caracteristicas),
            joinedload(Pedidos.paradas)
        ).filter(Pedidos.fecha_programado == fecha).offset(offset).limit(limit).all()
        cantidad = db.query(Pedidos).filter(Pedidos.fecha_programado == fecha).count()
        return pedidos, cantidad

def update_pedido_db(id_pedido, pedido):
    with get_db() as db:
        db.query(Pedidos).filter(Pedidos.id == id_pedido).update(pedido.dict())
        db.commit()
        return pedido

def delete_pedido_db(id_pedido):
    with get_db() as db:
        db.query(Pedidos).filter(Pedidos.id == id_pedido).delete()
        db.commit()
        return {"message": f"Pedido con ID {id_pedido} eliminado correctamente."}
    
# endregion

# region TipoParada
class TiposParadas(Base):
    __tablename__ = 'tipo_parada'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

def get_tipo_parada_db(id_tipo_parada):
    with get_db() as db:
        return db.query(TiposParadas).filter(TiposParadas.id == id_tipo_parada).first()

def get_tipos_paradas_db(limit: int = 100, offset: int = 0):
    with get_db() as db:
        tipos_parada = db.query(TiposParadas).offset(offset).limit(limit).all()
        cantidad = db.query(TiposParadas).count()
        return tipos_parada, cantidad
    
def add_tipo_parada_db(tipo_parada):
    with get_db() as db:
        tipo_parada_obj = TiposParadas(**tipo_parada.dict())
        db.add(tipo_parada_obj)
        db.commit()
        db.refresh(tipo_parada_obj)
        return tipo_parada_obj

def update_tipo_parada_db(id_tipo_parada, tipo_parada):
    with get_db() as db:
        db.query(TiposParadas).filter(TiposParadas.id == id_tipo_parada).update(tipo_parada.dict())
        db.commit()
        return tipo_parada
    
def delete_tipo_parada_db(id_tipo_parada):
    with get_db() as db:
        db.query(TiposParadas).filter(TiposParadas.id == id_tipo_parada).delete()
        db.commit()
        return {"message": f"Tipo de parada con ID {id_tipo_parada} eliminado correctamente."}
    
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
    ventana_horaria_inicio = Column(Time)
    ventana_horaria_fin = Column(Time)
    tipo = Column(Integer, ForeignKey('tipo_parada.id'))
    observaciones = Column(String)
    pedido = relationship('Pedidos', back_populates='paradas')

# Agrega una parada a un pedido
def add_parada_pedido_db(parada, id_pedido):
    with get_db() as db:
        #parada_obj = Paradas(**parada.dict())
        parada_obj = Paradas(**parada)
        parada_obj.id_pedido = id_pedido
        db.add(parada_obj)
        db.commit()
        db.refresh(parada_obj)
        return parada_obj
    
def get_parada_db(id_parada, ):
    with get_db() as db:
        return db.query(Paradas).filter(Paradas.id_parada == id_parada).first()

def get_paradas_pedido_db(id_pedido, limit: int = 100, offset: int = 0):
    with get_db() as db:
        paradas = db.query(Paradas).filter(Paradas.id_pedido == id_pedido).order_by(Paradas.posicion_en_pedido).offset(offset).limit(limit).all()
        cantidad = db.query(Paradas).filter(Paradas.id_pedido == id_pedido).count()
        return paradas, cantidad

def update_parada_db(id_parada, parada):
    with get_db() as db:
        db.query(Paradas).filter(Paradas.id_parada == id_parada).update(parada.dict())
        db.commit()
        return parada
    
# Elimina una parada y actualiza las posiciones de las paradas restantes
def delete_parada_db(id_parada):
    with get_db() as db:
        parada = db.query(Paradas).filter(Paradas.id_parada == id_parada).first()
        id_pedido = parada.id_pedido
        db.query(Paradas).filter(Paradas.id_parada == id_parada).delete()
        db.query(Paradas).filter(Paradas.id_pedido == id_pedido, Paradas.posicion_en_pedido > parada.posicion_en_pedido).update({Paradas.posicion_en_pedido: Paradas.posicion_en_pedido - 1})
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
    disponibilidad = Column(Boolean, default=True)
    activo = Column(Boolean, default=True)
    observaciones = Column(String)

    caracteristicas = relationship(
        'Caracteristicas',
        secondary='vehiculos_caracteristicas',
        backref='vehiculos'
    )

    __table_args__ = (
        CheckConstraint('capacidad_convencional > 0', name='capacidad_convencional_check'),
        CheckConstraint('capacidad_silla_de_ruedas > 0', name='capacidad_silla_de_ruedas_check'),
    )

# Agrega un vehículo y sus características asociadas
def add_vehiculo_db(vehiculo):
    with get_db() as db:
        vehiculo_obj = vehiculo.dict()
        caracteristicas = vehiculo_obj.pop('caracteristicas', [])
        vehiculo_obj = Vehiculos(**vehiculo_obj)
        db.add(vehiculo_obj)
        db.flush()
        caracteristicas_obj = []
        if caracteristicas:
            for caracteristica in caracteristicas:
                caracteristica_obj = VehiculosCaracteristicas(id_vehiculo=vehiculo_obj.id, id_caracteristica=caracteristica)
                db.add(caracteristica_obj)
                db.flush()
                caracteristicas_obj.append(caracteristica_obj)
        db.commit()
        return vehiculo_obj
    
def get_vehiculo_db(id_vehiculo):
    with get_db() as db:
        return db.query(Vehiculos).filter(Vehiculos.id == id_vehiculo).first()

def get_vehiculos_db(limit: int = 100, offset: int = 0):
    with get_db() as db:
        vehiculos = db.query(Vehiculos).offset(offset).limit(limit).all()
        cantidad = db.query(Vehiculos).count()
        return vehiculos, cantidad

def get_vehiculo_by_matricula_db(matricula):
    with get_db() as db:
        return db.query(Vehiculos).filter(Vehiculos.matricula == matricula).first()

def get_vehiculos_by_activo_db(activo: bool, limit: int = 100, offset: int = 0):
    with get_db() as db:
        vehiculos = db.query(Vehiculos).filter(Vehiculos.activo == activo).offset(offset).limit(limit).all()
        cantidad = db.query(Vehiculos).filter(Vehiculos.activo == activo).count()
        return vehiculos, cantidad

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
    id_caracteristica = Column(Integer, ForeignKey('caracteristicas.id'))

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
    activo = Column(Boolean, default=True)
    observaciones = Column(String)

def add_chofer_db(chofer):
    with get_db() as db:
        chofer_obj = Choferes(**chofer.dict())
        db.add(chofer_obj)
        db.commit()
        db.refresh(chofer_obj)
        return chofer_obj
    
def get_chofer_db(id):
    with get_db() as db:
        return db.query(Choferes).filter(Choferes.id == id).first()
    
def get_choferes_db(limit: int = 100, offset: int = 0):
    with get_db() as db:
        choferes = db.query(Choferes).offset(offset).limit(limit).all()
        cantidad = db.query(Choferes).count()
        return choferes, cantidad

def get_choferes_by_activo_db(activo, limit: int = 100, offset: int = 0):
    with get_db() as db:
        choferes = db.query(Choferes).filter(Choferes.activo == activo).all()
        return choferes

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
    activo = Column(Boolean, default=True)
    observaciones = Column(String)

def add_lugar_comun_db(deposito):
    with get_db() as db:
        deposito_obj = LugaresComunes(**deposito.dict())
        db.add(deposito_obj)
        db.commit()
        db.refresh(deposito_obj)
        return deposito_obj
    
def get_lugar_comun_db(id):
    with get_db() as db:
        return db.query(LugaresComunes).filter(LugaresComunes.id == id).first()

def get_lugares_comunes_db(limit: int = 100, offset: int = 0):
    with get_db() as db:
        lugares_comunes = db.query(LugaresComunes).offset(offset).limit(limit).all()
        cantidad = db.query(LugaresComunes).count()
        return lugares_comunes, cantidad

def get_lugares_comunes_by_activo_db(activo, limit: int = 100, offset: int = 0):
    with get_db() as db:
        lugares_comunes = db.query(LugaresComunes).filter(LugaresComunes.activo == activo).all()
        return lugares_comunes

def update_lugar_comun_db(id, deposito):
    with get_db() as db:
        db.query(LugaresComunes).filter(LugaresComunes.id == id).update(deposito.dict())
        db.commit()
        return deposito
    
def delete_lugar_comun_db(id):
    with get_db() as db:
        db.query(LugaresComunes).filter(LugaresComunes.id == id).delete()
        db.commit()
        return {"message": f"Depósito con ID {id} eliminado correctamente."}

# endregion

# region Planificaciones
class Planificaciones(Base):
    __tablename__ = 'planificaciones'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    fecha = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now())
    observaciones = Column(String)

    turnos = relationship('Turnos', back_populates='planificacion')
    rutas = relationship('Rutas', back_populates='planificacion')

# Crea un planificación y dos turnos asociados
def crear_planificacion(user_id, planificacion, turnos, rutas):
    with get_db() as db:
        log.info(planificacion)
        log.info(user_id)
        planificacion.usuario_id = user_id
        planificacion_obj = add_planificacion_db(planificacion)

        # Crea dos turnos por defecto asociados a la planificación
        for t in turnos:
            t.id_planificacion = planificacion_obj.id
            #turno = Turnos(id_planificacion=planificacion_obj.id, **t)
            turno = add_turno_db(t)
        for r in rutas:
            r.id_planificacion = planificacion_obj.id
            rutas_obj = add_ruta_db(r)

        # Asocia a la planificación los vehículos, choferes y lugares comunes disponibles
        planificacion_obj.vehiculos = get_vehiculos_db()
        planificacion_obj.choferes = get_choferes_db()
        planificacion_obj.lugares_comunes = get_lugares_comunes_db()

        # Asocia a la planificación los pedidos para su fecha
        planificacion_obj.pedios = get_pedidos_by_fecha_db(datetime.strftime(planificacion_obj.fecha, '%Y-%m-%d'))

        return planificacion_obj

def add_planificacion_db(planificacion):
    with get_db() as db:
        planificacion_obj = Planificaciones(**planificacion.dict())
        db.add(planificacion_obj)
        db.commit()
        db.refresh(planificacion_obj)
        return planificacion_obj

# Obtiene una planificación con sus turnos y rutas asociados, y las visitas asociadas a las rutas,
# paradas o lugares comunes asociados a las visitas, vehiculos y choferes asociados a las rutas
def get_planificacion_db(id_planificacion: int):
    with get_db() as db:
        planificacion = db.query(Planificaciones).options(
            joinedload(Planificaciones.turnos),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.vehiculo),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.rutas_turnos)
                .joinedload(RutasTurnos.chofer),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.visitas)
        ).filter(Planificaciones.id == id_planificacion).first()

        # Completar las visitas con sus detalles
        for ruta in planificacion.rutas:
            for visita in ruta.visitas:
                if visita.tipo_item == m.TipoItemVisita.parada:
                    visita.item = db.query(Paradas).filter(Paradas.id == visita.id_item).first()
                else:
                    visita.item = db.query(LugaresComunes).filter(LugaresComunes.id == visita.id_item).first()

        return planificacion

    
# Obtiene las planificaciones para un determinado día
def get_planificaciones_by_fecha_db(fecha: str, limit: int = 100, offset: int = 0):
    with get_db() as db:
        fecha = datetime.strptime(fecha, '%Y-%m-%d')
        log.info(fecha)
        planificaciones = db.query(Planificaciones).options(
            joinedload(Planificaciones.turnos),
            joinedload(Planificaciones.rutas)
                .load_only(Rutas.id, Rutas.hora_fin, Rutas.hora_inicio)
                .joinedload(Rutas.vehiculo),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.rutas_turnos)
                .joinedload(RutasTurnos.chofer),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.visitas)
        ).filter(Planificaciones.fecha == fecha).offset(offset).limit(limit).all()
        log.info(planificaciones)
        cantidad = db.query(Planificaciones).filter(Planificaciones.fecha == fecha).count()
        return planificaciones, cantidad

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
    descripcion = Column(String)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    planificacion = relationship('Planificaciones', back_populates='turnos')

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

def get_turnos_by_planificacion_db(id_planificacion):
    with get_db() as db:
        turnos = db.query(Turnos).filter(Turnos.id_planificacion == id_planificacion).all()
        return turnos

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
    id_planificacion = Column(Integer, ForeignKey('planificaciones.id'))
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id'))
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    geometria = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    observaciones = Column(String)
    planificacion = relationship('Planificaciones', back_populates='rutas')
    vehiculo = relationship('Vehiculos')
    rutas_turnos = relationship('RutasTurnos')
    visitas = relationship('Visitas', back_populates='ruta')

def add_ruta_db(ruta):
    with get_db() as db:
        geometria_wkt = WKTElement(LineString(ruta.geometria).wkt, srid=4326)
        ruta_obj = Rutas(
            id_planificacion=ruta.id_planificacion,
            id_vehiculo=ruta.id_vehiculo,
            hora_inicio=ruta.hora_inicio,
            hora_fin=ruta.hora_fin,
            geometria=geometria_wkt,  
            observaciones=ruta.observaciones
        )
        db.add(ruta_obj)
        db.commit()
        db.refresh(ruta_obj)
        return ruta_obj
    
def get_ruta_db(id_ruta):
    with get_db() as db:
        return db.query(Rutas).filter(Rutas.id_ruta == id_ruta).first()

def get_rutas_by_planificacion_db(id_planificacion):
    with get_db() as db:
        rutas = db.query(Rutas).filter(Rutas.id_planificacion == id_planificacion).all()
        return rutas

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

# region RutasTurnos
class RutasTurnos(Base):
    __tablename__ = 'rutas_turnos'

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey('rutas.id'))
    id_turno = Column(Integer, ForeignKey('turnos.id'))
    id_chofer = Column(Integer, ForeignKey('choferes.id'))
    chofer = relationship('Choferes')

def add_ruta_turno_db(ruta_turno):
    with get_db() as db:
        ruta_turno_obj = RutasTurnos(**ruta_turno.dict())
        db.add(ruta_turno_obj)
        db.commit()
        db.refresh(ruta_turno_obj)
        return ruta_turno_obj
    
def get_ruta_turno_db(id_ruta, id_turno):
    with get_db() as db:
        return db.query(RutasTurnos).filter(RutasTurnos.id_ruta == id_ruta, RutasTurnos.id_turno == id_turno).first()
    
def get_ruta_turnos_by_ruta_db(id_ruta):
    with get_db() as db:
        ruta_turnos = db.query(RutasTurnos).filter(RutasTurnos.id_ruta == id_ruta).all()
        return ruta_turnos
    
def update_ruta_turno_db(id_ruta, id_turno, ruta_turno):
    with get_db() as db:
        db.query(RutasTurnos).filter(RutasTurnos.id_ruta == id_ruta, RutasTurnos.id_turno == id_turno).update(ruta_turno.dict())
        db.commit()
        return ruta_turno
    
def delete_ruta_turno_db(id_ruta, id_turno):
    with get_db() as db:
        db.query(RutasTurnos).filter(RutasTurnos.id_ruta == id_ruta, RutasTurnos.id_turno == id_turno).delete()
        db.commit()
        return {"message": f"Ruta-Turno con ID {id_ruta}-{id_turno} eliminada correctamente."}
    
# endregion

# region Visitas

class Visitas(Base):
    __tablename__ = 'visitas'

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey('rutas.id'))
    id_item = Column(Integer, nullable=False)
    tipo_item = Column(SQLAEnum(m.TipoItemVisita), nullable=False)
    estado = Column(SQLAEnum(m.EstadoVisita), nullable=False)
    hora_llegada = Column(Time, nullable=False)
    hora_salida = Column(DateTime, nullable=False)
    observaciones = Column(String)
    ruta = relationship('Rutas', back_populates='visitas')
    
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

def get_visitas_by_ruta_db(id_ruta):
    with get_db() as db:
        visitas = db.query(Visitas).filter(Visitas.id_ruta == id_ruta).all()
        return visitas

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
