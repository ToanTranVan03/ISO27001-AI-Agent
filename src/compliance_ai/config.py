from dataclasses import dataclass
from os import getenv
from typing import Literal

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    execution_mode: Literal["SIMULATION"] = "SIMULATION"
    database_url: str | None = None

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        if getenv("EXECUTION_MODE", "SIMULATION") != "SIMULATION":
            raise ValueError("EXECUTION_MODE must be SIMULATION")
        if getenv("LAB_ENABLED", "false").lower() != "false":
            raise ValueError("LAB_ENABLED must be false")
        return cls(database_url=getenv("DATABASE_URL") or None)


def auth_secret() -> str:
    secret = getenv("APP_SECRET_KEY", "")
    if len(secret.encode("utf-8")) < 32:
        raise ValueError("APP_SECRET_KEY must be set to a random secret of at least 32 bytes")
    return secret
