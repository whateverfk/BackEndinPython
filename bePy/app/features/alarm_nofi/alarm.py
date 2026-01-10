import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app.core.http_client import get_http_client
from app.Models.AlarmMessege import AlarmMessage
from sqlalchemy.orm import Session
from app.db.session import AsyncSessionLocal

ALLOWED_EVENT_TYPES = {
    "videoloss",
    "deviceOffline",
    "networkDisconnected",
    "netBroken",
}

XML_NS = {"ns": "http://www.hikvision.com/ver20/XMLSchema"}


async def get_alarm(
    device,
    headers,
):
    """
    Listen Hikvision alertStream (LONG-LIVED HTTP CONNECTION)
    """

    base_url = f"http://{device.ip_web}"
    url = f"{base_url}/ISAPI/Event/notification/alertStream"

    # debounce theo (eventType, channelID)
    active_events: dict[tuple[str, str], bool] = {}

    buffer = ""

    client = get_http_client()

    async with client.stream("GET", url, headers=headers, timeout=None) as resp:
        resp.raise_for_status()

        async for chunk in resp.aiter_text():
            if not chunk:
                continue

            buffer += chunk

            # xử lý khi buffer có đủ 1 XML hoàn chỉnh
            while True:
                start = buffer.find("<EventNotificationAlert")
                end = buffer.find("</EventNotificationAlert>")

                if start == -1 or end == -1:
                    break

                end += len("</EventNotificationAlert>")
                xml_str = buffer[start:end]
                buffer = buffer[end:]

                try:
                    root = ET.fromstring(xml_str)

                    event_type = root.findtext("ns:eventType", namespaces=XML_NS)
                    event_state = root.findtext("ns:eventState", namespaces=XML_NS)
                    channel_id = root.findtext("ns:channelID", namespaces=XML_NS)
                    event_time = root.findtext("ns:dateTime", namespaces=XML_NS)
                    ip_address = root.findtext("ns:ipAddress", namespaces=XML_NS)

                    if not event_type or event_type not in ALLOWED_EVENT_TYPES:
                        continue

                    key = (event_type, channel_id)

                    # debounce logic
                    if event_state == "active":
                        if key in active_events:
                            continue
                        active_events[key] = True

                    elif event_state == "inactive":
                        active_events.pop(key, None)

                    yield {
                        "device_id": device.id,
                        "eventType": event_type,
                        "eventState": event_state,
                        "channelID": channel_id,
                        "time": event_time,
                        "ipAddress": ip_address,
                    }

                except ET.ParseError:
                    # XML chưa đủ → bỏ qua
                    continue

                except Exception as ex:
                    print(f"[ALERT_STREAM] Error: {ex}")

def build_alarm_message(alarm: dict, device_name: str | None = None) -> str:
    event_type = alarm["eventType"]
    channel = alarm["channelID"]
    time = alarm["time"]
    ip = alarm["ipAddress"]

    device_label = f"[{device_name}] " if device_name else ""

    return (
        f"{device_label}"
        f"Event: {event_type} | "
        f"Channel: {channel} | "
        f"Time: {time} | "
    )

async def save_alarm_message_async(user_id, device_id, message):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(
                AlarmMessage(
                    user_id=user_id,
                    device_id=device_id,
                    message=message,
                )
            )

