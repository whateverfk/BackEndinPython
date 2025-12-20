import base64
import httpx


def build_hik_auth(device):
    auth = base64.b64encode(
        f"{device.username}:{device.password}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/xml"
    }
