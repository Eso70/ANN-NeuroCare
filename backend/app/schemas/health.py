from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class DatabaseHealthResponse(HealthResponse):
    database: Literal["connected"] = "connected"


class ApiInfo(BaseModel):
    name: str = "NeuroCare API"
    version: str = "0.1.0"
