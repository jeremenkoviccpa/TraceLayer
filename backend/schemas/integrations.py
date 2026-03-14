import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from integrations.registry import available_integrations


class ConnectRequest(BaseModel):
    integration_type: str
    credentials: dict

    def validate_type(self) -> None:
        if self.integration_type not in available_integrations():
            raise ValueError(
                f"Unknown integration type '{self.integration_type}'. "
                f"Available: {available_integrations()}"
            )


class IntegrationResponse(BaseModel):
    id: uuid.UUID
    integration_type: str
    status: str
    last_collected_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
