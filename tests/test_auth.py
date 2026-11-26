from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from compliance_ai.auth import (
    PASSWORDS,
    TOKEN_AUDIENCE,
    TOKEN_ISSUER,
    issue_token,
    verified_actor,
    verify_password,
)


def test_argon2_and_verified_token() -> None:
    password = "phase03-test-only"
    password_hash = PASSWORDS.hash(password)
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash)
    assert not verify_password("incorrect", password_hash)
    assert not verify_password(password, None)
    actor = uuid4()
    secret = "t" * 32
    token = issue_token(actor, secret)
    assert verified_actor(token, secret) == actor
    with pytest.raises(jwt.InvalidTokenError):
        verified_actor(token, "s" * 32)


def test_expired_token_rejected() -> None:
    now = datetime.now(UTC)
    secret = "s" * 32
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": TOKEN_AUDIENCE,
            "iss": TOKEN_ISSUER,
            "iat": now - timedelta(minutes=16),
            "exp": now - timedelta(minutes=1),
        },
        secret,
        algorithm="HS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        verified_actor(token, secret)
