from fastapi import Header, HTTPException, status

from .config import settings


def verify_api_key(x_api_key: str = Header(...)):
    """FastAPI dependency — called automatically on every protected route.

    FastAPI reads the parameter name 'x_api_key' and maps it to the
    HTTP header 'X-API-Key' (underscores become dashes automatically).

    Header(...) means "this header is required — reject the request if missing".
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
