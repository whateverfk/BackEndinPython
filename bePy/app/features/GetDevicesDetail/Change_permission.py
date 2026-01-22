
from app.Models.channel import Channel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from app.Models.device_user import DeviceUser


# Trong file service hoặc utils

async def get_channel_map_from_device(db: AsyncSession, device_id: int) -> dict:
    """
    Lấy danh sách channel từ device và tạo map: channel.id -> (channel_no - 1) / 100
    
    Args:
        db: Database session
        device_id: ID của device
        
    Returns:
        dict: {channel_id: calculated_value}
        Ví dụ: {1: 10, 2: 20, 3: 10} với channel_no tương ứng là 1001, 2001, 1001
    """
    result = await db.execute(select(Channel).filter(
        Channel.device_id == device_id
    ))
    channels = result.scalars().all()
    
    channel_map = {}
    for ch in channels:
        channel_map[ch.id] = (ch.channel_no - 1) // 100
    
    return channel_map


# có thể không dùng tới 
def get_channels_list_from_device(db: Session, device_id: int) -> list:
    """
    Lấy danh sách channel từ device với đầy đủ thông tin
    
    Args:
        db: Database session
        device_id: ID của device
        
    Returns:
        list: [{"id": 1, "channel_no": 1001, "calculated_value": 10, "name": "..."}, ...]
    """
    channels = db.query(Channel).filter(
        Channel.device_id == device_id
    ).all()
    
    result = []
    for ch in channels:
        result.append({
            "id": ch.id,
            "channel_no": ch.channel_no,
            "calculated_value": (ch.channel_no - 1) // 100,
            "name": ch.name
        })
    
    return result



def create_video_channel_permission_list_xml(
    scope: str,  # "local" hoặc "remote"
    channels_data: dict,  # {"playback": [1, 3], "record": [1], "backup": [1, 2, 3]}
    channel_map: dict  # {channel_id: channel_no_value}
) -> Element:
    """
    Tạo videoChannelPermissionList XML element
    
    Args:
        scope: "local" hoặc "remote"
        channels_data: Dict chứa danh sách channel_id cho mỗi permission
        channel_map: Map từ channel.id -> (channel_no - 1) // 100
        
    Returns:
        Element: videoChannelPermissionList element
    """
    list_elem = Element("videoChannelPermissionList")
    
    # Lấy tất cả channel IDs từ map
    all_channel_ids = sorted(channel_map.keys())
    
    for ch_id in all_channel_ids:
        perm_elem = SubElement(list_elem, "videoChannelPermission")
        
        # ID trong XML là giá trị calculated từ channel_no
        SubElement(perm_elem, "id").text = str(channel_map[ch_id])
        
        # Kiểm tra permissions cho scope local
        if scope == "local":
            playback_enabled = ch_id in channels_data.get("playback", [])
            record_enabled = ch_id in channels_data.get("record", [])
            backup_enabled = ch_id in channels_data.get("backup", [])
            
            SubElement(perm_elem, "playBack").text = str(playback_enabled).lower()
            SubElement(perm_elem, "record").text = str(record_enabled).lower()
            SubElement(perm_elem, "backup").text = str(backup_enabled).lower()
        
        # Kiểm tra permissions cho scope remote
        elif scope == "remote":
            preview_enabled = ch_id in channels_data.get("preview", [])
            record_enabled = ch_id in channels_data.get("record", [])
            playback_enabled = ch_id in channels_data.get("playback", [])
            
            SubElement(perm_elem, "preview").text = str(preview_enabled).lower()
            SubElement(perm_elem, "record").text = str(record_enabled).lower()
            SubElement(perm_elem, "playBack").text = str(playback_enabled).lower()
    
    return list_elem


def create_ptz_channel_permission_list_xml(
    channels_data: dict,  # {"ptz_control": [1, 4]}
    channel_map: dict  # {channel_id: channel_no_value}
) -> Element:
    """
    Tạo ptzChannelPermissionList XML element
    
    Args:
        channels_data: Dict chứa danh sách channel_id có ptz_control
        channel_map: Map từ channel.id -> (channel_no - 1) // 100
        
    Returns:
        Element: ptzChannelPermissionList element
    """
    list_elem = Element("ptzChannelPermissionList")
    
    # Lấy tất cả channel IDs từ map
    all_channel_ids = sorted(channel_map.keys())
    ptz_enabled_ids = channels_data.get("ptz_control", [])
    
    for ch_id in all_channel_ids:
        perm_elem = SubElement(list_elem, "ptzChannelPermission")
        
        # ID trong XML là giá trị calculated từ channel_no
        SubElement(perm_elem, "id").text = str(channel_map[ch_id])
        
        # Kiểm tra xem channel này có ptz_control không
        ptz_enabled = ch_id in ptz_enabled_ids
        SubElement(perm_elem, "ptzControl").text = str(ptz_enabled).lower()
    
    return list_elem


async def create_user_permission_xml(
    db: AsyncSession,
    device_id: int,
    device_user_id: int,
    payload: dict  # Payload từ frontend
) -> str:
    """
    Tạo XML UserPermission hoàn chỉnh từ payload frontend
    
    Args:
        db: Database session
        device_id: ID của device
        device_user_id: ID của device_user
        payload: {
            "device_id": 1,
            "device_user_id": 5,
            "permissions": {
                "local": {
                    "global": {"upgrade": false, "parameter_config": true, ...},
                    "channels": {"playback": [1, 3], "record": [1], ...}
                },
                "remote": {...}
            }
        }
        
    Returns:
        str: XML string 
    """
    # Lấy thông tin device_user
    result = await db.execute(select(DeviceUser).filter(
        DeviceUser.id == device_user_id
    ))
    device_user = result.scalars().first()
    
    if not device_user:
        raise ValueError(f"DeviceUser {device_user_id} not found")
    
    # Lấy channel map
    channel_map = await get_channel_map_from_device(db, device_id)
    
    # Lấy permissions từ payload
    permissions = payload.get("permissions", {})
    local_perm = permissions.get("local", {})
    remote_perm = permissions.get("remote", {})
    
    local_global = local_perm.get("global", {})
    local_channels = local_perm.get("channels", {})
    
    remote_global = remote_perm.get("global", {})
    remote_channels = remote_perm.get("channels", {})
    
    # Tạo root element
    root = Element("UserPermission")
    
    # Thông tin user
    SubElement(root, "id").text = str(device_user.user_id)
    SubElement(root, "userID").text = str(device_user.user_id)
    SubElement(root, "userType").text = device_user.role or "viewer"
    
    # ===== LOCAL PERMISSION =====
    local_elem = SubElement(root, "localPermission")
    
    # Global permissions - local
    SubElement(local_elem, "upgrade").text = str(local_global.get("upgrade", False)).lower()
    SubElement(local_elem, "parameterConfig").text = str(local_global.get("parameter_config", False)).lower()
    SubElement(local_elem, "restartOrShutdown").text = str(local_global.get("restart_or_shutdown", False)).lower()
    SubElement(local_elem, "logOrStateCheck").text = str(local_global.get("log_or_state_check", False)).lower()
    SubElement(local_elem, "manageChannel").text = str(local_global.get("manage_channel", False)).lower()
    
    # Channel-based global flags (có ít nhất 1 channel enabled)
    SubElement(local_elem, "playBack").text = str(len(local_channels.get("playback", [])) > 0).lower()
    SubElement(local_elem, "record").text = str(len(local_channels.get("record", [])) > 0).lower()
    SubElement(local_elem, "ptzControl").text = str(len(local_channels.get("ptz_control", [])) > 0).lower()
    SubElement(local_elem, "backup").text = str(len(local_channels.get("backup", [])) > 0).lower()
    
    # Video channel permission list - local
    video_list_local = create_video_channel_permission_list_xml(
        "local", local_channels, channel_map
    )
    local_elem.append(video_list_local)
    
    # PTZ channel permission list - local
    ptz_list_local = create_ptz_channel_permission_list_xml(
        local_channels, channel_map
    )
    local_elem.append(ptz_list_local)
    
    # ===== REMOTE PERMISSION =====
    remote_elem = SubElement(root, "remotePermission")
    
    # Global permissions - remote
    SubElement(remote_elem, "parameterConfig").text = str(remote_global.get("parameter_config", False)).lower()
    SubElement(remote_elem, "logOrStateCheck").text = str(remote_global.get("log_or_state_check", False)).lower()
    SubElement(remote_elem, "upgrade").text = str(remote_global.get("upgrade", False)).lower()
    SubElement(remote_elem, "voiceTalk").text = str(remote_global.get("voice_talk", False)).lower()
    SubElement(remote_elem, "restartOrShutdown").text = str(remote_global.get("restart_or_shutdown", False)).lower()
    SubElement(remote_elem, "alarmOutOrUpload").text = str(remote_global.get("alarm_out_or_upload", False)).lower()
    SubElement(remote_elem, "contorlLocalOut").text = str(remote_global.get("control_local_out", False)).lower()
    SubElement(remote_elem, "transParentChannel").text = str(remote_global.get("transparent_channel", False)).lower()
    SubElement(remote_elem, "manageChannel").text = str(remote_global.get("manage_channel", False)).lower()
    
    # Channel-based global flags - remote
    SubElement(remote_elem, "preview").text = str(len(remote_channels.get("preview", [])) > 0).lower()
    SubElement(remote_elem, "record").text = str(len(remote_channels.get("record", [])) > 0).lower()
    SubElement(remote_elem, "ptzControl").text = str(len(remote_channels.get("ptz_control", [])) > 0).lower()
    SubElement(remote_elem, "playBack").text = str(len(remote_channels.get("playback", [])) > 0).lower()
    
    # Video channel permission list - remote
    video_list_remote = create_video_channel_permission_list_xml(
        "remote", remote_channels, channel_map
    )
    remote_elem.append(video_list_remote)
    
    # PTZ channel permission list - remote
    ptz_list_remote = create_ptz_channel_permission_list_xml(
        remote_channels, channel_map
    )
    remote_elem.append(ptz_list_remote)
    
    # Convert to pretty XML string
    xml_str = tostring(root, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    # Remove XML declaration và empty lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines[1:])  # Skip XML declaration

pay_load_vi_du={
  "device_id": 44,
  "device_user_id": 175,
  "permissions": {
    "local": {
      "global": {
        "upgrade": True,
        "parameter_config": True,
        "restart_or_shutdown": False,
        "log_or_state_check": False,
        "manage_channel": True,
        "playback": True,
        "record": True,
        "backup": True,
        "preview": False,
        "voice_talk": False,
        "alarm_out_or_upload": False,
        "control_local_out": False,
        "transparent_channel": False
      },
      "channels": {
        "playback": [
          248,
          253,
          256
        ],
        "backup": [
          248,
          249,
          250,
          255,
          256,
          257
        ],
        "record": [
          254
        ],
        "ptz_control": [
          248
        ]
      }
    },
    "remote": {
      "global": {
        "upgrade": False,
        "parameter_config": False,
        "restart_or_shutdown": False,
        "log_or_state_check": False,
        "manage_channel": False,
        "playback": True,
        "record": False,
        "backup": False,
        "preview": True,
        "voice_talk": True,
        "alarm_out_or_upload": False,
        "control_local_out": True,
        "transparent_channel": False
      },
      "channels": {
        "preview": [
          248,
          249,
          250,
          251,
          252,
          253,
          254,
          255,
          256
        ],
        "playback": [],
        "ptz_control": [
          251,
          257
        ]
      }
    }
  }
}
