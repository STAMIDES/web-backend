from sqlite3 import Date
from sqlalchemy import create_engine, Column, ForeignKey,Integer, cast, func, String, Float, DateTime, Time, Boolean, Enum as SQLAEnum, or_, distinct # type: ignore
from enum import Enum
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker, joinedload, relationship # type: ignore
from geoalchemy2 import Geometry # type: ignore
from datetime import datetime, timedelta, time
from shapely.geometry import LineString
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from fastapi import HTTPException # type: ignore
import hashlib
import random
import models as m
import logging
log = logging.getLogger(__name__)
import os

from sqlalchemy import CheckConstraint # type: ignore

import autenticacion.autenticacion as aut

SQLALCHEMY_DATABASE_URL = 'postgresql://fernando:123123123@db:5432/mides'

dominio_frontend=os.getenv('DOMINIO_FRONTEND')

INVITATION_SUBJECT_TEMPLATE = "Invitación al Sistema de Servicio de transporte accesible"
INVITATION_BODY_TEMPLATE = f""" Hola {{nombre_usuario}}, 
Felicidades has sido invitado a ser un usuario del Sistema de Servicio de transporte accesible, 
ingresa aqui {dominio_frontend}/cuenta/registro/{{hash_link}} para generar una contraseña y completar tu registro."""



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

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True, unique=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

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
        usuario_obj = Usuarios(email=usuarioInv.email,
                               nombre=nuevo_user.nombre, hashed_password=hashed_password)
        db.add(usuario_obj)
        db.query(InvitacionUsuario).filter(InvitacionUsuario.hash_link == usuarioInv.hash_link,
                                          InvitacionUsuario.used==False ).update({"used": True})
        db.commit()
        db.refresh(usuario_obj)
        return usuario_obj

# Obtiene los usuarios desde offset hasta offset+limit, devuelve también la cantidad total de usuarios   
def get_usuarios(offset: int = 0, limit: int = 100, search: str = ''):
    with get_db() as db:
        if search:
            search_func = or_(
                    Usuarios.nombre.ilike(f'%{search}%'),
                    Usuarios.email.ilike(f'%{search}%'),
                )
        else:
            search_func = True
        usuarios = db.query(Usuarios).filter(search_func).offset(offset).limit(limit).all()
        public_users_full = []
        for user in usuarios:
            public_users_full.append({
                'id': user.id,
                'email': user.email,
                'nombre': user.nombre,
            })
        cantidad = db.query(Usuarios).filter(search_func).count()
        return public_users_full, cantidad

def get_usuario_db(id_usuario):
    with get_db() as db:
        usuario= db.query(Usuarios).filter(Usuarios.id == id_usuario).first()
        return {
            'id': usuario.id,
            'email': usuario.email,
            'nombre': usuario.nombre,
        }
    
def update_usuario_db(email, usuario):
    with get_db() as db:
        user_db = db.query(Usuarios).filter(Usuarios.email == email).first()
        if user_db:
            # Update individual fields
            user_db.hashed_password = usuario.hashed_password
            # Update any other fields you need to update
            db.commit()
            return user_db
        return None

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

def logout(refresh_token: str):
    with get_db() as db:
        user = db.query(Usuarios, RefreshToken).\
            join(RefreshToken, Usuarios.id == RefreshToken.user_id).\
            filter( RefreshToken.token == refresh_token).\
            first()
        if not user:
            return False
        db.query(Usuarios).filter(Usuarios.id == user.Usuarios.id).update({"token": None})
        db.query(RefreshToken).filter(RefreshToken.token == refresh_token).update({"is_revoked": True})
        db.commit()
        return True


def is_refresh_token_valid(user_id: int, refresh_token: str):
    with get_db() as db:
        token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()
        return token is not None
    


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

def generate_password_reset_token(email: str, expiration_hours: int = 24):
    try:
        with get_db() as db:
            counter = 0
            while counter < 10:
                token = hashlib.sha256(f"{email}{random.random()}".encode()).hexdigest()
                existing_token = db.query(PasswordResetToken).filter(
                    PasswordResetToken.token == token,
                    PasswordResetToken.used == False
                ).first()
                if not existing_token:
                    break
                counter += 1

            if counter >= 10:
                return None

            new_token = PasswordResetToken(
                token=token,
                email=email,
                expires_at=datetime.utcnow() + timedelta(hours=expiration_hours)
            )
            db.add(new_token)
            db.commit()
            db.refresh(new_token)
            return token
    except Exception as e:
        print(e)
        return None

def get_password_reset_token(token: str, email: str):
    with get_db() as db:
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.email == email,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()

def mark_password_reset_token_used(token: str):
    with get_db() as db:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).update({"used": True})
        db.commit()

# endregion

# region Clientes

class Clientes(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True, index=True)
    documento = Column(Integer, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    direccion = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
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
        cliente = db.query(Clientes).options(
            joinedload(Clientes.caracteristicas)).filter(Clientes.id == id).first()
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
                    Clientes.caracteristicas.any(Caracteristicas.nombre.ilike(f'%{search}%'))
                )
            )
        clientes = db.query(Clientes).options(
            joinedload(Clientes.caracteristicas)
        ).filter(search_func).offset(offset).limit(limit).all()
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
        cliente_obj = cliente.dict()
        caracteristicas = cliente_obj.pop('caracteristicas', [])
        db.query(Clientes).filter(Clientes.documento == documento).update(cliente_obj)
        db.commit()
        
        cliente_id = db.query(Clientes.id).filter(Clientes.documento == documento).scalar()
        
        if caracteristicas:
            existing_caracteristicas = db.query(ClientesCaracteristicas).filter(ClientesCaracteristicas.id_cliente == cliente_id).all()
            existing_ids = {c.id_caracteristica for c in existing_caracteristicas}
            new_ids = set(caracteristicas)
            
            to_add = new_ids - existing_ids
            to_remove = existing_ids - new_ids
            
            for caracteristica in to_add:
                caracteristica_obj = ClientesCaracteristicas(id_cliente=cliente_id, id_caracteristica=caracteristica)
                db.add(caracteristica_obj)
            
            for caracteristica in to_remove:
                db.query(ClientesCaracteristicas).filter(ClientesCaracteristicas.id_cliente == cliente_id, ClientesCaracteristicas.id_caracteristica == caracteristica).delete()
        
        db.commit()
        updated_cliente = db.query(Clientes).options(
            joinedload(Clientes.caracteristicas)).filter(Clientes.documento == documento).first()
        return updated_cliente

def delete_cliente_db(id):
    with get_db() as db:
        # Delete client from the database based on document
        db.query(Clientes).filter(Clientes.id == id).update({"activo": False})
        db.commit()
        return {"message": f"Cliente eliminado correctamente."}

def activate_cliente_db(documento):
    with get_db() as db:
        cliente = db.query(Clientes).filter(Clientes.documento == documento).first()
        if cliente:
            cliente.activo = True
            db.commit()
            return {"message": f"Cliente activado correctamente."}
        else:
            return {"message": f"Cliente no encontrado."}
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
        paradas_data = pedido_obj.pop('paradas', [])
        pedido_obj = Pedidos(**pedido_obj)
        db.add(pedido_obj)
        db.flush()
        paradas_obj = []
        for parada_item_data in paradas_data:           
            if parada_item_data.get('ventana_horaria_inicio') and isinstance(parada_item_data['ventana_horaria_inicio'], time):
                parada_item_data['ventana_horaria_inicio'] = parada_item_data['ventana_horaria_inicio'].replace(second=0, microsecond=0)
            if parada_item_data.get('ventana_horaria_fin') and isinstance(parada_item_data['ventana_horaria_fin'], time):
                parada_item_data['ventana_horaria_fin'] = parada_item_data['ventana_horaria_fin'].replace(second=0, microsecond=0)
            
            parada_obj = Paradas(**parada_item_data)
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

def get_pedidos_by_id_db(id_pedidos):
    with get_db() as db:
        pedidos = db.query(Pedidos) \
            .join(Pedidos.cliente) \
            .outerjoin(Clientes.caracteristicas) \
            .outerjoin(Pedidos.paradas) \
            .outerjoin(Paradas.tipo_parada).filter(Pedidos.id.in_(id_pedidos)).all()
        return pedidos

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
def get_pedidos_by_fecha_db(fecha_str: str, limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        search_func = Pedidos.fecha_programado == fecha
        if search:
            log.info('Searching for %s', search)
            search_func = search_func & (
                or_(
                    Clientes.nombre.ilike(f'%{search}%'),
                    Clientes.apellido.ilike(f'%{search}%'),
                    cast(Clientes.documento, String).ilike(f'%{search}%'),
                    Clientes.caracteristicas.any(Caracteristicas.nombre.ilike(f'%{search}%')),
                    Paradas.direccion.ilike(f'%{search}%'),
                    TiposParadas.nombre.ilike(f'%{search}%')
                )
            )

        # Realizamos los joins necesarios para que los filtros de relaciones se apliquen
        query = db.query(Pedidos) \
            .join(Pedidos.cliente) \
            .outerjoin(Clientes.caracteristicas) \
            .outerjoin(Pedidos.paradas) \
            .outerjoin(Paradas.tipo_parada) \
            .filter(search_func)

        cantidad = query.with_entities(func.count(distinct(Pedidos.id))).scalar()

        # For the main query, use a subquery approach to apply pagination correctly
        subquery = db.query(Pedidos.id).distinct() \
            .join(Pedidos.cliente) \
            .outerjoin(Clientes.caracteristicas) \
            .outerjoin(Pedidos.paradas) \
            .outerjoin(Paradas.tipo_parada) \
            .filter(search_func) \
            .offset(offset) \
            .limit(limit) \
            .subquery()

        # Now get the full pedidos with the limited IDs
        pedidos = db.query(Pedidos) \
            .filter(Pedidos.id.in_(subquery)) \
            .options(
                joinedload(Pedidos.cliente).joinedload(Clientes.caracteristicas),
                joinedload(Pedidos.paradas).joinedload(Paradas.tipo_parada)
            ).all()

        return pedidos, cantidad

def update_pedido_db(id_pedido, pedido):
    with get_db() as db:
        # Verificar si el pedido existe
        existing_pedido = db.query(Pedidos).filter(Pedidos.id == id_pedido).first()
        if not existing_pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")

        # Verificar si el cliente existe
        cliente_existente = db.query(Clientes).filter(Clientes.documento == pedido.cliente_documento).first()
        if not cliente_existente:
            raise HTTPException(status_code=400, detail="El cliente especificado no existe.")

        # Validar formato de fecha programada
        if not isinstance(pedido.fecha_programado, datetime):
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Se espera un objeto datetime.")

        # Convertir el pedido a diccionario sin los valores no enviados
        update_data = pedido.dict(exclude_unset=True)
        update_data.pop("id", None)
        update_data.pop("paradas", None)

        # Actualizar el pedido en la base de datos
        db.query(Pedidos).filter(Pedidos.id == id_pedido).update(update_data)

        db.commit()
        return pedido

def delete_pedido_db(id_pedido):
    with get_db() as db:
        # Delete related records in the paradas table
        db.query(Paradas).filter(Paradas.id_pedido == id_pedido).delete()
        
        # Delete the pedido record
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
    tipo_parada = relationship('TiposParadas')
    pedido = relationship('Pedidos', foreign_keys=[id_pedido])

# Agrega una parada a un pedido
def add_parada_pedido_db(parada: dict, id_pedido: int):
    with get_db() as db:
        if parada.get('ventana_horaria_inicio') and isinstance(parada['ventana_horaria_inicio'], time):
            parada['ventana_horaria_inicio'] = parada['ventana_horaria_inicio'].replace(second=0, microsecond=0)
        if parada.get('ventana_horaria_fin') and isinstance(parada['ventana_horaria_fin'], time):
            parada['ventana_horaria_fin'] = parada['ventana_horaria_fin'].replace(second=0, microsecond=0)

        parada_obj = Paradas(**parada)
        parada_obj.id_pedido = id_pedido
        db.add(parada_obj)
        db.commit()
        db.refresh(parada_obj)
        return parada_obj
    
def get_parada_db(id_parada: int):
    with get_db() as db:
        return db.query(Paradas).filter(Paradas.id == id_parada).first()

def get_paradas_pedido_db(id_pedido, limit: int = 100, offset: int = 0):
    with get_db() as db:
        paradas = db.query(Paradas).filter(Paradas.id_pedido == id_pedido).order_by(Paradas.posicion_en_pedido).offset(offset).limit(limit).all()
        cantidad = db.query(Paradas).filter(Paradas.id_pedido == id_pedido).count()
        return paradas, cantidad

def update_parada_db(id_parada, parada):
    with get_db() as db:
        # Modify the Pydantic model instance directly if fields are present and are time objects
        if hasattr(parada, 'ventana_horaria_inicio') and parada.ventana_horaria_inicio is not None and isinstance(parada.ventana_horaria_inicio, time):
            parada.ventana_horaria_inicio = parada.ventana_horaria_inicio.replace(second=0, microsecond=0)
        
        if hasattr(parada, 'ventana_horaria_fin') and parada.ventana_horaria_fin is not None and isinstance(parada.ventana_horaria_fin, time):
            parada.ventana_horaria_fin = parada.ventana_horaria_fin.replace(second=0, microsecond=0)

        update_data = parada.dict(exclude_unset=True) 

        db.query(Paradas).filter(Paradas.id == id_parada).update(update_data)
        db.commit()
        return parada
    
# Elimina una parada y actualiza las posiciones de las paradas restantes
def delete_parada_db(id_parada: int):
    with get_db() as db:
        parada = db.query(Paradas).filter(Paradas.id == id_parada).first()
        if not parada:
            raise HTTPException(status_code=404, detail=f"Parada con ID {id_parada} no encontrada.")
        id_pedido = parada.id_pedido
        db.query(Paradas).filter(Paradas.id == id_parada).delete()
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
    capacidad_convencional = Column(Integer, nullable=False)
    capacidad_silla_de_ruedas = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    borrado = Column(Boolean, default=False)
    observaciones = Column(String)

    caracteristicas = relationship(
        'Caracteristicas',
        secondary='vehiculos_caracteristicas',
        backref='vehiculos'
    )

    __table_args__ = (
        CheckConstraint('capacidad_convencional > 0', name='capacidad_convencional_check'),
        CheckConstraint('capacidad_silla_de_ruedas >= 0', name='capacidad_silla_de_ruedas_check'),
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
        return db.query(Vehiculos).options(
            joinedload(Vehiculos.caracteristicas)
        ).filter(Vehiculos.id == id_vehiculo, Vehiculos.borrado == False).first()

def get_vehiculos_db(limit: int = 100, offset: int = 0, search = ''):
    with get_db() as db:
        search_func = Vehiculos.borrado == False
        if search:
            search_func = search_func & (
                or_(
                    Vehiculos.matricula.ilike(f'%{search}%'),
                    Vehiculos.descripcion.ilike(f'%{search}%'),
                    cast(Vehiculos.capacidad_convencional, String).ilike(f'%{search}%'),
                    cast(Vehiculos.capacidad_silla_de_ruedas, String).ilike(f'%{search}%'),
                    Vehiculos.observaciones.ilike(f'%{search}%')
                )
            )
        vehiculos = db.query(Vehiculos).options(
            joinedload(Vehiculos.caracteristicas)
            ).filter(search_func).order_by(Vehiculos.activo.desc(), Vehiculos.matricula.asc()).offset(offset).limit(limit).all()
        cantidad = db.query(Vehiculos).filter(search_func).count()
        return vehiculos, cantidad

def get_vehiculo_by_matricula_db(matricula):
    with get_db() as db:
        return db.query(Vehiculos).filter(Vehiculos.matricula == matricula, Vehiculos.borrado == False).first()

def get_vehiculos_by_activo_db(activo: bool, limit: int = 100, offset: int = 0):
    with get_db() as db:
        vehiculos = db.query(Vehiculos).filter(Vehiculos.activo == activo, Vehiculos.borrado == False).order_by(Vehiculos.matricula.asc()).offset(offset).limit(limit).all()
        cantidad = db.query(Vehiculos).filter(Vehiculos.activo == activo, Vehiculos.borrado == False).count()
        return vehiculos, cantidad

def update_vehiculo_db(id_vehiculo, vehiculo):
    with get_db() as db:
        # Extract characteristics from the vehicle data
        vehiculo_obj = vehiculo.dict()
        caracteristicas = vehiculo_obj.pop('caracteristicas', [])
        
        # Update vehicle in the database
        db.query(Vehiculos).filter(Vehiculos.id == id_vehiculo).update({
            'matricula': vehiculo.matricula,
            'descripcion': vehiculo.descripcion,
            'capacidad_convencional': vehiculo.capacidad_convencional,
            'capacidad_silla_de_ruedas': vehiculo.capacidad_silla_de_ruedas,
            'observaciones': vehiculo.observaciones
        })
        db.commit()
        
        # Handle characteristics
        if caracteristicas:
            existing_caracteristicas = db.query(VehiculosCaracteristicas).filter(
                VehiculosCaracteristicas.id_vehiculo == id_vehiculo
            ).all()
            existing_ids = {c.id_caracteristica for c in existing_caracteristicas}
            new_ids = set(caracteristicas)
            
            to_add = new_ids - existing_ids
            to_remove = existing_ids - new_ids
            
            # Add new characteristics
            for caracteristica in to_add:
                caracteristica_obj = VehiculosCaracteristicas(
                    id_vehiculo=id_vehiculo, 
                    id_caracteristica=caracteristica
                )
                db.add(caracteristica_obj)
            
            # Remove existing characteristics that are not in the new set
            for caracteristica in to_remove:
                db.query(VehiculosCaracteristicas).filter(
                    VehiculosCaracteristicas.id_vehiculo == id_vehiculo, 
                    VehiculosCaracteristicas.id_caracteristica == caracteristica
                ).delete()
        
        db.commit()
        
        # Return the updated vehicle with characteristics loaded
        updated_vehiculo = db.query(Vehiculos).options(
            joinedload(Vehiculos.caracteristicas)
        ).filter(Vehiculos.id == id_vehiculo).first()
        
        return updated_vehiculo

def update_vehiculo_estado_db(id_vehiculo, activo):
    with get_db() as db:
        activo_bool = activo.lower() in ['true', '1', 't', 'y', 'yes']
        db.query(Vehiculos).filter(Vehiculos.id == id_vehiculo).update({"activo": activo_bool})
        db.commit()
    
def delete_vehiculo_db(id_vehiculo):
    with get_db() as db:
        result = db.query(Vehiculos).filter(Vehiculos.id == id_vehiculo, Vehiculos.borrado == False).update({"activo": False, "borrado": True})
        if result == 0:
            return {"error": f"El vehículo con ID {id_vehiculo} ya estaba eliminado o no existe."}
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
    borrado = Column(Boolean, default=False)
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
        return db.query(Choferes).filter(Choferes.id == id, Choferes.borrado == False).first()
    
def get_choferes_db(limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        search_func = Choferes.borrado == False
        if search:
            search_func = search_func & (
                or_(
                    Choferes.nombre.ilike(f'%{search}%'),
                    Choferes.apellido.ilike(f'%{search}%'),
                    cast(Choferes.documento, String).ilike(f'%{search}%'),
                    Choferes.telefono.ilike(f'%{search}%'),
                )
            )
        choferes = db.query(Choferes).filter(search_func).order_by(Choferes.activo.desc(), Choferes.apellido.asc()).offset(offset).limit(limit).all()
        cantidad = db.query(Choferes).filter(search_func).count()
        return choferes, cantidad

def get_choferes_activos_db(activo, limit: int = 100, offset: int = 0):
    with get_db() as db:
        choferes = db.query(Choferes).filter(Choferes.activo == activo, Choferes.borrado == False).order_by(Choferes.apellido.asc()).all()
        return choferes

def update_chofer_db(id, chofer):
    with get_db() as db:
        db.query(Choferes).filter(Choferes.id == id).update(chofer.dict())
        db.commit()
        return chofer

def update_chofer_estado_db(id_chofer, activo):
    with get_db() as db:
        activo_bool = activo.lower() in ['true', '1', 't', 'y', 'yes']
        db.query(Choferes).filter(Choferes.id == id_chofer).update({"activo": activo_bool})
        db.commit()

def delete_chofer_db(id):
    with get_db() as db:
        chofer = db.query(Choferes).filter(Choferes.id == id, Choferes.borrado == False).first()
        if not chofer:
            return {"error": f"El chofer con ID {id} ya estaba eliminado o no existe."}

        # Marcar el chofer como eliminado
        db.query(Choferes).filter(Choferes.id == id).update({"activo": False, "borrado": True})
        db.commit()
        
        return {"message": f"Chofer con documento {chofer.documento} eliminado correctamente."}

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
    borrado = Column(Boolean, default=False)
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
        return db.query(LugaresComunes).filter(LugaresComunes.id == id, LugaresComunes.borrado == False).first()

def get_lugares_comunes_db(limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        filter_func = LugaresComunes.borrado == False
        if search:
            filter_func = filter_func & (
                or_(
                    LugaresComunes.nombre.ilike(f'%{search}%'),
                    LugaresComunes.direccion.ilike(f'%{search}%'),
                    LugaresComunes.observaciones.ilike(f'%{search}%')
                )
            )
        lugares_comunes = db.query(LugaresComunes).filter(filter_func).order_by(LugaresComunes.activo.desc(), LugaresComunes.nombre.asc()).offset(offset).limit(limit).all()
        cantidad = db.query(LugaresComunes).filter(filter_func).count()
        return lugares_comunes, cantidad

def get_lugares_comunes_by_activo_db(activo, limit: int = 100, offset: int = 0):
    with get_db() as db:
        lugares_comunes = db.query(LugaresComunes).filter(LugaresComunes.activo == activo, LugaresComunes.borrado == False).order_by(LugaresComunes.nombre.asc()).all()
        return lugares_comunes

def update_lugar_comun_db(id, deposito):
    with get_db() as db:
        db.query(LugaresComunes).filter(LugaresComunes.id == id).update(deposito.dict())
        db.commit()
        return deposito

def update_lugar_comun_estado_db(id_lugar_comun, activo):
    with get_db() as db:
        activo_bool = activo.lower() in ['true', '1', 't', 'y', 'yes']
        db.query(LugaresComunes).filter(LugaresComunes.id == id_lugar_comun).update({"activo": activo_bool})
        db.commit()

def delete_lugar_comun_db(id):
    with get_db() as db:
        result = db.query(LugaresComunes).filter(LugaresComunes.id == id, LugaresComunes.borrado == False).update({"activo": False, "borrado": True})
        if result == 0:
            return {"error": f"El lugar común con ID {id} ya estaba eliminado o no existe."}
        db.commit()
        return {"message": f"Lugar común con ID {id} eliminado correctamente."}

# endregion

# region Planificaciones
class Planificaciones(Base):
    __tablename__ = 'planificaciones'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    creado_por = relationship('Usuarios')
    fecha = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now())
    definitiva = Column(Boolean, nullable=False, default=True)
    observaciones = Column(String)

    turnos = relationship('Turnos', back_populates='planificacion')
    rutas = relationship('Rutas', back_populates='planificacion', order_by='Rutas.hora_inicio')
    pedidos_no_atendidos = relationship('PedidosNoAtendidos', back_populates='planificacion')
    
    @property
    def fmt_fecha(self):
        if self.fecha:
            return self.fecha.strftime("%d/%m/%Y")
        return None
        
    @property
    def fmt_fecha_creacion(self):
        if self.fecha_creacion:
            return self.fecha_creacion.strftime("%d/%m/%Y %H:%M")
        return None

class PedidosNoAtendidos(Base):
    __tablename__ = 'pedidos_no_atendidos'
    
    id = Column(Integer, primary_key=True, index=True)
    id_planificacion = Column(Integer, ForeignKey('planificaciones.id'))
    id_pedido = Column(Integer, ForeignKey('pedidos.id'))
    no_enviado_al_optimizador = Column(Boolean, default=False)
    
    planificacion = relationship('Planificaciones', back_populates='pedidos_no_atendidos')
    pedido = relationship('Pedidos')

# Crea un planificación y dos turnos asociados
def crear_planificacion(user_id, planificacion, turnos, rutas, pedidos_no_atendidos=None, pedidos_no_seleccionados=None):
    with get_db() as db:
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
            for v in r.visitas:
                v.id_ruta = rutas_obj.id
                visita_obj = add_visita_db(v)
        if pedidos_no_atendidos:
            for pedido_id in pedidos_no_atendidos:
                pedido_no_atendido = PedidosNoAtendidos(
                    id_planificacion=planificacion_obj.id,
                    id_pedido=pedido_id
                )
                db.add(pedido_no_atendido)
            db.commit()
        if pedidos_no_seleccionados:
            for pedido_id in pedidos_no_seleccionados:
                pedido_no_seleccionado = PedidosNoAtendidos(
                    id_planificacion=planificacion_obj.id,
                    id_pedido=pedido_id,
                    no_enviado_al_optimizador=True # el creador de la planificacion no envio estos pedidos al optimizador,
                )                                  # fueron dejados sin atender intencionalmente                       
                db.add(pedido_no_seleccionado)
            db.commit()
        return get_planificacion_db(planificacion_obj.id)

def add_planificacion_db(planificacion):
    with get_db() as db:
        log.info('Creando planificación: %s', planificacion)
        # Verificar si la planificación ya existe
        existing_planificacion = db.query(Planificaciones).filter(
            Planificaciones.fecha == planificacion.fecha,
        ).first()
        if existing_planificacion: # si ya existe, entonces el usuario debe elegir para ese dia cual sera la definitiva asi que se marcan ambas como falsas
            planificacion.definitiva = False
            if existing_planificacion.definitiva:
                db.query(Planificaciones).filter(Planificaciones.id == existing_planificacion.id).update({"definitiva": False})
                db.commit()
        else:
            planificacion.definitiva = True
        # Crear la planificación
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
                .joinedload(Rutas.chofer),
            joinedload(Planificaciones.rutas)
                .joinedload(Rutas.visitas),
            joinedload(Planificaciones.creado_por),
            joinedload(Planificaciones.pedidos_no_atendidos)
                .joinedload(PedidosNoAtendidos.pedido)
                .joinedload(Pedidos.cliente).joinedload(Clientes.caracteristicas),
            joinedload(Planificaciones.pedidos_no_atendidos)
                .joinedload(PedidosNoAtendidos.pedido)
                .joinedload(Pedidos.paradas)
                .joinedload(Paradas.tipo_parada)
        ).filter(Planificaciones.id == id_planificacion).first()

        if planificacion:
            # Ordenar rutas por hora de inicio
            planificacion.rutas = sorted(planificacion.rutas, key=lambda r: r.hora_inicio)
            destinos_de_pedidos = {}
            # Completar las visitas con sus detalles
            for ruta in planificacion.rutas:
                if ruta.geometria:
                    ruta_geometria_geojson = mapping(to_shape(ruta.geometria))
                    ruta.geometria = ruta_geometria_geojson['coordinates']
                for visita in ruta.visitas:
                    if visita.tipo_item == m.TipoItemVisita.parada:
                        parada = db.query(Paradas).options(
                            joinedload(Paradas.tipo_parada),
                            joinedload(Paradas.pedido).joinedload(Pedidos.cliente).joinedload(Clientes.caracteristicas)
                        ).filter(Paradas.id == visita.id_item).first()
                        
                        if parada.id_pedido not in destinos_de_pedidos:
                            # Maxima posición del pedido
                            max_pos = db.query(func.max(Paradas.posicion_en_pedido)).filter(
                                Paradas.id_pedido == parada.id_pedido
                            ).scalar()
                            destinos_de_pedidos[parada.id_pedido] = max_pos

                        # Le agregás el atributo dinámico
                        parada.es_destino = (parada.posicion_en_pedido == destinos_de_pedidos[parada.id_pedido])
                        visita.item = parada
                    else:
                        visita.item = db.query(LugaresComunes).filter(LugaresComunes.id == visita.id_item).first()
            processed_pedidos_no_atendidos = []
            if planificacion.pedidos_no_atendidos:
                for pna in planificacion.pedidos_no_atendidos:
                    pedido_obj = pna.pedido
                    if pedido_obj:
                        setattr(pedido_obj, 'no_enviado_al_optimizador', pna.no_enviado_al_optimizador)
                        processed_pedidos_no_atendidos.append(pedido_obj)
                planificacion_dict = {
                    **planificacion.__dict__,
                    "fmt_fecha": planificacion.fmt_fecha,
                    "fmt_fecha_creacion": planificacion.fmt_fecha_creacion,
                    "pedidos_no_atendidos": processed_pedidos_no_atendidos
                }
                return planificacion_dict
                
            # processed_pedidos_no_atendidos will be an empty list.
            planificacion.__dict__["fmt_fecha"] = planificacion.fmt_fecha
            planificacion.__dict__["fmt_fecha_creacion"] = planificacion.fmt_fecha_creacion
            planificacion.__dict__["pedidos_no_atendidos"] = processed_pedidos_no_atendidos
        return planificacion

# Internal helper function
def _get_planificaciones(db, filter_val, offset, limit, search=None, get_cantidad=False):
    query = db.query(Planificaciones)
    
    # Join necessary tables for search functionality
    query = query.join(Usuarios, Usuarios.id == Planificaciones.usuario_id)
    
    # If search parameter is provided, add search filters
    if search:
        search_term = f"%{search}%"
        search_filter = or_(
            Usuarios.nombre.ilike(search_term), 
            cast(Planificaciones.id, String).ilike(search_term), 
        )
        
        # Additional joins for searching related entities
        query = query.outerjoin(Rutas, Rutas.id_planificacion == Planificaciones.id)
        query = query.outerjoin(Vehiculos, Vehiculos.id == Rutas.id_vehiculo)
        query = query.outerjoin(Choferes, Choferes.id == Rutas.id_chofer)
        
        # Add more search conditions
        search_filter = or_(
            search_filter,
            Vehiculos.matricula.ilike(search_term),  # Vehicle registration
            Vehiculos.descripcion.ilike(search_term),  # Vehicle description
            Choferes.nombre.ilike(search_term),  # Driver name
            Choferes.apellido.ilike(search_term)  # Driver last name
        )
        
        # Apply the search filter
        filter_val = filter_val & search_filter
    
    # Create a base query with all necessary filters
    base_query = query.filter(filter_val)
    
    # Get count if needed - using the same query structure with distinct to avoid duplicates
    cantidad = None
    if get_cantidad:
        cantidad = base_query.with_entities(func.count(distinct(Planificaciones.id))).scalar()
    
    # Apply options and get results
    planificaciones = base_query.options(
        joinedload(Planificaciones.turnos),
        joinedload(Planificaciones.rutas)
            .load_only(Rutas.id, 
                       Rutas.hora_fin, 
                       Rutas.hora_inicio,
                       Rutas.descanso_inicio,
                       Rutas.descanso_fin
                       ) 
            .joinedload(Rutas.vehiculo),
        joinedload(Planificaciones.rutas)
            .joinedload(Rutas.chofer),
        joinedload(Planificaciones.rutas)
            .joinedload(Rutas.visitas)
            .joinedload(Visitas.parada)
            .joinedload(Paradas.tipo_parada),
        joinedload(Planificaciones.rutas)
            .joinedload(Rutas.visitas)
            .joinedload(Visitas.lugar_comun),
        joinedload(Planificaciones.creado_por)
            .load_only(Usuarios.nombre),
        joinedload(Planificaciones.pedidos_no_atendidos)
                .joinedload(PedidosNoAtendidos.pedido)
    ).offset(offset).limit(limit).all()

    for plan in planificaciones:
        plan.__dict__["fmt_fecha"] = plan.fmt_fecha
        plan.__dict__["fmt_fecha_creacion"] = plan.fmt_fecha_creacion

    if get_cantidad:
        return planificaciones, cantidad
    return planificaciones

def get_planificaciones_by_dia_db(fecha: str, limit: int = 100, offset: int = 0, search: str = ''):
    with get_db() as db:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        filter_val = Planificaciones.fecha == fecha_dt

        planificaciones, cantidad = _get_planificaciones(db, filter_val, offset, limit, search, get_cantidad=True)

        return planificaciones, cantidad

def get_planificaciones_by_rango_db(fecha_start: datetime, fecha_end: datetime, limit: int = 100, offset: int = 0, definitivas: bool = None):
    with get_db() as db:
        
        filter_val = Planificaciones.fecha.between(fecha_start, fecha_end)
        
        # Add filter for definitivas if specified
        if definitivas is not None:
            filter_val = filter_val & (Planificaciones.definitiva == definitivas)

        planificaciones, cantidad = _get_planificaciones(db, filter_val, offset, limit, get_cantidad=True)

        return planificaciones, cantidad

def validar_planificaciones_definitivas(fecha_start: datetime, fecha_end: datetime):
    """
    Valida que para cada día en el rango de fechas haya una única planificación definitiva.
    
    Returns:
        dict: Un diccionario con el resultado de la validación:
            - valid (bool): True si la validación es exitosa, False en caso contrario.
            - message (str): Mensaje descriptivo del resultado.
            - days_without_planification (list): Lista de fechas sin planificación (sólo informativo).
            - days_without_definitive (list): Lista de fechas sin planificación definitiva.
            - days_with_multiple_definitives (list): Lista de fechas con múltiples planificaciones definitivas.
    """
    with get_db() as db:
        result = {
            "valid": True,
            "message": "",
            "days_without_planification": [],
            "days_without_definitive": [],
            "days_with_multiple_definitives": []
        }
        
        current_date = fecha_start
        while current_date <= fecha_end:
            # Contar planificaciones definitivas para este día
            definitives_count = db.query(func.count(Planificaciones.id)).filter(
                Planificaciones.fecha == current_date,
                Planificaciones.definitiva == True
            ).scalar()
            
            # Verificar si hay planificaciones para este día
            has_any_planification = db.query(Planificaciones).filter(
                Planificaciones.fecha == current_date
            ).first() is not None
            
            if not has_any_planification:
                result["days_without_planification"].append(current_date.strftime('%Y-%m-%d'))
            elif definitives_count == 0:
                result["days_without_definitive"].append(current_date.strftime('%Y-%m-%d'))
                result["valid"] = False
            elif definitives_count > 1:
                result["days_with_multiple_definitives"].append(current_date.strftime('%Y-%m-%d'))
                result["valid"] = False
                
            current_date += timedelta(days=1)
        
        # Construir mensaje de error si es necesario
        if not result["valid"]:
            result["message"] = '''No se pudo validar la planificación definitiva. Para generar un informe, es necesario identificar claramente cuál fue la planificación realizada en cada uno de los días seleccionados.

                Esto implica que debes marcar una única planificación como *definitiva* para cada día en que exista más de una opción.

                Por favor, revisa el listado y corrige las siguientes situaciones: \n
                '''
            error_msg = []
            if result["days_without_definitive"]:
                error_msg.append(f"- Días sin planificación definitiva seleccionada: {', '.join(result['days_without_definitive'])}")
            if result["days_with_multiple_definitives"]:
                error_msg.append(f"- Días con múltiples planificaciones marcadas como definitivas: {', '.join(result['days_with_multiple_definitives'])}")
            result["message"] += "\n".join(error_msg)
            raise HTTPException(status_code=400, detail=result["message"])

        return True
        

def update_planificacion_db(id_planificacion, planificacion):
    with get_db() as db:
        db.query(Planificaciones).filter(Planificaciones.id_planificacion == id_planificacion).update(planificacion.dict())
        db.commit()
        return planificacion

def update_planificacion_estado_db(id_planificacion, activo):
    with get_db() as db:
        activo_bool = activo.lower() in ['true', '1', 't', 'y', 'yes']
        db.query(Planificaciones).filter(Planificaciones.id == id_planificacion).update({"definitiva": activo_bool})
        db.commit()
    
def delete_planificacion_db(id_planificacion):
    with get_db() as db:
        # Delete related Visitas
        db.query(Visitas).filter(
            Visitas.id_ruta.in_(
                db.query(Rutas.id).filter(Rutas.id_planificacion == id_planificacion)
            )
        ).delete(synchronize_session=False)

        # Delete related Rutas
        db.query(Rutas).filter(Rutas.id_planificacion == id_planificacion).delete(synchronize_session=False)

        # Delete related Turnos
        db.query(Turnos).filter(Turnos.id_planificacion == id_planificacion).delete(synchronize_session=False)

        db.query(PedidosNoAtendidos).filter(PedidosNoAtendidos.id_planificacion == id_planificacion).delete(synchronize_session=False)

        # Delete the Planificacion
        db.query(Planificaciones).filter(Planificaciones.id == id_planificacion).delete(synchronize_session=False)

        db.commit()
        return {"message": f"Planificación con ID {id_planificacion} y sus dependencias eliminadas correctamente."}
    
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
    id_planificacion = Column(Integer, ForeignKey('planificaciones.id'), nullable=False)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id'), nullable=False)
    id_chofer = Column(Integer, ForeignKey('choferes.id'), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    geometria = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    observaciones = Column(String)
    descanso_inicio = Column(Time, nullable=True) # Added
    descanso_fin = Column(Time, nullable=True)    # Added
    planificacion = relationship('Planificaciones', back_populates='rutas')
    vehiculo = relationship('Vehiculos')
    chofer = relationship('Choferes')
    visitas = relationship('Visitas', back_populates='ruta', order_by='Visitas.hora_llegada')

def add_ruta_db(ruta):
    with get_db() as db:
        geometria_wkt = WKTElement(LineString(ruta.geometria).wkt, srid=4326)
        ruta_obj = Rutas(
            id_planificacion=ruta.id_planificacion,
            id_vehiculo=ruta.id_vehiculo,
            id_chofer=ruta.id_chofer,
            hora_inicio=ruta.hora_inicio,
            hora_fin=ruta.hora_fin,
            geometria=geometria_wkt,  
            observaciones=ruta.observaciones,
            descanso_inicio=getattr(ruta, 'descanso_inicio', None),
            descanso_fin=getattr(ruta, 'descanso_fin', None)
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

# region Visitas

class Visitas(Base):
    __tablename__ = 'visitas'

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey('rutas.id'))
    id_item = Column(Integer, nullable=False)
    tipo_item = Column(SQLAEnum(m.TipoItemVisita), nullable=False)
    estado = Column(SQLAEnum(m.EstadoVisita), nullable=False)
    hora_llegada = Column(Time, nullable=False)
    hora_salida = Column(Time, nullable=False)
    observaciones = Column(String)
    ruta = relationship('Rutas', back_populates='visitas')
    parada = relationship('Paradas', foreign_keys=[id_item], primaryjoin="and_(Visitas.id_item == Paradas.id, Visitas.tipo_item == 'Parada')")
    lugar_comun = relationship('LugaresComunes', foreign_keys=[id_item], primaryjoin="and_(Visitas.id_item == LugaresComunes.id, Visitas.tipo_item == 'lugar_comun')")

    
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
