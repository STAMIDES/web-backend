from fastapi import APIRouter, HTTPException # type: ignore
from app.models import Pedidos, Personas, PersonasCaracteristicas, Vehiculos, LugaresComunes, Choferes, VehiculosCaracteristicas, Planificaciones, Turnos, Rutas
import app.database as db

# region Personas
personas_router = APIRouter()
@personas_router.get("/{documento}")
def get_persona(documento: int):
    try:
        persona = db.get_persona_db(documento)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona no encontrada.")
        return {"persona": persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@personas_router.post("/")
def add_persona(persona: Personas):
    try:
        db.add_persona_db(persona)
        return {"persona": persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@personas_router.put("/{documento}")
def update_persona(documento: int, persona: Personas):
    try:
        db.update_persona_db(documento, persona)
        return {"persona": persona}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@personas_router.delete("/{documento}")
def delete_persona(documento: int):
    try:
        db.delete_persona_db(documento)
        return {"message": f"Persona con documento {documento} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region PersonasCaracteristicas
personas_caracteristicas_router = APIRouter()

@personas_caracteristicas_router.post("/")
def add_persona_caracteristica(persona_caracteristica: PersonasCaracteristicas):
    try:
        db.add_persona_caracteristica(persona_caracteristica)
        return {"persona_caracteristica": persona_caracteristica}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@personas_caracteristicas_router.get("/{documento}")
def get_persona_caracteristica(documento: int):
    persona_caracteristica = db.get_persona_caracteristica(documento)
    if persona_caracteristica:
        return {"persona_caracteristica": persona_caracteristica}
    raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")

@personas_caracteristicas_router.put("/{documento}")
def update_persona_caracteristica(documento: int, caracteristica: str):
    try:
        updated = db.update_persona_caracteristica(documento, caracteristica)
        if updated:
            return {"message": f"Característica actualizada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@personas_caracteristicas_router.delete("/{documento}")
def delete_persona_caracteristica(documento: int):
    try:
        deleted = db.delete_persona_caracteristica(documento)
        if deleted:
            return {"message": f"Característica eliminada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Pedidos
pedidos_router = APIRouter()

@pedidos_router.get("/{id_pedido}")
def get_pedido(id_pedido: int):
    try:
        pedido = db.get_pedido_db(id_pedido)
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.post("/")
def add_pedido(pedido: Pedidos):
    try:
        db.add_pedido_db(pedido)
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.put("/{id_pedido}")
def update_pedido(id_pedido: int, pedido: Pedidos):
    try:
        db.update_pedido_db(id_pedido, pedido)
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.delete("/{id_pedido}")
def delete_pedido(id_pedido: int):
    try:
        db.delete_pedido_db(id_pedido)
        return {"message": f"Pedido con ID {id_pedido} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Vehiculos
vehiculos_router = APIRouter()

@vehiculos_router.get("/{id_vehiculo}")
def get_vehiculo(id_vehiculo: int):
    try:
        vehiculo = db.get_vehiculo_db(id_vehiculo)
        if not vehiculo:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.post("/")
def add_vehiculo(vehiculo: Vehiculos):
    try:
        db.add_vehiculo_db(vehiculo)
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.put("/{id_vehiculo}")
def update_vehiculo(id_vehiculo: int, vehiculo: Vehiculos):
    try:
        db.update_vehiculo_db(id_vehiculo, vehiculo)
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.delete("/{id_vehiculo}")
def delete_vehiculo(id_vehiculo: int):
    try:
        db.delete_vehiculo_db(id_vehiculo)
        return {"message": f"Vehículo con ID {id_vehiculo} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region VehiculosCaracteristicas
vehiculos_caracteristicas_router = APIRouter()

@vehiculos_caracteristicas_router.post("/")
def add_vehiculo_caracteristica(vehiculo_caracteristica: VehiculosCaracteristicas):
    try:
        db.add_vehiculo_caracteristica(vehiculo_caracteristica)
        return {"vehiculo_caracteristica": vehiculo_caracteristica}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_caracteristicas_router.get("/{id_vehiculo}")
def get_vehiculo_caracteristica(id_vehiculo: int):
    vehiculo_caracteristica = db.get_vehiculo_caracteristica(id_vehiculo)
    if vehiculo_caracteristica:
        return {"vehiculo_caracteristica": vehiculo_caracteristica}
    raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")

@vehiculos_caracteristicas_router.put("/{id_vehiculo}")
def update_vehiculo_caracteristica(id_vehiculo: int, caracteristica: str):
    try:
        updated = db.update_vehiculo_caracteristica(id_vehiculo, caracteristica)
        if updated:
            return {"message": f"Característica actualizada correctamente para el vehículo con ID {id_vehiculo}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_caracteristicas_router.delete("/{id_vehiculo}")
def delete_vehiculo_caracteristica(id_vehiculo: int):
    try:
        deleted = db.delete_vehiculo_caracteristica(id_vehiculo)
        if deleted:
            return {"message": f"Característica eliminada correctamente para el vehículo con ID {id_vehiculo}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Choferes
choferes_router = APIRouter()

@choferes_router.get("/{documento}")
def get_chofer(documento: int):
    try:
        chofer = db.get_chofer_db(documento)
        if not chofer:
            raise HTTPException(status_code=404, detail="Chofer no encontrado.")
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.post("/")
def add_chofer(chofer: Choferes):
    try:
        db.add_chofer_db(chofer)
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.put("/{documento}")
def update_chofer(documento: int, chofer: Choferes):
    try:
        db.update_chofer_db(documento, chofer)
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.delete("/{documento}")
def delete_chofer(documento: int):
    try:
        db.delete_chofer_db(documento)
        return {"message": f"Chofer con documento {documento} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region LugaresComunes
lugares_comunes_router = APIRouter()

@lugares_comunes_router.get("/{id_lugar}")
def get_lugar_comun(id_lugar: int):
    try:
        lugar = db.get_lugar_comun_db(id_lugar)
        if not lugar:
            raise HTTPException(status_code=404, detail="Lugar común no encontrado.")
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.post("/")
def add_lugar_comun(lugar: LugaresComunes):
    try:
        db.add_lugar_comun_db(lugar)
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.put("/{id_lugar}")
def update_lugar_comun(id_lugar: int, lugar: LugaresComunes):
    try:
        db.update_lugar_comun_db(id_lugar, lugar)
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.delete("/{id_lugar}")
def delete_lugar_comun(id_lugar: int):
    try:
        db.delete_lugar_comun_db(id_lugar)
        return {"message": f"Lugar común con ID {id_lugar} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Planificaciones
planificaciones_router = APIRouter()

@planificaciones_router.get("/{id_planificacion}")
def get_planificacion(id_planificacion: int):
    try:
        planificacion = db.get_planificacion_db(id_planificacion)
        if not planificacion:
            raise HTTPException(status_code=404, detail="Planificación no encontrada.")
        return {"planificacion": planificacion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.post("/")
def add_planificacion(planificacion: Planificaciones):
    try:
        db.add_planificacion_db(planificacion)
        return {"planificacion": planificacion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.put("/{id_planificacion}")
def update_planificacion(id_planificacion: int, planificacion: Planificaciones):
    try:
        db.update_planificacion_db(id_planificacion, planificacion)
        return {"planificacion": planificacion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.delete("/{id_planificacion}")
def delete_planificacion(id_planificacion: int):
    try:
        db.delete_planificacion_db(id_planificacion)
        return {"message": f"Planificación con ID {id_planificacion} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Turnos
turnos_router = APIRouter()

@turnos_router.get("/{id_turno}")
def get_turno(id_turno: int):
    try:
        turno = db.get_turno_db(id_turno)
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado.")
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.post("/")
def add_turno(turno: Turnos):
    try:
        db.add_turno_db(turno)
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.put("/{id_turno}")
def update_turno(id_turno: int, turno: Turnos):
    try:
        db.update_turno_db(id_turno, turno)
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.delete("/{id_turno}")
def delete_turno(id_turno: int):
    try:
        db.delete_turno_db(id_turno)
        return {"message": f"Turno con ID {id_turno} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Rutas
rutas_router = APIRouter()

@rutas_router.get("/{id_ruta}")
def get_ruta(id_ruta: int):
    try:
        ruta = db.get_ruta_db(id_ruta)
        if not ruta:
            raise HTTPException(status_code=404, detail="Ruta no encontrada.")
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.post("/")
def add_ruta(ruta: Rutas):
    try:
        db.add_ruta_db(ruta)
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.put("/{id_ruta}")
def update_ruta(id_ruta: int, ruta: Rutas):
    try:
        db.update_ruta_db(id_ruta, ruta)
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.delete("/{id_ruta}")
def delete_ruta(id_ruta: int):
    try:
        db.delete_ruta_db(id_ruta)
        return {"message": f"Ruta con ID {id_ruta} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion