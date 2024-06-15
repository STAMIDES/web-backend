from typing import Optional, List
from pydantic import BaseModel, Field # type: ignore
from shapely.geometry import LineString # type: ignore
from datetime import datetime
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

class TipoCliente(str, Enum):
    particular = "particular"
    dispositivo = "dispositivo"
    salud = "salud"
 
class Clientes(BaseModel):
    id: Optional[int] = None
    documento: int
    nombre: str
    apellido: str
    direccion: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    tipo: TipoCliente
    observaciones: Optional[str] = None

class ClientesCaracteristicas(BaseModel):
    id: Optional[int] = None
    id_cliente: int
    caracteristica: str # esto debe ser una clave foránea de una tabla de características. hay que crear esa tabla con el modelo de abajo

class CaracteristicasClientes(BaseModel):
    id: Optional[int] = None
    nombre: str

class TipoPedido(str, Enum):
    solo_ida = "Solo ida"
    solo_vuelta = "Solo vuelta"
    ida_y_vuelta = "Ida y vuelta"

class Pedidos(BaseModel):
    id: Optional[int] = None
    cliente_documento: int
    prioridad: int
    acompañante: bool
    tipo: TipoPedido
    fecha_ingresado: datetime
    observaciones: Optional[str] = None

class Paradas(BaseModel):
    id: Optional[int] = None
    id_pedido: int
    posicion_en_pedido: int
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ventana_horaria_inicio: Optional[datetime] = None
    ventana_horaria_fin: Optional[datetime] = None
    observaciones: Optional[str] = None

class Vehiculos(BaseModel):
    id: Optional[int] = None
    matricula: Optional[str] = None
    descripcion: Optional[str] = None
    documento_chofer_habitual: Optional[int]
    capacidad_convencional: int = Field(..., gt=0)
    capacidad_silla_de_ruedas: int = Field(..., gt=0)
    disponibilidad: bool
    observaciones: Optional[str]

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
    observaciones: Optional[str] = None

class LugaresComunes(BaseModel):
    id: Optional[int] = None
    nombre: str
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    observaciones: Optional[str] = None

class Planificaciones(BaseModel):
    id: Optional[int] = None
    nombre: str
    fecha: datetime
    fechaCreacion: datetime
    observaciones: Optional[str] = None

class Turnos(BaseModel):
    id: Optional[int] = None
    id_planificacion: int
    descripcion: str
    hora_inicio: datetime
    hora_fin: datetime

class Geometria(BaseModel):
    type: str
    coordinates: List[List[float]]

class Rutas(BaseModel):
    id: Optional[int] = None
    id_turno: int
    id_vehiculo: int
    id_chofer: int
    hora_inicio: datetime
    hora_fin: datetime
    geometria: Geometria
    observaciones: Optional[str] = None

class EstadoVisita(str, Enum):
    pendiente = "Pendiente"
    realizada = "Realizada"
    cancelada = "Cancelada"

class TipoItemVisita(str, Enum):
    lugar_comun = "Lugar común"
    parada = "Parada"

class Visitas(BaseModel):
    id: Optional[int] = None
    id_ruta: int
    id_item: int # id del lugar común o de la parada
    tipo_item: TipoItemVisita
    hora_llegada: datetime
    hora_salida: datetime
    estado: EstadoVisita
    observaciones: Optional[str] = None

