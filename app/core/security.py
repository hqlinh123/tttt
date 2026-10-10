from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config.settings import settings


# ================================
# Password hashing
# ================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ================================
# JWT helpers
# ================================

def _create_token(
    subject: UUID,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    now = datetime.utcnow()
    expire = now + expires_delta
    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),  # FIXED: use expire, not now
        "type": token_type,
        "iss": settings.JWT_ISSUER,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    subject: UUID,
    expires_delta: timedelta,
    extra_claims: dict | None = None,
) -> str:
    now = datetime.utcnow()
    to_encode = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
        "iss": settings.JWT_ISSUER,
    }

    # Merge extra claims
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def create_refresh_token(
    subject: UUID,
) -> str:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


# ================================
# Decode & validate tokens
# ================================

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises JWTError for invalid/expired tokens.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        options={"verify_exp": True, "verify_iss": False},
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate an access token.
    Raises JWTError for invalid tokens or ValueError for wrong token type.
    """
    try:
        payload = decode_token(token)
        
        # Check token type
        if payload.get("type") != "access":
            raise ValueError("Invalid token type: expected access token")
        
        # Optional: Check if token is expired (though decode_token already does this)
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise ValueError("Token has expired")
        
        return payload
        
    except JWTError as e:
        raise JWTError(f"Invalid or expired token: {str(e)}")
    except ValueError as e:
        raise ValueError(str(e))


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a refresh token.
    Raises JWTError for invalid tokens or ValueError for wrong token type.
    """
    try:
        payload = decode_token(token)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type: expected refresh token")
        
        return payload
        
    except JWTError as e:
        raise JWTError(f"Invalid or expired refresh token: {str(e)}")
    except ValueError as e:
        raise ValueError(str(e))


def decode_reset_token(token: str) -> Dict[str, Any]:
    """
    Decode a password reset token.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid or expired reset token: {str(e)}")


# ================================
# Optional: Helper for FastAPI dependencies
# ================================

def get_current_user_from_token(token: str) -> int:
    """
    Extract user ID from access token.
    Useful for dependency injection.
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing subject")
        return int(user_id)
    except (JWTError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )