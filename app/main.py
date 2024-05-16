from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
import database as db
import routes as r
from database import Base


origins = [
    "*",  
]

app = FastAPI(debug = True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=db.engine) # En producción hay que sacar esto de acá
app.include_router(r.clientes_router, prefix="/clientes")
app.include_router(r.clientes_caracteristicas_router, prefix="/clientes_caracteristicas")
app.include_router(r.pedidos_router, prefix="/pedidos")
app.include_router(r.vehiculos_router, prefix="/vehiculos")
app.include_router(r.vehiculos_caracteristicas_router, prefix="/vehiculos_caracteristicas")
app.include_router(r.choferes_router, prefix="/choferes")
app.include_router(r.lugares_comunes_router, prefix="/lugares_comunes")
app.include_router(r.planificaciones_router, prefix="/planificaciones")
app.include_router(r.turnos_router, prefix="/turnos")
app.include_router(r.rutas_router, prefix="/rutas")
app.include_router(r.visitas_router, prefix="/visitas")
app.include_router(r.usuarios_router, prefix="/usuarios")

