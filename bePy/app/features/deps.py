import xml.etree.ElementTree as ET
import base64
import httpx

HIK_NS = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

def xml_text(elem, path: str):
    node = elem.find(path, HIK_NS)
    return node.text if node is not None else None

def build_hik_auth(device):
    

    auth = base64.b64encode(
        f"{device.username}:{device.password}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/xml"
    }
