import logging
import sys
from fastapi import FastAPI, Request, status # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from fastapi.responses import JSONResponse # type: ignore

import database as db
import routes as r
from database import Base

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('app.log', mode='a')

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)



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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)