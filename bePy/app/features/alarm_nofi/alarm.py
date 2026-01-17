import xml.etree.ElementTree as ET
from app.core.http_client import get_http_client
from app.Models.AlarmMessege import AlarmMessage
from app.Models.channel import Channel
from app.db.session import AsyncSessionLocal, SessionLocal



#Chưa rõ network disconnect là gì nên viết 2 cái có khả năng vào


ALLOWED_EVENT_TYPES = {
    "videoloss",
    "networkDisconnected",
    "netBroken",
    "hdFull",
    "hdError"

}
EVENT_TYPE_LABEL_MAP = {
    "videoloss": "Video Signal Loss",
    "networkDisconnected": "Network Disconnected",
    "netBroken": "Network Disconnected",
    "hdFull":"HDD Full",
    "hdError":"HDD Error"
}


XML_NS = {"ns": "http://www.hikvision.com/ver20/XMLSchema"}

# =========================
# CHANNEL NAME CACHE
# key = (ip_web, device_id)
# value = { channel_no: channel_name }
# =========================

CHANNEL_NAME_CACHE: dict[tuple[str, int], dict[int, str]] = {}


# =========================
# CACHE HELPERS
# =========================

def _cache_key(device) -> tuple[str, int]:
    return (device.ip_web, device.id)


def load_channel_name_map(device) -> dict[int, str]:
    """
    Load channel_no -> channel_name from DB
    """
    with SessionLocal() as db:
        rows = (
            db.query(Channel.channel_no, Channel.name)
            .filter(Channel.device_id == device.id)
            .all()
        )

    return {row.channel_no: row.name for row in rows}


def get_channel_name_map(device) -> dict[int, str]:
    key = _cache_key(device)

    if key not in CHANNEL_NAME_CACHE:
        CHANNEL_NAME_CACHE[key] = load_channel_name_map(device)

    return CHANNEL_NAME_CACHE[key]


def invalidate_channel_cache(device):
    CHANNEL_NAME_CACHE.pop(_cache_key(device), None)

# =========================
# ALARM STREAM LISTENER
# =========================

async def get_alarm(device, headers):
    """
    Hikvision alertStream (LONG-LIVED HTTP CONNECTION)
    """

    base_url = f"http://{device.ip_web}"
    url = f"{base_url}/ISAPI/Event/notification/alertStream"

    # debounce theo (eventType, channelID)
    active_events: dict[tuple[str, str], bool] = {}

    buffer = ""
    client = get_http_client()

    channel_name_map = get_channel_name_map(device)

    async with client.stream("GET", url, headers=headers, timeout=None) as resp:
        resp.raise_for_status()

        async for chunk in resp.aiter_text():
            if not chunk:
                continue

            buffer += chunk

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

                    if not channel_id:
                        continue

                    key = (event_type, channel_id)

                    # debounce
                    if event_state == "active":
                        if key in active_events:
                            continue          
                        active_events[key] = True

                    elif event_state == "inactive":
                       active_events.pop(key, None)

                    # convert channelID -> channel_no
                    channel_no = int(channel_id) * 100 + 1
                    channel_name = channel_name_map.get(channel_no)

                    yield {
                        "device_id": device.id,
                        "ip_web": device.ip_web,
                        "eventType": event_type,
                        "eventState": event_state,
                        "channelID": channel_id,
                        "channelName": channel_name,
                        "time": event_time,
                        "ipAddress": ip_address,
                    }

                except ET.ParseError:
                    continue
                except Exception as ex:
                    print(f"[ALERT_STREAM] Error: {ex}")
# =========================
# MESSAGE BUILDER
# =========================

def build_alarm_message(alarm: dict) -> str:
    raw_event_type = alarm["eventType"]
    event_type = EVENT_TYPE_LABEL_MAP.get(raw_event_type, raw_event_type)
    channel_id = alarm["channelID"]
    channel_name = alarm.get("channelName")
    time = alarm["time"]

    ip_web = alarm.get("ip_web")

    ip_label = f"({ip_web}) " if ip_web else ""

    

    return (
        f"{ip_label}"
        f" Event: {event_type} | "
        f"Channel Id: {channel_id} |"
        f" Channel name: {channel_name} | "
        f"Time: {time}"
    )

# =========================
# SAVE MESSAGE
# =========================




from dotenv import load_dotenv
import os

async def send_alarm_to_n8n_webhook(
    *,
    user_id: int,
    device_id: int,
   
    message: str,
):
    load_dotenv("./app/.env")
    N8N_WEBHOOK_URL=os.getenv("N8N_WEBHOOK_URL")
    payload = {
        "user_id": user_id,
        "device_id": device_id,

        # message đã build để hiển thị
        "message": message
    }
    client = get_http_client()
    try:
        resp = await client.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()

    except Exception as ex:
        print(f"[N8N WEBHOOK] Send failed: {ex}")


async def save_alarm_message_async(user_id, device_id, message: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(
                AlarmMessage(
                    user_id=user_id,
                    device_id=device_id,
                    message=message,
                )
            )
