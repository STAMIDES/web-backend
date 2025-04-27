from typing import Optional, List
from pydantic import BaseModel, Field, validator # type: ignore
from shapely.geometry import LineString # type: ignore
from datetime import datetime, time
from enum import Enum

class TipoUsuario(str, Enum):
    operador = "operador"
    chofer = "chofer"

class LoginRequest(BaseModel):
    username: str
    password: str

class Usuarios(BaseModel):
    id: Optional[int] = None
    email: str
    hashed_password: str
    nombre: Optional[str] = None
    rol: TipoUsuario
    token: Optional[str] = None

class InvitacionUsuario(BaseModel):
    nombre: str
    email: str
    rol: TipoUsuario

class RegistroUsuario(BaseModel):
    nombre: str
    password: str


class Clientes(BaseModel):
    id: Optional[int] = None
    documento: int
    nombre: str
    apellido: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    observaciones: Optional[str] = None
    caracteristicas: Optional[List[int]] = None

class ClientesCaracteristicas(BaseModel):
    id: Optional[int] = None
    id_cliente: int
    caracteristica: str # esto debe ser una clave foránea de una tabla de características. hay que crear esa tabla con el modelo de abajo

class Caracteristicas(BaseModel):
    id: Optional[int] = None
    nombre: str
class ForgotPasswordRequest(BaseModel):
    email: str

class ValidateResetTokenRequest(BaseModel):
    token: str
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    email: str
    new_password: str

class TipoPedido(str, Enum):
    solo_ida = "Solo ida"
    solo_vuelta = "Solo vuelta"
    ida_y_vuelta = "Ida y vuelta"

@validator('ventana_horaria_inicio', 'ventana_horaria_fin', pre=True)
def validate_time(cls, v):
    if v is not None:
        try:
            datetime.strptime(v, '%H:%M')
        except ValueError:
            raise ValueError('Time must be in format HH:MM')
    return v

class TiposParadas(BaseModel):
    id: Optional[int] = None
    nombre: str

class Paradas(BaseModel):
    id: Optional[int] = None
    id_pedido: Optional[int] = None
    posicion_en_pedido: int
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ventana_horaria_inicio: Optional[time] = None
    ventana_horaria_fin: Optional[time] = None
    tipo: Optional[int] = None
    observaciones: Optional[str] = None

class EstadoPedido(str, Enum):
    pendiente = "Pendiente"
    asignado = "Asignado"
    rechazado = "Rechazado"

class Pedidos(BaseModel):
    id: Optional[int] = None
    cliente_documento: int
    prioridad: int
    acompañante: bool
    tipo: TipoPedido
    fecha_ingresado: Optional[datetime] = None
    fecha_programado: datetime
    estado: EstadoPedido = EstadoPedido.pendiente
    observaciones: Optional[str] = None
    paradas: List[Paradas]

class Vehiculos(BaseModel):
    id: Optional[int] = None
    matricula: Optional[str] = None
    descripcion: Optional[str] = None
    capacidad_convencional: int = Field(..., gt=0)
    capacidad_silla_de_ruedas: int = Field(..., ge=0)
    activo: bool = True
    observaciones: Optional[str] = None
    caracteristicas: Optional[List[int]] = None	

class VehiculosCaracteristicas(BaseModel):
    id: Optional[int] = None
    id_vehiculo: int
    caracteristica: str

class Choferes(BaseModel):
    id: Optional[int] = None
    documento: int
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    activo: bool
    observaciones: Optional[str] = None

class LugaresComunes(BaseModel):
    id: Optional[int] = None
    nombre: str
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    activo: Optional [bool] = True
    observaciones: Optional[str] = None

class Geometria(BaseModel):  # REMOVEME??
    type: str
    coordinates: List[List[float]]

class EstadoVisita(str, Enum):
    pendiente = "Pendiente"
    realizada = "Realizada"
    cancelada = "Cancelada"

class TipoItemVisita(str, Enum):
    lugar_comun = "Lugar común"
    parada = "Parada"

class Visitas(BaseModel):
    id: Optional[int] = None
    id_ruta: Optional[int] = None
    id_item: int # id del lugar común o de la parada
    tipo_item: TipoItemVisita
    hora_llegada: time
    hora_salida: time
    estado: EstadoVisita = EstadoVisita.pendiente
    observaciones: Optional[str] = None

# Una ruta pertece a una planificación y tiene un vehículo asignado, puede pertenecer a varios turnos y tiene un chofer por turno
class Rutas(BaseModel):
    id: Optional[int] = None
    id_planificacion: int = None
    id_vehiculo: int
    id_chofer: int
    hora_inicio: time
    hora_fin: time
    geometria: List[List[float]]
    observaciones: Optional[str] = None
    visitas: List[Visitas] = None

class Turnos(BaseModel):
    id: Optional[int] = None
    id_planificacion: int = None
    hora_inicio: time
    hora_fin: time

class Planificaciones(BaseModel):
    id: Optional[int] = None
    usuario_id: int = None
    fecha: datetime
    fecha_creacion: datetime = None
    observaciones: Optional[str] = None

