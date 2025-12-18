from app.sync.dahua import DahuaSync
from app.sync.hikvision import HikvisionSync


class SyncStrategyResolver:

    def resolve(self, brand: str):
        if brand == "Dahua":
            return DahuaSync()
        if brand == "HIKVision":
            return HikvisionSync()

        raise Exception("Unsupported brand")
