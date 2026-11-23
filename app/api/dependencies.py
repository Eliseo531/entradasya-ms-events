from typing import Any, Dict, Optional
import uuid
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """Validates JWT bearer token and extracts user information."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera Authorization no proporcionada",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta claim sub",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(user_id_str))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sub debe ser un UUID válido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user_uuid,
        "name": payload.get("name"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


async def require_organizer(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Ensures that the authenticated user has the 'organizador' role."""
    if current_user.get("role") != "organizador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: requiere rol de organizador",
        )
    return current_user


async def verify_internal_or_user(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """
    Validates either internal microservice secret or client JWT.
    Used for endpoints invoked by ms-orders (/reserve, /release, /confirm-reservation).
    """
    if x_internal_token:
        if x_internal_token == settings.INTERNAL_TOKEN:
            return {"type": "internal"}
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token interno inválido",
        )

    if authorization:
        user = await get_current_user(authorization)
        return {"type": "user", **user}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida: proporcione Bearer JWT o X-Internal-Token",
        headers={"WWW-Authenticate": "Bearer"},
    )
