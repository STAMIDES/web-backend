from typing import List
from fastapi import APIRouter, HTTPException, Response, Request, Depends # type: ignore
from models import (Pedidos, Paradas, Clientes, ClientesCaracteristicas, Vehiculos, LugaresComunes, Choferes,
                    VehiculosCaracteristicas, Planificaciones, Turnos, Rutas, Visitas, Usuarios, LoginRequest, InvitacionUsuario, RegistroUsuario) # type: ignore
import database as db

import autenticacion.autenticacion as aut
from autenticacion.autenticacion_bearer import JWTBearer
from datetime import datetime
import logging
from utils import Mailer
import traceback
log = logging.getLogger("routes")

# region Usuarios
usuarios_router = APIRouter()

@usuarios_router.get("/", dependencies=[Depends(JWTBearer())])
def get_usuarios(offset: int = 0, limit: int = 10, search: str = ''):
    try:
        usuarios, cantidad = db.get_usuarios(offset=offset, limit=limit)
        return {"usuarios": usuarios, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.get("/check", response_model=dict, dependencies=[Depends(JWTBearer())])
def check_session():
    try:
        return {"detail": "Logged in successfully"}
    except Exception as e:
        log.error(traceback.format_exc())

@usuarios_router.get("/{id_usuario}", dependencies=[Depends(JWTBearer())])
def get_usuario(id_usuario: int):
    try:
        usuario = db.get_usuario_db(id_usuario)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        return {"usuario": usuario}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/invitar", dependencies=[Depends(JWTBearer())])
def invite_usuario(usuarioInv: InvitacionUsuario):
    try:
        if not db.get_user_by_email(usuarioInv.email):
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

@usuarios_router.post("/") # FIXME delete this endpoint and create users by invitations// this is for testing purposes
def add_usuario(usuario: Usuarios):
    try:
        usuario = db.add_usuario_db(usuario)
        return {"usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
            
@usuarios_router.get("/registro/{hash_link}")
def get_user_invitation(hash_link: str): # type: ignore
    try:
        usuarioInv = db.get_invitation(hash_link)
        if not usuarioInv:
            raise HTTPException(status_code=400, detail='Invitación no existente o ya usada')
        return usuarioInv
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.post("/registro/{hash_link}")
def add_usuario_by_inv(hash_link: str, nuevo_user: RegistroUsuario):
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@usuarios_router.put("/{email}", dependencies=[Depends(JWTBearer())])
def update_usuario(email: int, usuario: Usuarios):
    try:
        db.update_usuario_db(email, usuario)
        return {"usuario": usuario}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@usuarios_router.delete("/{email}", dependencies=[Depends(JWTBearer())])
def delete_usuario(email: int):
    try:
        db.delete_usuario_db(email)
        return {"detail": f"Usuario {email} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")


@usuarios_router.post("/login")
def login(request: LoginRequest, response: Response):
    try:
        access_token, refresh_token = db.login(request.username, request.password)
        # Set secure HTTP-only cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600  # 1 hour
        )
        response.set_cookie(
            key="refresh_token", 
            value=refresh_token,
            path='/usuarios/logout',
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=6*31*24*3600  # 6 months
        )
        
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=e.args[0] if e.args else "Usuario o contraseña incorrectos")
    
@usuarios_router.post("/logout/refresh")
def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    payload = aut.validate_token(refresh_token)
    
    user_email = payload.get("sub")
    user = db.get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if the refresh token is valid in the database
    if not db.is_refresh_token_valid(user.id, refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token is not valid")
    
    # Generate new access token
    new_access_token = aut.create_access_token(data={"sub": user_email, "user_id": user.id})
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite='lax',
        max_age=3600  # 1 day
    )
    
    return {"message": "Token refreshed successfully"}

@usuarios_router.post("/logout", dependencies=[Depends(JWTBearer())])
def logout(request: Request, response: Response):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            db.logout(refresh_token)
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token", path='/usuarios/refresh')
        return {"message": "Usuario desconectado correctamente"}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
# endregion

# region Clientes
clientes_router = APIRouter()

@clientes_router.get("/{id}", dependencies=[Depends(JWTBearer())])
def get_cliente_completo(id: int, completo = False):
    try:
        if completo:
            cliente = db.get_cliente_completo(id)
        else:
            cliente = db.get_cliente(id)
        if not cliente:
            raise HTTPException(status_code=400, detail="Cliente no encontrado.")
        return cliente
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/", dependencies=[Depends(JWTBearer())])
def get_clientes(limit: int = 10, offset: int = 0, search: str = ''):
    try:
        log.info("Obteniendo clientes")
        clientes, cantidad = db.get_clientes_db(limit, offset, search)
        return {"clientes": clientes, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/doc/{documento}", dependencies=[Depends(JWTBearer())])
def get_clientes_documento(documento: int, limit: int = 10, offset: int = 0):
    try:
        clientes, cantidad = db.get_clientes_by_documento_db(documento, limit, offset)
        return {"clientes": clientes, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("/nombre/{nombre}", dependencies=[Depends(JWTBearer())])
def get_clientes_nombre(nombre: str, limit: int = 10, offset: int = 0):
    try:
        clientes = db.get_clientes_by_nombre_db(nombre, limit, offset)
        return {"clientes": clientes}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.get("tipo/{tipo}", dependencies=[Depends(JWTBearer())])
def get_clientes_tipo(tipo: str, limit: int = 10, offset: int = 0):
    try:
        clientes = db.get_clientes_by_tipo_db(tipo, limit, offset)
        return {"clientes": clientes}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.get("/caracteristica/{caracteristica}", dependencies=[Depends(JWTBearer())])
def get_clientes_caracteristica(caracteristica: str, limit: int = 10, offset: int = 0):
    try:
        clientes = db.get_clientes_by_caracteristica_db(caracteristica, limit, offset)
        return {"clientes": clientes}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_cliente(cliente: Clientes):
    try:
        if not db.get_cliente_by_doc(cliente.documento):
            cliente = db.add_cliente_db(cliente)
            return {"cliente": cliente}
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese documento.")
    except HTTPException as e:
        raise e
    except Exception as e:
       log.error(traceback.format_exc())
       raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.put("/{documento}", dependencies=[Depends(JWTBearer())])
def update_cliente(documento: int, cliente: Clientes):
    try:
        updated_cliente = db.update_cliente_db(documento, cliente)
        return  updated_cliente
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@clientes_router.delete("/{id}", dependencies=[Depends(JWTBearer())])
def delete_cliente(id: int):
    try:
        db.delete_cliente_db(id)
        return {"detail": f"Cliente eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_router.put("/activar/{documento}", dependencies=[Depends(JWTBearer())])
def activate_cliente(documento: int):
    try:
        message = db.activate_cliente_db(documento)
        return message
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@clientes_caracteristicas_router.delete("/{documento}", dependencies=[Depends(JWTBearer())])
def delete_cliente_caracteristica(documento: int):
    try:
        deleted = db.delete_cliente_caracteristica(documento)
        if deleted:
            return {"detail": f"Característica eliminada correctamente para el documento {documento}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el documento {documento}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region Caracteristicas
caracteristicas_router = APIRouter()

@caracteristicas_router.get("/", dependencies=[Depends(JWTBearer())])
def get_caracteristicas(limit: int = 10, offset: int = 0):
    try:
        return db.get_caracteristicas_db()
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@caracteristicas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_caracteristica(caracteristica: str):
    try:
        db.add_caracteristica_db(caracteristica)
        return {"caracteristica": caracteristica}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.get("/", dependencies=[Depends(JWTBearer())])
def get_pedidos(limit: int = 10, offset: int = 0, search: str = ''):
    try:
        pedidos, cantidad = db.get_pedidos_db(limit, offset, search)
        return {"pedidos": pedidos, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.get("/cliente/{documento}", dependencies=[Depends(JWTBearer())])
def get_pedidos_cliente(documento: int, limit: int = 10, offset: int = 0):
    try:
        pedidos = db.get_pedidos_by_cliente_db(documento, limit, offset)
        return {"pedidos": pedidos}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.get("/fecha/{fecha}", dependencies=[Depends(JWTBearer())])
def get_pedidos_fecha(fecha: str, limit: int = 10, offset: int = 0, search: str = ''):
    try:
        pedidos, cantidad = db.get_pedidos_by_fecha_db(fecha, limit, offset)
        return {"pedidos": pedidos, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@pedidos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_pedido(pedido: Pedidos):
    try:
        p = db.add_pedido_db(pedido)
        return {"pedido": p}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@pedidos_router.put("/{id_pedido}", dependencies=[Depends(JWTBearer())])
def update_pedido(id_pedido: int, pedido: Pedidos):
    try:
        updated_pedido = db.update_pedido_db(id_pedido, pedido)
        return {"pedido": updated_pedido}
    except HTTPException as e:
        raise e  # Excepciones ya manejadas en database.py
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@pedidos_router.delete("/{id_pedido}", dependencies=[Depends(JWTBearer())])
def delete_pedido(id_pedido: int):
    try:
        db.delete_pedido_db(id_pedido)
        return {"message": f"Pedido con ID {id_pedido} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

# endregion

# region TiposParadas
tipos_paradas_router = APIRouter()

@tipos_paradas_router.get("/{id_tipo_parada}", dependencies=[Depends(JWTBearer())])
def get_tipo_parada(id_tipo_parada: int):
    try:
        tipo_parada = db.get_tipo_parada_db(id_tipo_parada)
        if not tipo_parada:
            raise HTTPException(status_code=404, detail="Tipo de parada no encontrado.")
        return {"tipo_parada": tipo_parada}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@tipos_paradas_router.get("/", dependencies=[Depends(JWTBearer())])
def get_tipos_paradas(limit: int = 10, offset: int = 0):
    try:
        tipos_paradas, cantidad = db.get_tipos_paradas_db(limit, offset)
        return tipos_paradas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@tipos_paradas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_tipo_parada(tipo_parada: str):
    try:
        db.add_tipo_parada_db(tipo_parada)
        return {"tipo_parada": tipo_parada}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@tipos_paradas_router.put("/{id_tipo_parada}", dependencies=[Depends(JWTBearer())])
def update_tipo_parada(id_tipo_parada: int, tipo_parada: str):
    try:
        db.update_tipo_parada_db(id_tipo_parada, tipo_parada)
        return {"tipo_parada": tipo_parada}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@tipos_paradas_router.delete("/{id_tipo_parada}", dependencies=[Depends(JWTBearer())])
def delete_tipo_parada(id_tipo_parada: int):
    try:
        db.delete_tipo_parada_db(id_tipo_parada)
        return {"message": f"Tipo de parada con ID {id_tipo_parada} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Paradas
paradas_router = APIRouter()

@paradas_router.get("/{id_parada}", dependencies=[Depends(JWTBearer())])
def get_parada(id_parada: int):
    try:
        parada = db.get_parada_db(id_parada)
        if not parada:
            raise HTTPException(status_code=404, detail="Parada no encontrada.")
        return {"parada": parada}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@paradas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_parada_pedido(parada: Paradas, pedido_id: int):
    try:
        db.add_parada_pedido_db(parada, pedido_id)
        return {"parada": parada}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@paradas_router.put("/{id_parada}", dependencies=[Depends(JWTBearer())])
def update_parada(id_parada: int, parada: Paradas):
    try:
        db.update_parada_db(id_parada, parada)
        return {"parada": parada}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@paradas_router.delete("/{id_parada}", dependencies=[Depends(JWTBearer())])
def delete_parada(id_parada: int):
    try:
        db.delete_parada_db(id_parada)
        return {"message": f"Parada con ID {id_parada} eliminada correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@vehiculos_router.get("/", dependencies=[Depends(JWTBearer())])
def get_vehiculos(limit: int = 10, offset: int = 0, search: str = ''):
    try:
        vehiculos, cantidad = db.get_vehiculos_db(limit, offset)
        return {"vehiculos": vehiculos, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@vehiculos_router.get("/matricula/{matricula}", dependencies=[Depends(JWTBearer())])
def get_vehiculo_matricula(matricula: str, limit: int = 10, offset: int = 0):
    try:
        vehiculos = db.get_vehiculo_by_matricula_db(matricula)
        return {"vehiculos": vehiculos}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@vehiculos_router.get("/activo/{activo}", dependencies=[Depends(JWTBearer())])
def get_vehiculos_activos(activo: bool, limit: int = 10, offset: int = 0):
    try:
        vehiculos = db.get_vehiculos_by_activo_db(activo, limit, offset)
        return {"vehiculos": vehiculos}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@vehiculos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_vehiculo(vehiculo: Vehiculos):
    try:
        db.add_vehiculo_db(vehiculo)
        return {"vehiculo": vehiculo}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.put("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def update_vehiculo(id_vehiculo: int, vehiculo: Vehiculos):
    try:
        nuevo_vehiculo = db.update_vehiculo_db(id_vehiculo, vehiculo)
        return {"vehiculo": nuevo_vehiculo}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@vehiculos_router.put("/estado/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def update_vehiculo(id_vehiculo: int, activo):
    try:
        db.update_vehiculo_estado_db(id_vehiculo, activo)
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_router.delete("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def delete_vehiculo(id_vehiculo: int):
    try:
        db.delete_vehiculo_db(id_vehiculo)
        return {"detail": f"Vehículo con ID {id_vehiculo} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@vehiculos_caracteristicas_router.delete("/{id_vehiculo}", dependencies=[Depends(JWTBearer())])
def delete_vehiculo_caracteristica(id_vehiculo: int):
    try:
        deleted = db.delete_vehiculo_caracteristica(id_vehiculo)
        if deleted:
            return {"detail": f"Característica eliminada correctamente para el vehículo con ID {id_vehiculo}"}
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna característica para el vehículo con ID {id_vehiculo}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion

# region Choferes
choferes_router = APIRouter()

@choferes_router.get("/{id}", dependencies=[Depends(JWTBearer())])
def get_chofer(id: int):
    try:
        chofer = db.get_chofer_db(id)
        if not chofer:
            raise HTTPException(status_code=404, detail="Chofer no encontrado.")
        return {"chofer": chofer}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.get("/", dependencies=[Depends(JWTBearer())])
def get_choferes(limit: int = 10, offset: int = 0, search: str = ''):
    try:
        choferes, cantidad = db.get_choferes_db(limit, offset)
        return {"choferes": choferes, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@choferes_router.get("/activo/{activo}", dependencies=[Depends(JWTBearer())])
def get_choferes_activos(activo: bool, limit: int = 10, offset: int = 0):
    try:
        choferes = db.get_choferes_by_activo_db(activo, limit, offset)
        return {"choferes": choferes}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@choferes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_chofer(chofer: Choferes):
    try:
        db.add_chofer_db(chofer)
        return {"chofer": chofer}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.put("/{id}", dependencies=[Depends(JWTBearer())])
def update_chofer(id: int, chofer: Choferes):
    try:
        nuevo_chofer = db.update_chofer_db(id, chofer)
        return {"chofer": nuevo_chofer}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@choferes_router.put("/estado/{id_chofer}", dependencies=[Depends(JWTBearer())])
def update_chofer(id_chofer: int, activo):
    try:
        db.update_chofer_estado_db(id_chofer, activo)
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@choferes_router.delete("/{id_chofer}", dependencies=[Depends(JWTBearer())])
def delete_chofer(id_chofer: int):
    try:
        db.delete_chofer_db(id_chofer)
        return {"detail": f"Chofer {id_chofer} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.get("/", dependencies=[Depends(JWTBearer())])
def get_lugares_comunes(limit: int = 10, offset: int = 0, search: str = ''):
    try:
        lugares, cantidad = db.get_lugares_comunes_db(limit, offset)
        return {"lugares": lugares, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@lugares_comunes_router.get("/activo/{activo}", dependencies=[Depends(JWTBearer())])
def get_lugares_comunes_activos(activo: bool, limit: int = 10, offset: int = 0):
    try:
        lugares = db.get_lugares_comunes_by_activo_db(activo, limit, offset)
        return {"lugares": lugares}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@lugares_comunes_router.post("/", dependencies=[Depends(JWTBearer())])
def add_lugar_comun(lugar: LugaresComunes):
    try:
        db.add_lugar_comun_db(lugar)
        return {"lugar": lugar}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.put("/{id_lugar}", dependencies=[Depends(JWTBearer())])
def update_lugar_comun(id_lugar: int, lugar: LugaresComunes):
    try:
        nuevo_lugar = db.update_lugar_comun_db(id_lugar, lugar)
        return {"lugar": nuevo_lugar}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@lugares_comunes_router.put("/estado/{id_lugar}", dependencies=[Depends(JWTBearer())])
def update_lugar_comun(id_lugar: int, activo):
    try:
        db.update_lugar_comun_estado_db(id_lugar, activo)
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@lugares_comunes_router.delete("/{id_lugar}", dependencies=[Depends(JWTBearer())])
def delete_lugar_comun(id_lugar: int):
    try:
        db.delete_lugar_comun_db(id_lugar)
        return {"detail": f"Lugar común con ID {id_lugar} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")

@planificaciones_router.get("/fecha/{fecha}", dependencies=[Depends(JWTBearer())])
def get_planificaciones_fecha(fecha:str, limit: int = 10, offset: int = 0, search: str = ''):
    try:
        planificaciones, cantidad = db.get_planificaciones_by_fecha_db(fecha, limit, offset)
        return {"planificaciones": planificaciones, "cantidad": cantidad}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.post("/")
def add_planificacion(
            planificacion: Planificaciones, 
            turnos: List[Turnos], 
            rutas: List[Rutas], 
            token_payload: dict = Depends(JWTBearer())  # Move token_payload inside the function parameters
        ):
    try:
        user_id: int = token_payload.get("user_id")
        nueva_planificacion = db.crear_planificacion(user_id, planificacion, turnos, rutas)
        return {"planificacion": nueva_planificacion}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.put("/{id_planificacion}", dependencies=[Depends(JWTBearer())])
def update_planificacion(id_planificacion: int, planificacion: Planificaciones):
    try:
        db.update_planificacion_db(id_planificacion, planificacion)
        return {"planificacion": planificacion}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@planificaciones_router.delete("/{id_planificacion}", dependencies=[Depends(JWTBearer())])
def delete_planificacion(id_planificacion: int):
    try:
        db.delete_planificacion_db(id_planificacion)
        return {"detail": f"Planificación con ID {id_planificacion} eliminada correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.post("/", dependencies=[Depends(JWTBearer())])
def add_turno(turno: Turnos):
    try:
        db.add_turno_db(turno)
        return {"turno": turno}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.put("/{id_turno}", dependencies=[Depends(JWTBearer())])
def update_turno(id_turno: int, turno: Turnos):
    try:
        db.update_turno_db(id_turno, turno)
        return {"turno": turno}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@turnos_router.delete("/{id_turno}", dependencies=[Depends(JWTBearer())])
def delete_turno(id_turno: int):
    try:
        db.delete_turno_db(id_turno)
        return {"detail": f"Turno con ID {id_turno} eliminado correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_ruta(ruta: Rutas):
    try:
        db.add_ruta_db(ruta)
        return {"ruta": ruta}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.put("/{id_ruta}", dependencies=[Depends(JWTBearer())])
def update_ruta(id_ruta: int, ruta: Rutas):
    try:
        db.update_ruta_db(id_ruta, ruta)
        return {"ruta": ruta}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@rutas_router.delete("/{id_ruta}", dependencies=[Depends(JWTBearer())])
def delete_ruta(id_ruta: int):
    try:
        db.delete_ruta_db(id_ruta)
        return {"detail": f"Ruta con ID {id_ruta} eliminada correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
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
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.post("/", dependencies=[Depends(JWTBearer())])
def add_visita(visita: Visitas):
    try:
        db.add_visita_db(visita)
        return {"visita": visita}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.put("/{id_visita}", dependencies=[Depends(JWTBearer())])
def update_visita(id_visita: int, visita: Visitas):
    try:
        db.update_visita_db(id_visita, visita)
        return {"visita": visita}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
@visitas_router.delete("/{id_visita}", dependencies=[Depends(JWTBearer())])
def delete_visita(id_visita: int):
    try:
        db.delete_visita_db(id_visita)
        return {"detail": f"Visita con ID {id_visita} eliminada correctamente."}
    except Exception as e:
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=e.args[0] if e.args else "Error interno del servidor")
    
# endregion