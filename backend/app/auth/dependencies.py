import jwt
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import get_settings
from app.database.supabase_client import get_supabase_client
from app.schemas.auth import CurrentUser
from app.utils.exceptions import UnauthorizedError
from app.utils.logger import logger

security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    Validates Supabase JWT or Bearer token and returns the authenticated CurrentUser.
    Raises UnauthorizedError (401) if missing or invalid.
    """
    if not auth_credentials or not auth_credentials.credentials:
        raise UnauthorizedError("Missing authentication credentials")

    token = auth_credentials.credentials.strip()
    settings = get_settings()

    # 1. Dev / Test mode quick token bypass
    if settings.DEBUG and (token.startswith("dev-") or token.startswith("test-") or token == "demo-token"):
        user_id = token.split("-", 1)[1] if "-" in token else "demo-user"
        return CurrentUser(
            id=user_id,
            email=f"{user_id}@civicai.local",
            role="authenticated",
            is_anonymous=False,
        )

    # 2. Try Supabase Auth client if live
    supabase = get_supabase_client()
    if supabase:
        try:
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                u = user_response.user
                return CurrentUser(
                    id=str(u.id),
                    email=u.email,
                    role=getattr(u, "role", "authenticated") or "authenticated",
                    is_anonymous=False,
                )
        except Exception as e:
            logger.debug(f"Supabase auth client validation failed: {e}. Falling back to JWT decode.")

    # 3. Fallback: Decode Supabase JWT locally
    try:
        # First attempt with secret if configured
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise UnauthorizedError("Token payload missing subject identifier")

        return CurrentUser(
            id=str(user_id),
            email=payload.get("email"),
            role=payload.get("role", "authenticated"),
            is_anonymous=False,
        )
    except jwt.PyJWTError as e:
        # In development/test mode, if JWT secret doesn't match, decode unverified for test ergonomics
        if settings.ENVIRONMENT in ["development", "test"]:
            try:
                unverified_payload = jwt.decode(token, options={"verify_signature": False})
                user_id = unverified_payload.get("sub") or unverified_payload.get("user_id") or "dev-user"
                return CurrentUser(
                    id=str(user_id),
                    email=unverified_payload.get("email", "user@civicai.local"),
                    role=unverified_payload.get("role", "authenticated"),
                    is_anonymous=False,
                )
            except Exception:
                pass
        
        logger.warning(f"JWT verification failed: {e}")
        raise UnauthorizedError("Invalid or expired authentication token")


async def get_optional_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """
    Returns CurrentUser if valid token is provided, or None if unauthenticated.
    """
    if not auth_credentials or not auth_credentials.credentials:
        return None

    try:
        return await get_current_user(auth_credentials)
    except UnauthorizedError:
        return None
