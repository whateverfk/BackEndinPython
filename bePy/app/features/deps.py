import xml.etree.ElementTree as ET
import base64
import httpx
import socket
import requests
from requests.auth import HTTPDigestAuth
from app.core.device_crypto import decrypt_device_password


from app.core.constants import (
    HIK_XML_NAMESPACE,
    DEFAULT_IP_PORT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_AUTH_TIMEOUT
)
from app.utils.date_helpers import to_date, to_date_str

# Hikvision XML namespace for use with ElementTree
HIK_NS = HIK_XML_NAMESPACE


def xml_text(elem, path: str):
    """Extract text from XML element using Hikvision namespace"""
    node = elem.find(path, HIK_NS)
    return node.text if node is not None else None


def xml_int(parent, tag):
    """Extract integer value from XML element"""
    v = xml_text(parent, tag)
    return int(v) if v and v.isdigit() else None


def build_hik_auth(device):
    """
    Build HTTP Basic Authentication header for Hikvision ISAPI.
    """
    password = decrypt_device_password(device.password)

    auth = base64.b64encode(
        f"{device.username}:{password}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/xml"
    }


def check_ip_reachable(
    ip: str,
    default_port: int = DEFAULT_IP_PORT,
    timeout: int = DEFAULT_CONNECTION_TIMEOUT
) -> bool:
    """
    Check if an IP address (with optional port) is reachable.
    
    Args:
        ip: IP address, optionally with port (e.g., "192.168.1.1:80")
        default_port: Port to use if not specified in ip
        timeout: Connection timeout in seconds
    
    Returns:
        True if reachable, False otherwise
    
    Business Logic: UNCHANGED
    """
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
    """
    Test Hikvision device authentication.
    
    Args:
        ip: Device IP address
        username: Device username
        password: Device password
    
    Returns:
        True if authentication successful, False otherwise
    
    Business Logic: UNCHANGED
    """
    url = f"http://{ip}/ISAPI/System/status"
    try:
        r = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            timeout=DEFAULT_AUTH_TIMEOUT
        )
        
        return r.status_code == 200
    except Exception:
        return False

