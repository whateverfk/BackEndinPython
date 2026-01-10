import xml.etree.ElementTree as ET
import base64
import httpx
import socket
import requests
from requests.auth import HTTPDigestAuth
HIK_NS = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

def xml_text(elem, path: str):
    node = elem.find(path, HIK_NS)
    return node.text if node is not None else None

def xml_int(parent, tag):
    v = xml_text(parent, tag)
    return int(v) if v and v.isdigit() else None

def build_hik_auth(device):
    

    auth = base64.b64encode(
        f"{device.username}:{device.password}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/xml"
    }

from datetime import datetime, date

def to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise TypeError(f"Invalid date type: {type(value)}")

def to_date_str(value) -> str | None:
    d = to_date(value)
    return d.strftime("%Y-%m-%d") if d else None


def check_ip_reachable(
    ip: str,
    default_port: int = 80,
    timeout: int = 3
) -> bool:
    try:
        if ":" in ip:
            host, port = ip.rsplit(":", 1)
            port = int(port)
        else:
            host = ip
            port = default_port

        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False




def check_hikvision_auth(ip: str, username: str, password: str) -> bool:
    url = f"http://{ip}/ISAPI/System/status"
    try:
        r = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            timeout=5
        )
        return r.status_code == 200
    except Exception:
        return False
