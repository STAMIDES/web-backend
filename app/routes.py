from fastapi import APIRouter, HTTPException # type: ignore
from models import (Pedidos, Clientes, ClientesCreate, ClientesCaracteristicas, Vehiculos, LugaresComunes, Choferes, 
                    VehiculosCaracteristicas, Planificaciones, Turnos, Rutas, Visitas, Usuarios, UsuarioCreate)
import database as db
import autenticacion as aut
from datetime import datetime
import logging
# region Usuarios
usuarios_router = APIRouter()

@usuarios_router.get("/{documento}")
def get_usuario(documento: int):
    try:
        usuario = db.get_usuario_db(documento)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.post("/")
def add_usuario(usuario: UsuarioCreate):
    try:
        db.add_usuario_db(usuario)
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.put("/{documento}")
def update_usuario(documento: int, usuario: Usuarios):
    try:
        db.update_usuario_db(documento, usuario)
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.delete("/{documento}")
def delete_usuario(documento: int):
    try:
        db.delete_usuario_db(documento)
        return {"message": f"Usuario con documento {documento} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/login")
def login(request_body: dict):
    username: str = str(request_body.get("username"))
    password: str = str(request_body.get("password"))
    token = db.login(username, password)
    if token:
        return {"token": token}
    else:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    

@usuarios_router.post("/logout")
def logout(usuario: Usuarios):
    try:
        db.logout(usuario)
        return {"message": "Usuario desconectado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.get("/validate/{token}")
def validate(token: str):
    try:
        payload = aut.validate_token(token)
        return {"payload": payload}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")

# endregion

# region Clientes
clientes_router = APIRouter()

@clientes_router.get("/{documento}")
def get_cliente(documento: int):
    try:
        cliente = db.get_cliente_db(documento)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
        return {"cliente": cliente}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.get("/{documento}")
def get_cliente_completo(documento: int):
    try:
        cliente = db.get_cliente_completo_db(documento)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
        return {"cliente": cliente}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/")
def get_clientes():
    try:
        clientes = db.get_clientes_db()
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/{documento}")
def get_clientes_documento(documento: int):
    try:
        clientes = db.get_clientes_by_documento_db(documento)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/nombre/{nombre}")
def get_clientes_nombre(nombre: str):
    try:
        clientes = db.get_clientes_by_nombre_db(nombre)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("tipo/{tipo}")
def get_clientes_tipo(tipo: str):
    try:
        clientes = db.get_clientes_by_tipo_db(tipo)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.get("/caracteristica/{caracteristica}")
def get_clientes_caracteristica(caracteristica: str):
    try:
        clientes = db.get_clientes_by_caracteristica_db(caracteristica)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.post("/")
def add_cliente(cliente: ClientesCreate):
    try:
        db.add_cliente_db(cliente)
        return {"cliente": cliente}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.put("/{documento}")
def update_cliente(documento: int, cliente: Clientes):
    try:
        db.update_cliente_db(documento, cliente)
        return {"cliente": cliente}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.delete("/{documento}")
def delete_cliente(documento: int):
    try:
        db.delete_cliente_db(documento)
        return {"message": f"Cliente con documento {documento} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region ClientesCaracteristicas
clientes_caracteristicas_router = APIRouter()

@clientes_caracteristicas_router.post("/")
def add_cliente_caracteristica(persona_caracteristica: ClientesCaracteristicas):
    try:
        db.add_cliente_caracteristica(persona_caracteristica)
        return {"persona_caracteristica": persona_caracteristica}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_caracteristicas_router.get("/{documento}")
def get_cliente_caracteristica(documento: int):
    persona_caracteristica = db.get_cliente_caracteristica(documento)
    if persona_caracteristica:
        return {"persona_caracteristica": persona_caracteristica}
    raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")

@clientes_caracteristicas_router.put("/{documento}")
def update_cliente_caracteristica(documento: int, caracteristica: str):
    try:
        updated = db.update_cliente_caracteristica(documento, caracteristica)
        if updated:
            return {"message": f"Característica actualizada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_caracteristicas_router.delete("/{documento}")
def delete_cliente_caracteristica(documento: int):
    try:
        deleted = db.delete_cliente_caracteristica(documento)
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

@pedidos_router.get("/")
def get_pedidos():
    try:
        pedidos = db.get_pedidos_db()
        return {"pedidos": pedidos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# obtener pedidos por fecha
@pedidos_router.get("/fecha/{fecha}")
def get_pedidos_fecha(fecha: str):
    try:
        fechaD = datetime.strptime(fecha, "%Y-%m-%d")
        pedidosdb = db.get_pedidos_by_fecha_db(fechaD)
        list_ret = []
        for p in pedidosdb:
            dic_ret=p[0].__dict__
            dic_ret['cliente_nombre'] = p.nombre
            dic_ret['cliente_apellido'] = p.apellido
            list_ret.append(dic_ret)
        return {"pedidos": list_ret}
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
    
def get_planificaciones_fecha(fecha):
    try:
        planificaciones = db.get_planificaciones_by_fecha_db(fecha)
        return {"planificaciones": planificaciones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.post("/")
def add_planificacion(planificacion: Planificaciones):
    try:
        db.crear_planificacion(planificacion)
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

# region Visitas
visitas_router = APIRouter()

@visitas_router.get("/{id_visita}")
def get_visita(id_visita: int):
    try:
        visita = db.get_visita_db(id_visita)
        if not visita:
            raise HTTPException(status_code=404, detail="Visita no encontrada.")
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.post("/")
def add_visita(visita: Visitas):
    try:
        db.add_visita_db(visita)
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.put("/{id_visita}")
def update_visita(id_visita: int, visita: Visitas):
    try:
        db.update_visita_db(id_visita, visita)
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.delete("/{id_visita}")
def delete_visita(id_visita: int):
    try:
        db.delete_visita_db(id_visita)
        return {"message": f"Visita con ID {id_visita} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion