from typing import Literal

from pydantic import BaseModel


class HealthData(BaseModel):
    status: Literal["healthy", "degraded"] = "healthy"
    database: Literal["connected", "disconnected"] = "connected"
