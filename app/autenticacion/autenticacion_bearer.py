from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .autenticacion import validate_token # Assuming this function decodes the JWT and returns the payload

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        # Get token from cookie instead of Authorization header
        access_token = request.cookies.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=403, detail="Not authenticated")
        
        try:
            payload = validate_token(access_token)
            request.state.user_email = payload.get("sub")
            return payload
        except Exception as e:
            raise HTTPException(status_code=403, detail="Invalid token or expired token")
