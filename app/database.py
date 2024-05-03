from sqlalchemy import create_engine, Column, ForeignKey,Integer, String, Float, DateTime, Boolean # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from geoalchemy2 import Geometry # type: ignore

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

# region Personas

class Personas(Base):
    __tablename__ = 'personas'

    id_persona = Column(Integer, primary_key=True, index=True)
    documento = Column(Integer, unique=True)
    nombre = Column(String)
    apellido = Column(String)
    telefono = Column(Integer)
    observaciones = Column(String)
    tipo_persona = Column(String)

def add_persona_db(persona):
    with get_db() as db:
        persona_obj = Personas(**persona.dict())
        db.add(persona_obj)
        db.commit()
        db.refresh(persona_obj)
        return persona_obj

def get_persona_db(documento):
    with get_db() as db:
        return db.query(Personas).filter(Personas.documento == documento).first()

def update_persona_db(documento, persona):
    with get_db() as db:
        db.query(Personas).filter(Personas.documento == documento).update(persona.dict())
        db.commit()
        return persona

def delete_persona_db(documento):
    with get_db() as db:
        db.query(Personas).filter(Personas.documento == documento).delete()
        db.commit()
        return {"message": f"Persona con documento {documento} eliminada correctamente."}

# endregion

# region PersonasCaracteristicas

class PersonasCaracteristicas(Base):
    __tablename__ = 'personas_caracteristicas'

    id = Column(Integer, primary_key=True, index=True)
    id_persona = Column(Integer, ForeignKey('personas.id_persona'))
    caracteristica = Column(String)

def add_persona_caracteristica(persona_caracteristica):
    with SessionLocal() as db:
        persona_caracteristica_obj = PersonasCaracteristicas(**persona_caracteristica.dict())
        db.add(persona_caracteristica_obj)
        db.commit()
        db.refresh(persona_caracteristica_obj)
        return persona_caracteristica_obj

def get_persona_caracteristica(documento: int):
    with SessionLocal() as db:
        persona_caracteristica = db.query(PersonasCaracteristicas).filter(PersonasCaracteristicas.documento == documento).first()
        return persona_caracteristica

def update_persona_caracteristica(documento: int, caracteristica: str):
    with SessionLocal() as db:
        persona_caracteristica = db.query(PersonasCaracteristicas).filter(PersonasCaracteristicas.documento == documento).first()
        if persona_caracteristica:
            persona_caracteristica.caracteristica = caracteristica
            db.commit()
            db.refresh(persona_caracteristica)
            return True
        return False

def delete_persona_caracteristica(documento: int):
    with SessionLocal() as db:
        persona_caracteristica = db.query(PersonasCaracteristicas).filter(PersonasCaracteristicas.documento == documento).first()
        if persona_caracteristica:
            db.delete(persona_caracteristica)
            db.commit()
            return True
        return False

# endregion

# region Pedidos

class Pedidos(Base):
    __tablename__ = 'pedidos'

    id_pedido = Column(Integer, primary_key=True, index=True)
    usuario_documento = Column(Integer, ForeignKey('personas.documento'))  # Referencia a la tabla personas
    direccion_origen = Column(String)
    direccion_destino = Column(String)
    latitud_origen = Column(Float)
    latitud_destino = Column(Float)
    longitud_origen = Column(Float)
    longitud_destino = Column(Float)
    ventana_origen_inicio = Column(DateTime)
    ventana_origen_fin = Column(DateTime)
    ventana_destino_inicio = Column(DateTime)
    ventana_destino_fin = Column(DateTime)
    hora_ingresado = Column(DateTime)
    prioridad = Column(Integer)
    acompañante = Column(Boolean)
    observaciones = Column(String)

def add_pedido_db(pedido):
    with get_db() as db:
        pedido_obj = Pedidos(**pedido.dict())
        db.add(pedido_obj)
        db.commit()
        db.refresh(pedido_obj)
        return pedido_obj

def get_pedido_db(id_pedido):
    with get_db() as db:
        return db.query(Pedidos).filter(Pedidos.id_pedido == id_pedido).first()

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

# region Vehiculos
class Vehiculos(Base):
    __tablename__ = 'vehiculos'

    id_vehiculo = Column(Integer, primary_key=True, index=True)
    matricula = Column(String, unique=True)
    descripcion = Column(String)
    documento_chofer = Column(Integer, ForeignKey('choferes.documento'))
    capacidad_convencional = Column(Integer)
    capacidad_silla_de_ruedas = Column(Integer)
    disponibilidad = Column(Boolean)
    observaciones = Column(String)

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
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id_vehiculo'))
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

    id_chofer = Column(Integer, primary_key=True, index=True)
    documento = Column(Integer, unique=True)
    nombre = Column(String)
    apellido = Column(String)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id_vehiculo'))
    telefono = Column(Integer)
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

    id_lugar_comun = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    direccion = Column(String)
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

    id_planificacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    fecha = Column(DateTime)
    fechaCreacion = Column(DateTime)
    observaciones = Column(String)

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

    id_turno = Column(Integer, primary_key=True, index=True)
    id_planificacion = Column(Integer, ForeignKey('planificaciones.id_planificacion'))
    descripcion = Column(String)
    hora_inicio = Column(DateTime)
    hora_fin = Column(DateTime)

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

    id_ruta = Column(Integer, primary_key=True, index=True)
    id_turno = Column(Integer, ForeignKey('turnos.id_turno'))
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id_vehiculo'))
    id_chofer = Column(Integer, ForeignKey('choferes.id_chofer'))
    hora_salida = Column(DateTime)
    hora_llegada = Column(DateTime)
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