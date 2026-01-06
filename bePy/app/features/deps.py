import xml.etree.ElementTree as ET
import base64
import httpx

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
