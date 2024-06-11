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
    id_usuario: Optional[int] = None
    nombre_usuario: str
    hashed_password: str
    email: str
    rol: TipoUsuario
    token: Optional[str] = None

class UsuarioInvite(BaseModel):
    nombre_usuario: str
    email: str
    rol: TipoUsuario

class TipoCliente(str, Enum):
    particular = "particular"
    dispositivo = "dispositivo"
    salud = "salud"

class ClientesCreate(BaseModel):
    documento: int
    nombre: str
    apellido: str
    tipo: TipoCliente
    
class Clientes(ClientesCreate):
    direccion: str
    telefono: Optional[int]
    email: Optional[str]
    observaciones: Optional[str]
    id_cliente: Optional[int]

class ClientesCaracteristicas(BaseModel):
    id_cliente: int
    caracteristica: str

class PedidosCreate(BaseModel):
    cliente_documento: int
    direccion_origen: str
    direccion_destino: str
    prioridad: int
    acompañante: bool
    observaciones: Optional[str]

class Pedidos(BaseModel):
    id_pedido: Optional[int]
    latitud_origen: float
    latitud_destino: float
    longitud_origen: float
    longitud_destino: float
    ventana_origen_inicio: Optional[datetime]
    ventana_origen_fin: Optional[datetime]
    ventana_destino_inicio: Optional[datetime]
    ventana_destino_fin: Optional[datetime]

class Vehiculos(BaseModel):
    id_vehiculo: Optional[int]
    matricula: str
    descripcion: Optional[str]
    documento_chofer: Optional[int]
    capacidad_convencional: int = Field(..., gt=0)
    capacidad_silla_de_ruedas: int = Field(..., gt=0)
    disponibilidad: bool
    observaciones: Optional[str]

class VehiculosCaracteristicas(BaseModel):
    id_vehiculo: int
    caracteristica: str

class Choferes(BaseModel):
    id_chofer: Optional[int] = None
    documento: int
    nombre: str
    apellido: str
    telefono: Optional[str]
    observaciones: Optional[str]

class LugaresComunes(BaseModel):
    id_lugar_comun: Optional[int]
    nombre: str
    direccion: str
    latitud: float
    longitud: float
    observaciones: Optional[str]

class Planificaciones(BaseModel):
    id_planificacion: Optional[int]
    nombre: str
    fecha: datetime
    fechaCreacion: datetime
    observaciones: Optional[str]

class Turnos(BaseModel):
    id_turno: Optional[int]
    id_planificacion: int
    descripcion: str
    hora_inicio: datetime
    hora_fin: datetime

class Geometria(BaseModel):
    type: str
    coordinates: List[List[float]]

class Rutas(BaseModel):
    id_ruta: Optional[int]
    id_turno: int
    id_vehiculo: int
    id_chofer: int
    hora_salida: datetime
    hora_llegada: datetime
    geometria: Geometria
    observaciones: Optional[str]

class EstadoVisita(str, Enum):
    pendiente = "Pendiente"
    realizada = "Realizada"
    cancelada = "Cancelada"

class TipoItemVisita(str, Enum):
    lugar_comun = "Lugar común"
    pedido = "Pedido"

class Visitas(BaseModel):
    id_visita: Optional[int]
    id_ruta: int
    id_item: int
    tipo_item: TipoItemVisita
    hora_llegada: datetime
    hora_salida: datetime
    estado: EstadoVisita
    observaciones: Optional[str]

