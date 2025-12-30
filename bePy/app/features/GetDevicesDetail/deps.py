import xml.etree.ElementTree as ET

HIK_NS = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

def xml_text(elem, path: str):
    node = elem.find(path, HIK_NS)
    return node.text if node is not None else None
