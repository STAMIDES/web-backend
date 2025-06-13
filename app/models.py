from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, validator, ConfigDict,  model_validator, computed_field# type: ignore
from shapely.geometry import LineString # type: ignore
from datetime import datetime, time
from enum import Enum

class LoginRequest(BaseModel):
    username: str
    password: str

class Usuarios(BaseModel):
    id: Optional[int] = None
    email: str
    hashed_password: str
    nombre: Optional[str] = None
    token: Optional[str] = None

class InvitacionUsuario(BaseModel):
    nombre: str
    email: str

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
    activo: Optional[bool] = True
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
    hora_calculada_de_llegada: time
    hora_pedida: Optional[time] = None
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
    descanso_inicio: Optional[time] = None
    descanso_fin: Optional[time] = None
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
    definitiva: Optional[bool] = False

class CaracteristicaSchema(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class ClienteSchema(BaseModel):
    id: int
    documento: int
    nombre: str
    apellido: str
    caracteristicas: List[CaracteristicaSchema] = []
    model_config = ConfigDict(from_attributes=True)

class TipoParadaSchema(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)
    
class ParadaSchema(BaseModel):
    id: int
    posicion_en_pedido: int
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ventana_horaria_inicio: Optional[time] = None
    ventana_horaria_fin: Optional[time] = None
    observaciones: Optional[str] = None
    tipo_parada: Optional[TipoParadaSchema] = None
    es_destino: bool = False
    model_config = ConfigDict(from_attributes=True)

class LugarComunSchema(BaseModel):
    id: int
    nombre: str
    direccion: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class PedidoSchema(BaseModel):
    id: int
    prioridad: int
    acompañante: bool
    tipo: TipoPedido
    fecha_programado: datetime
    observaciones: Optional[str] = None
    cliente: ClienteSchema
    paradas: List[ParadaSchema] = []
    no_enviado_al_optimizador: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class VisitaSchema(BaseModel):
    id: int
    estado: EstadoVisita
    hora_calculada_de_llegada: time
    hora_pedida: Optional[time] = None
    observaciones: Optional[str] = None
    
    # Campos que necesitamos para la lógica, pero que no queremos en el JSON final.
    # Los obtenemos del objeto SQLAlchemy usando un alias.
    parada: Optional[ParadaSchema] = Field(None, exclude=True)
    lugar_comun: Optional[LugarComunSchema] = Field(None, exclude=True)
    
    # El campo que SÍ queremos en el JSON final.
    item: Optional[Union[ParadaSchema, LugarComunSchema]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def set_item(self) -> 'VisitaSchema':
        # 'self' es la instancia de VisitaSchema ya creada.
        # Pydantic ya ha poblado self.parada y self.lugar_comun
        # a partir del objeto SQLAlchemy.
        if self.parada:
            self.item = self.parada
        elif self.lugar_comun:
            self.item = self.lugar_comun
        
        # Limpiamos los campos intermedios para que no se queden en el objeto final
        # (aunque `exclude=True` ya debería encargarse de esto en la serialización)
        self.parada = None
        self.lugar_comun = None
        
        return self
class VehiculoSchema(BaseModel):
    id: int
    matricula: str
    descripcion: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ChoferSchema(BaseModel):
    id: int
    nombre: str
    apellido: str
    model_config = ConfigDict(from_attributes=True)

class RutaSchema(BaseModel):
    id: int
    hora_inicio: time
    hora_fin: time
    geometria: Optional[List] = None # Geometría ya procesada
    observaciones: Optional[str] = None
    vehiculo: VehiculoSchema
    chofer: ChoferSchema
    visitas: List[VisitaSchema] = []
    model_config = ConfigDict(from_attributes=True)

class TurnoSchema(BaseModel):
    id: int
    descripcion: Optional[str] = None
    hora_inicio: time
    hora_fin: time
    model_config = ConfigDict(from_attributes=True)

class UsuarioSchema(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

# --- El Schema final para la respuesta del endpoint ---
class PlanificacionDetailSchema(BaseModel):
    id: int
    fecha: datetime
    fecha_creacion: datetime
    fmt_fecha: str
    fmt_fecha_creacion: str
    definitiva: bool
    observaciones: Optional[str] = None
    creado_por: UsuarioSchema
    turnos: List[TurnoSchema] = []
    rutas: List[RutaSchema] = []
    pedidos_no_atendidos: List[PedidoSchema] = Field(default=[], alias='pedidos_no_atendidos_procesados')
    model_config = ConfigDict(from_attributes=True)

class PlanificacionResponse(BaseModel):
    planificacion: PlanificacionDetailSchema