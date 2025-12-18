from abc import ABC, abstractmethod
from datetime import datetime
from app.schemas.sync import SyncResult


class SyncStrategy(ABC):

    @abstractmethod
    async def sync(self, device, server_time: datetime) -> SyncResult:
        ...
