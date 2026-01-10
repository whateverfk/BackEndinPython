import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app.core.http_client import get_http_client

MINOR_DISPLAY_MAP = {
    # Alarm
    "alarmOut": "Alarm Output",
    "alarmIn": "Alarm Input",

    
    "motionStart": "Start Motion Detection",
    "motionStop": "Stop Motion Detection",

    "hideStart": "Start Video Tampering",
    "hideStop": "Stop Video Tampering",

    "vcaStart": "Start VCA Alarm",
    "vcaStop": "Stop VCA Alarm",
    "remoteLogin": "Remote: Login",
    "remoteLogout": "Remote: Logout",

    "lineDetectionStart": "Line Crossing Detection Started",
    "lineDetectionStop": "Line Crossing Detection Stopped",
    "fieldDetectionStart": "Intrusion Detection Started",
    "fieldDetectionStop": "Intrusion Detection Stop",
    "audioInputExceptionStart":"Audio Input Exception Started",
    "audioInputExceptionStop":"Audio Input Exception Stop",
    "soundIntensityMutationStart":"Sudden change of Sound Intensity Detection Started",
    "soundIntensityMutationStop":"Sudden change of Sound Intensity Detection Stop",


    #information
    "runStatusInfo":"System Running State",
    "hddInfo":"HDD information",

    #exception
    "ipcDisconnect":"IP Camera Disconnect",
    "videoLost":"Video Signal Loss",
    "illlegealAccess":"Illegal Login",
    "netBroken":"Network Disconnected",
    "recordError":"Record/Capture Error",
    "hdFull":"HDD Full",
    "hdError":"HDD Error",
    "ipConflict":"IP Address Conflicted",
    "videoException":"Video Signal Exception",
    "videoFormatMismatch":"Input/Output Video Standard Mismatch",
    "ipcIpConfilict":"Ip Address of IPC Conflict"

}


def map_minor_display(minor: str) -> str:
    if not minor:
        return ""
    return MINOR_DISPLAY_MAP.get(minor, minor)



async def fetch_isapi_logs(
    device,
    headers,
    from_time: str,
    to_time: str,
    max_results: int,
    major_type: str = "ALL"
):
    """
    Fetch logs from Hikvision ISAPI logSearch with auto pagination
    """

    base_url = f"http://{device.ip_web}"
    url = f"{base_url}/ISAPI/ContentMgmt/logSearch"

    NS = {"ns": "urn:psialliance-org"}

    # ---- build metaId ----
    if major_type.upper() == "ALL":
        meta_id = "log.std-cgi.com"
    else:
        meta_id = f"log.std-cgi.com/{major_type}"

    # ---- convert time to Z ----
    def to_utc_z(t: str) -> str:
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    start_time = to_utc_z(from_time)
    end_time = to_utc_z(to_time)

    search_id = str(uuid.uuid4()).upper()
    position = 0
    remaining = max_results

    results = []

    try:
        while remaining > 0:
            # ---- build payload ----
            payload = f"""<?xml version="1.0" encoding="utf-8"?>
<CMSearchDescription>
    <searchID>{search_id}</searchID>
    <metaId>{meta_id}</metaId>
    <timeSpanList>
        <timeSpan>
            <startTime>{start_time}</startTime>
            <endTime>{end_time}</endTime>
        </timeSpan>
    </timeSpanList>
    <maxResults>{remaining}</maxResults>
    <searchResultPostion>{position}</searchResultPostion>
</CMSearchDescription>
"""
            self = get_http_client()
            resp = await self.post(
                url,
                headers=headers,
                content=payload
            )
            resp.raise_for_status()

            root = ET.fromstring(resp.text)

            status = root.findtext("ns:responseStatusStrg", namespaces=NS)
            num_matches = int(
                root.findtext("ns:numOfMatches", default="0", namespaces=NS)
            )

            # ---- parse logs ----
            for item in root.findall(
                "ns:matchList/ns:searchMatchItem", NS
            ):
                desc = item.find("ns:logDescriptor", NS)
                if desc is None:
                    continue

                meta = desc.findtext("ns:metaId", namespaces=NS) or ""
                path = meta.replace("log.hikvision.com/", "")
                parts = path.split("/")

                major = parts[0] if len(parts) > 0 else ""
                minor = parts[1] if len(parts) > 1 else ""
                meta_index = parts[2] if len(parts) > 2 else ""


                results.append({
                    "time": desc.findtext("ns:StartDateTime", namespaces=NS),
                    "majorType": major,
                    #"minorType": minor,
                    "minorType": map_minor_display(minor),
                    "localId": desc.findtext("ns:localId", namespaces=NS),
                    "userName": desc.findtext("ns:userName", namespaces=NS),
                    "ipAddress": desc.findtext("ns:ipAddress", namespaces=NS),
                })

            remaining -= num_matches
            position += num_matches

            # ---- stop condition ----
            if status == "OK" or num_matches == 0:
                break

        return {
            "device_id": device.id,
            "total": len(results),
            "logs": results
        }

    except Exception as ex:
        print(f"[ISAPI][LOG_SEARCH] Error fetching logs: {ex}")
        return None
