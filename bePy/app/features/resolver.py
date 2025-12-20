from app.features.sync.dahua import DahuaSync
from app.features.sync.hikvision import HikvisionSync
from app.features.RecordInfo.hikrecord import HikvisionRecordService

class StrategyResolver:

    def sync_resolve(self, brand: str):
        if brand == "Dahua":
            return DahuaSync()
        if brand == "HIKVision":
            return HikvisionSync()

        raise Exception("Unsupported brand")
    
    def record_resolve(self, brand: str):
        if brand == "HIKVision":
            return HikvisionRecordService()

        raise Exception("Unsupported brand")