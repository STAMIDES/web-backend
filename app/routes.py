from fastapi import APIRouter, HTTPException, Body, Depends # type: ignore
from models import (Pedidos, Clientes, ClientesCaracteristicas, Vehiculos, LugaresComunes, Choferes, 
                    VehiculosCaracteristicas, Planificaciones, Turnos, Rutas, Visitas, Usuarios, LoginRequest, InvitacionUsuario, RegistroUsuario)
import database as db
import autenticacion.autenticacion as aut
from autenticacion.autenticacion_bearer import JWTBearer
from datetime import datetime
import logging
from utils import Mailer

log = logging.getLogger(__name__)
# region Usuarios
usuarios_router = APIRouter()

@usuarios_router.get("/", dependencies=[Depends(JWTBearer())])
def get_usuarios(skip: int = 0, limit: int = 10):
    try:
        usuarios, total = db.get_usuarios(skip=skip, limit=limit)
        return {"usuarios": usuarios, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.get("/{email}", dependencies=[Depends(JWTBearer())])
def get_usuario(email: int):
    try:
        usuario = db.get_usuario_db(email)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/") # FIXME delete this endpoint and create users by invitations// this is for testing purposes
def add_usuario(usuario: Usuarios):
    try:
        usuario = db.add_usuario_db(usuario)
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/invitar", dependencies=[Depends(JWTBearer())])
def invite_usuario(usuarioInv: InvitacionUsuario):
    try:
        if not db.user_exists(usuarioInv.email):
            # Enviar correo
            hash_link = db.generate_invitation(usuarioInv)
            if not hash_link:
                raise HTTPException(status_code=400, detail='Error al generar la invitación')
            mailer = Mailer()
            subject = db.INVITATION_SUBJECT_TEMPLATE
            body = db.INVITATION_BODY_TEMPLATE.format(nombre_usuario=usuarioInv.nombre, hash_link=hash_link)
            mailer.send(usuarioInv.email, subject, body)
            return {'detail': usuarioInv.nombre + ' ha sido invitado correctamente'}
        else:
            raise HTTPException(status_code=400, detail='El usuario ya existe')
    except HTTPException as e:
        raise e
        
@usuarios_router.get("/registro/{hash_link}")
def add_usuario(hash_link: str):
    try:
        usuarioInv = db.get_invitation(hash_link)
        if not usuarioInv:
            raise HTTPException(status_code=400, detail='Invitación no existente o ya usada')
        return usuarioInv
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/registro/{hash_link}")
def add_usuario(hash_link: str, nuevo_user: RegistroUsuario):
    try:
        usuarioInv = db.get_invitation(hash_link)
        if not usuarioInv:
            raise HTTPException(status_code=400, detail='Invitación no existente o ya usada')
        log.info(nuevo_user)
        if len(nuevo_user.password) < 7:
            raise HTTPException(status_code=400, detail='La contraseña debe tener al menos 7 caracteres')
        db.registrar_usuario(usuarioInv, nuevo_user)
        return usuarioInv
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.put("/{email}", dependencies=[Depends(JWTBearer())])
def update_usuario(email: int, usuario: Usuarios):
    try:
        db.update_usuario_db(email, usuario)
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.delete("/{email}", dependencies=[Depends(JWTBearer())])
def delete_usuario(email: int):
    try:
        db.delete_usuario_db(email)
        return {"detail": f"Usuario {email} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/login")
def login(request: LoginRequest):
    try:
        token = db.login(request.username, request.password)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=e.args[0] if e.args else "Usuario o contraseña incorrectos")
    
@usuarios_router.post("/logout", dependencies=[Depends(JWTBearer())])
def logout(email: str):
    try:
        db.logout(email)
        return {"detail": "Usuario desconectado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Clientes
clientes_router = APIRouter()

@clientes_router.get("/{id}", dependencies=[Depends(JWTBearer())])
def get_cliente_completo(id: int, completo = False):
    try:
        cliente = db.get_cliente(id)
        if not cliente:
            raise HTTPException(status_code=400, detail="Cliente no encontrado.")
        if not completo:
            return {"cliente": cliente}
        pedidos = db.get_pedidos_cliente(cliente.documento)
        return {"cliente": cliente, "pedidos": pedidos}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/", dependencies=[Depends(JWTBearer())])
def get_clientes():
    try:
        clientes = db.get_clientes_db()
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/doc/{documento}", dependencies=[Depends(JWTBearer())])
def get_clientes_documento(documento: int):
    try:
        clientes = db.get_clientes_by_documento_db(documento)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/nombre/{nombre}", dependencies=[Depends(JWTBearer())])
def get_clientes_nombre(nombre: str):
    try:
        clientes = db.get_clientes_by_nombre_db(nombre)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("tipo/{tipo}", dependencies=[Depends(JWTBearer())])
def get_clientes_tipo(tipo: str):
    try:
        clientes = db.get_clientes_by_tipo_db(tipo)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.get("/caracteristica/{caracteristica}", dependencies=[Depends(JWTBearer())])
def get_clientes_caracteristica(caracteristica: str):
    try:
        clientes = db.get_clientes_by_caracteristica_db(caracteristica)
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_cliente(cliente: Clientes):
    try:
        if not db.get_cliente(cliente.documento):
            db.add_cliente_db(cliente)
            return {"cliente": cliente}
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese documento.")
    except HTTPException as e:
        raise e
    except Exception as e:
       print(e)
       raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.put("/{documento}", dependencies=[Depends(JWTBearer())])
def update_cliente(documento: int, cliente: Clientes):
    try:
        db.update_cliente_db(documento, cliente)
        return {"cliente": cliente}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.delete("/{documento}", dependencies=[Depends(JWTBearer())])
def delete_cliente(documento: int):
    try:
        db.delete_cliente_db(documento)
        return {"detail": f"Cliente con documento {documento} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region ClientesCaracteristicas
clientes_caracteristicas_router = APIRouter()

@clientes_caracteristicas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_cliente_caracteristica(persona_caracteristica: ClientesCaracteristicas):
    try:
        db.add_cliente_caracteristica(persona_caracteristica)
        return {"persona_caracteristica": persona_caracteristica}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_caracteristicas_router.get("/{documento}", dependencies=[Depends(JWTBearer())])
def get_cliente_caracteristica(documento: int):
    persona_caracteristica = db.get_cliente_caracteristica(documento)
    if persona_caracteristica:
        return {"persona_caracteristica": persona_caracteristica}
    raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")

@clientes_caracteristicas_router.put("/{documento}", dependencies=[Depends(JWTBearer())])
def update_cliente_caracteristica(documento: int, caracteristica: str):
    try:
        updated = db.update_cliente_caracteristica(documento, caracteristica)
        if updated:
            return {"detail": f"Característica actualizada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_caracteristicas_router.delete("/{documento}", dependencies=[Depends(JWTBearer())])
def delete_cliente_caracteristica(documento: int):
    try:
        deleted = db.delete_cliente_caracteristica(documento)
        if deleted:
            return {"detail": f"Característica eliminada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Pedidos
pedidos_router = APIRouter()

@pedidos_router.get("/{id_pedido}", dependencies=[Depends(JWTBearer())])
def get_pedido(id_pedido: int):
    try:
        pedido = db.get_pedido_db(id_pedido)
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado.")
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.get("/", dependencies=[Depends(JWTBearer())])
def get_pedidos():
    try:
        pedidos = db.get_pedidos_db()
        return {"pedidos": pedidos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# Obtener pedidos por fecha
@pedidos_router.get("/fecha/{fecha}", dependencies=[Depends(JWTBearer())])
def get_pedidos_fecha(fecha: str):
        pedidos = db.get_pedidos_by_fecha_db(fecha)
        return {"pedidos": pedidos}
    
@pedidos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_pedido(pedido: Pedidos):
    try:
        db.add_pedido_db(pedido)
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.put("/{id_pedido}", dependencies=[Depends(JWTBearer())])
def update_pedido(id_pedido: int, pedido: Pedidos):
    try:
        db.update_pedido_db(id_pedido, pedido)
        return {"pedido": pedido}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.delete("/{id_pedido}", dependencies=[Depends(JWTBearer())])
def delete_pedido(id_pedido: int):
    try:
        db.delete_pedido_db(id_pedido)
        return {"detail": f"Pedido con ID {id_pedido} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Vehiculos
vehiculos_router = APIRouter()

@vehiculos_router.get("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def get_vehiculo(id_vehiculo: int):
    try:
        vehiculo = db.get_vehiculo_db(id_vehiculo)
        if not vehiculo:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_vehiculo(vehiculo: Vehiculos):
    try:
        db.add_vehiculo_db(vehiculo)
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.put("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def update_vehiculo(id_vehiculo: int, vehiculo: Vehiculos):
    try:
        db.update_vehiculo_db(id_vehiculo, vehiculo)
        return {"vehiculo": vehiculo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.delete("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def delete_vehiculo(id_vehiculo: int):
    try:
        db.delete_vehiculo_db(id_vehiculo)
        return {"detail": f"Vehículo con ID {id_vehiculo} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region VehiculosCaracteristicas
vehiculos_caracteristicas_router = APIRouter()

@vehiculos_caracteristicas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_vehiculo_caracteristica(vehiculo_caracteristica: VehiculosCaracteristicas):
    try:
        db.add_vehiculo_caracteristica(vehiculo_caracteristica)
        return {"vehiculo_caracteristica": vehiculo_caracteristica}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_caracteristicas_router.get("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def get_vehiculo_caracteristica(id_vehiculo: int):
    vehiculo_caracteristica = db.get_vehiculo_caracteristica(id_vehiculo)
    if vehiculo_caracteristica:
        return {"vehiculo_caracteristica": vehiculo_caracteristica}
    raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")

@vehiculos_caracteristicas_router.put("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def update_vehiculo_caracteristica(id_vehiculo: int, caracteristica: str):
    try:
        updated = db.update_vehiculo_caracteristica(id_vehiculo, caracteristica)
        if updated:
            return {"detail": f"Característica actualizada correctamente para el vehículo con ID {id_vehiculo}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_caracteristicas_router.delete("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def delete_vehiculo_caracteristica(id_vehiculo: int):
    try:
        deleted = db.delete_vehiculo_caracteristica(id_vehiculo)
        if deleted:
            return {"detail": f"Característica eliminada correctamente para el vehículo con ID {id_vehiculo}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Choferes
choferes_router = APIRouter()

@choferes_router.get("/{documento}", dependencies=[Depends(JWTBearer())])
def get_chofer(documento: int):
    try:
        chofer = db.get_chofer_db(documento)
        if not chofer:
            raise HTTPException(status_code=404, detail="Chofer no encontrado.")
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_chofer(chofer: Choferes):
    try:
        db.add_chofer_db(chofer)
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.put("/{documento}", dependencies=[Depends(JWTBearer())])
def update_chofer(documento: int, chofer: Choferes):
    try:
        db.update_chofer_db(documento, chofer)
        return {"chofer": chofer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.delete("/{documento}", dependencies=[Depends(JWTBearer())])
def delete_chofer(documento: int):
    try:
        db.delete_chofer_db(documento)
        return {"detail": f"Chofer con documento {documento} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region LugaresComunes
lugares_comunes_router = APIRouter()

@lugares_comunes_router.get("/{id_lugar}", dependencies=[Depends(JWTBearer())])
def get_lugar_comun(id_lugar: int):
    try:
        lugar = db.get_lugar_comun_db(id_lugar)
        if not lugar:
            raise HTTPException(status_code=404, detail="Lugar común no encontrado.")
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_lugar_comun(lugar: LugaresComunes):
    try:
        db.add_lugar_comun_db(lugar)
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.put("/{id_lugar}", dependencies=[Depends(JWTBearer())])
def update_lugar_comun(id_lugar: int, lugar: LugaresComunes):
    try:
        db.update_lugar_comun_db(id_lugar, lugar)
        return {"lugar": lugar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.delete("/{id_lugar}", dependencies=[Depends(JWTBearer())])
def delete_lugar_comun(id_lugar: int):
    try:
        db.delete_lugar_comun_db(id_lugar)
        return {"detail": f"Lugar común con ID {id_lugar} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Planificaciones
planificaciones_router = APIRouter()

@planificaciones_router.get("/{id_planificacion}", dependencies=[Depends(JWTBearer())])
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
    
@planificaciones_router.post("/", dependencies=[Depends(JWTBearer())])
def add_planificacion(planificacion: Planificaciones):
    try:
        db.crear_planificacion(planificacion)
        return {"planificacion": planificacion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.put("/{id_planificacion}", dependencies=[Depends(JWTBearer())])
def update_planificacion(id_planificacion: int, planificacion: Planificaciones):
    try:
        db.update_planificacion_db(id_planificacion, planificacion)
        return {"planificacion": planificacion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.delete("/{id_planificacion}", dependencies=[Depends(JWTBearer())])
def delete_planificacion(id_planificacion: int):
    try:
        db.delete_planificacion_db(id_planificacion)
        return {"detail": f"Planificación con ID {id_planificacion} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Turnos
turnos_router = APIRouter()

@turnos_router.get("/{id_turno}", dependencies=[Depends(JWTBearer())])
def get_turno(id_turno: int):
    try:
        turno = db.get_turno_db(id_turno)
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado.")
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_turno(turno: Turnos):
    try:
        db.add_turno_db(turno)
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.put("/{id_turno}", dependencies=[Depends(JWTBearer())])
def update_turno(id_turno: int, turno: Turnos):
    try:
        db.update_turno_db(id_turno, turno)
        return {"turno": turno}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.delete("/{id_turno}", dependencies=[Depends(JWTBearer())])
def delete_turno(id_turno: int):
    try:
        db.delete_turno_db(id_turno)
        return {"detail": f"Turno con ID {id_turno} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Rutas
rutas_router = APIRouter()

@rutas_router.get("/{id_ruta}", dependencies=[Depends(JWTBearer())])
def get_ruta(id_ruta: int):
    try:
        ruta = db.get_ruta_db(id_ruta)
        if not ruta:
            raise HTTPException(status_code=404, detail="Ruta no encontrada.")
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_ruta(ruta: Rutas):
    try:
        db.add_ruta_db(ruta)
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.put("/{id_ruta}", dependencies=[Depends(JWTBearer())])
def update_ruta(id_ruta: int, ruta: Rutas):
    try:
        db.update_ruta_db(id_ruta, ruta)
        return {"ruta": ruta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.delete("/{id_ruta}", dependencies=[Depends(JWTBearer())])
def delete_ruta(id_ruta: int):
    try:
        db.delete_ruta_db(id_ruta)
        return {"detail": f"Ruta con ID {id_ruta} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Visitas
visitas_router = APIRouter()

@visitas_router.get("/{id_visita}", dependencies=[Depends(JWTBearer())])
def get_visita(id_visita: int):
    try:
        visita = db.get_visita_db(id_visita)
        if not visita:
            raise HTTPException(status_code=404, detail="Visita no encontrada.")
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_visita(visita: Visitas):
    try:
        db.add_visita_db(visita)
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.put("/{id_visita}", dependencies=[Depends(JWTBearer())])
def update_visita(id_visita: int, visita: Visitas):
    try:
        db.update_visita_db(id_visita, visita)
        return {"visita": visita}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.delete("/{id_visita}", dependencies=[Depends(JWTBearer())])
def delete_visita(id_visita: int):
    try:
        db.delete_visita_db(id_visita)
        return {"detail": f"Visita con ID {id_visita} eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion