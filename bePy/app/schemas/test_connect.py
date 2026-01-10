from pydantic import BaseModel

class DeviceConnectionTest(BaseModel):
    ip_web: str
    username: str
    password: str
    brand: str
class DeviceConnectionTestResult(BaseModel):
    ip_reachable: bool
    auth_ok: bool
    message: str
