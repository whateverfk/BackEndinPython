from pydantic import BaseModel


class SyncResult(BaseModel):
    success: bool
    message: str
