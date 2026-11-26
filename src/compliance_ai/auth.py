from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

TOKEN_ISSUER = "compliance-ai"
TOKEN_AUDIENCE = "compliance-api"
TOKEN_SECONDS = 900
PASSWORDS = PasswordHasher()
DUMMY_HASH = PASSWORDS.hash(token_urlsafe())


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return PASSWORDS.verify(password_hash or DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def issue_token(actor: UUID, secret: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(actor),
            "iss": TOKEN_ISSUER,
            "aud": TOKEN_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(seconds=TOKEN_SECONDS),
        },
        secret,
        algorithm="HS256",
    )


def verified_actor(token: str, secret: str) -> UUID:
    claims = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=TOKEN_ISSUER,
        audience=TOKEN_AUDIENCE,
        options={"require": ["sub", "iss", "aud", "iat", "exp"]},
    )
    return UUID(claims["sub"])
