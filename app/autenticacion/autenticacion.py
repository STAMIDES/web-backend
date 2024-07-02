import jwt # type: ignore
from datetime import datetime, timedelta
from passlib.context import CryptContext # type: ignore

# Clave secreta para firmar el token (asegúrate de mantenerla segura)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
TOKEN_EXPIRATION = timedelta(hours = 10)
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Función para generar el token
# def generate_token(user_id: int):
#     payload = {
#         "user_id": user_id,
#         "exp": datetime.utcnow() + TOKEN_EXPIRATION
#     }

#     # Genera el token utilizando la clave secreta y el algoritmo de firma indicado
#     token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#     return token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Función para validar el token
def validate_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Si el token ha expirado, se lanza una excepción
        raise jwt.ExpiredSignatureError
    except jwt.InvalidTokenError:
        # Si el token es inválido, se lanza una excepción
        raise jwt.InvalidTokenError

# Función para verificar la contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Función para encriptar la contraseña
def get_password_hash(password):
    return pwd_context.hash(password)
