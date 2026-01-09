from pydantic import BaseModel, Field

class DeviceLogRequest(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    maxResults: int = 100
    majorType: str = "ALL"

    class Config:
        allow_population_by_field_name = True
