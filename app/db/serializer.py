from pydantic import BaseModel, Field, validator
from typing import Dict
from datetime import datetime


class InDBBaseSerializer(BaseModel):
    id: str
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime | None

    class Config:
        orm_mode = True

    @validator("updated_at")
    def default_updated_at_to_created_at(
        cls, updated_at: datetime | None, values: Dict
    ) -> datetime:
        if not updated_at:
            updated_at = (
                values["created_at"] if values["created_at"] else datetime.now()
            )
        return updated_at
