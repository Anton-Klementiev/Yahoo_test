from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from src.config import API_KEY

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided: str = Security(_api_key_header)) -> None:
    """Reject any request that doesn't carry the correct X-API-Key header."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server API key is not configured.")
    if provided != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )