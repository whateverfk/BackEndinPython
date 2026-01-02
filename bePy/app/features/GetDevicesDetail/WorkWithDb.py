from sqlalchemy import select
from app.Models.device_system_info import DeviceSystemInfo
from app.db.session import get_db
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.Models.channel_extensions import ChannelExtension
from app.Models.channel_stream_config import ChannelStreamConfig
from sqlalchemy.orm import Session
from app.Models.device_storage import DeviceStorage
from app.Models.device_integration_users import DeviceIntegrationUser
from app.Models.device_user import DeviceUser
from app.Models.user_channel_permissions import UserChannelPermission
from app.Models.user_global_permissions import UserGlobalPermission
from app.Models.channel import Channel


def saveSystemInfo(db: Session, system_info: dict):
    obj = db.execute(
        select(DeviceSystemInfo)
        .where(DeviceSystemInfo.device_id == system_info["device_id"])
    ).scalar_one_or_none()

    if obj:
        for k, v in system_info.items():
            setattr(obj, k, v)
    else:
        db.add(DeviceSystemInfo(**system_info))

    db.commit()


async def sync_channel_config(
    db: Session,
    device,
    channel,
    headers,
):
    hikservice = HikDetailService()
    # =========================
    # STREAM CONFIG
    # =========================
    stream_data = await hikservice.fetch_stream_config(device, channel, headers)
    if stream_data:
        if channel.stream_config:
            cfg = channel.stream_config
        else:
            cfg = ChannelStreamConfig(channel_id=channel.id)
            db.add(cfg)

        cfg.resolution_width = stream_data["resolution_width"]
        cfg.resolution_height = stream_data["resolution_height"]
        cfg.video_codec = stream_data["video_codec"]
        cfg.max_frame_rate = stream_data["max_frame_rate"]
        cfg.fixed_quality = stream_data["fixed_quality"]
        cfg.vbr_average_cap = stream_data["vbr_average_cap"]

    # =========================
    # MOTION DETECTION
    # =========================
    motion_enabled = await hikservice.fetch_motion_detection(device, channel, headers)

    if channel.extension:
        ext = channel.extension
    else:
        ext = ChannelExtension(channel_id=channel.id)
        db.add(ext)

    ext.motion_detect_enabled = motion_enabled

    db.flush()

# -------------------------------
# 1. Lấy thông tin từ DB
# -------------------------------
async def get_device_storage_from_db(db, device_id: int):
    """
    Lấy danh sách HDD của device từ DB.
    """
    result = db.execute(select(DeviceStorage).where(DeviceStorage.device_id == device_id))
    hdds = result.scalars().all()
    return hdds

# -------------------------------
# 2. Upsert thông tin HDD vào DB
# -------------------------------
def upsert_device_storage(
    db: Session,
    device_id: int,
    storage_list: list[dict]
):
    existing = db.execute(
        select(DeviceStorage)
        .where(DeviceStorage.device_id == device_id)
    ).scalars().all()

    existing_map = {
        h.hdd_id: h for h in existing
    }

    new_items = []

    for s in storage_list:
        hdd_id = s["hdd_id"]

        if hdd_id in existing_map:
            obj = existing_map[hdd_id]
            obj.hdd_name = s.get("hdd_name")
            obj.status = s.get("status")
            obj.hdd_type = s.get("hdd_type")
            obj.capacity = s.get("capacity")
            obj.free_space = s.get("free_space")
            obj.property = s.get("property")
        else:
            new_items.append(DeviceStorage(
                device_id=device_id,
                hdd_id=s["hdd_id"],
                hdd_name=s.get("hdd_name"),
                status=s.get("status"),
                hdd_type=s.get("hdd_type"),
                capacity=s.get("capacity"),
                free_space=s.get("free_space"),
                property=s.get("property"),
            ))

    if new_items:
        db.add_all(new_items)

    db.commit()



async def get_device_integration_users_from_db(
    db: Session,
    device_id: int
):
    result =  db.execute(
        select(DeviceIntegrationUser)
        .where(DeviceIntegrationUser.device_id == device_id)
        .order_by(DeviceIntegrationUser.user_id)
    )
    return result.scalars().all()

def upsert_device_integration_users(
    db: Session,
    device_id: int,
    users: list[dict]
):
    existing = db.execute(
        select(DeviceIntegrationUser)
        .where(DeviceIntegrationUser.device_id == device_id)
    ).scalars().all()

    existing_map = {u.user_id: u for u in existing}
    new_items = []

    for u in users:
        if u["user_id"] in existing_map:
            obj = existing_map[u["user_id"]]
            obj.username = u["username"]
            obj.level = u["level"]
        else:
            new_items.append(DeviceIntegrationUser(
                device_id=device_id,
                user_id=u["user_id"],
                username=u["username"],
                level=u["level"]
            ))

    if new_items:
        db.add_all(new_items)

    db.commit()

def upsert_device_users(
    db: Session,
    device_id: int,
    users_data: list[dict]
):
    existing = db.query(DeviceUser)\
                 .filter(DeviceUser.device_id == device_id)\
                 .all()

    existing_map = {u.user_id: u for u in existing}
    incoming_ids = set()
    new_items = []

    for u in users_data:
        incoming_ids.add(u["user_id"])

        if u["user_id"] in existing_map:
            obj = existing_map[u["user_id"]]
            obj.user_name = u["user_name"]
            obj.role = u["role"]
            obj.is_active = True
        else:
            new_items.append(DeviceUser(
                device_id=device_id,
                is_active=True,
                **u
            ))

    for obj in existing:
        if obj.user_id not in incoming_ids:
            obj.is_active = False

    if new_items:
        db.add_all(new_items)

    db.commit()



async def sync_device_users_from_isapi(
    db: Session,
    device,
    headers
):
    hik = HikDetailService()
    users = await hik.fetch_device_users(device, headers)

    if not users:
        return []

    upsert_device_users(
        db=db,
        device_id=device.id,
        users_data=users
    )

    return users


def get_device_users_from_db(
    db: Session,
    device_id: int,
    only_active: bool = True
):
    """
    Lấy danh sách user của device từ DB
    """

    query = db.query(DeviceUser).filter(
        DeviceUser.device_id == device_id
    )

    if only_active:
        query = query.filter(DeviceUser.is_active == True)

    users = query.order_by(DeviceUser.user_id.asc()).all()

    return [
        {
            "id": u.id,
            "device_id": u.device_id,
            "user_id": u.user_id,
            "user_name": u.user_name,
            "role": u.role,
            "is_active": u.is_active
        }
        for u in users
    ]


GLOBAL_PERMISSION_MAP = {
    # common
    "upgrade": "upgrade",
    "parameterConfig": "parameter_config",
    "restartOrShutdown": "restart_or_shutdown",
    "logOrStateCheck": "log_or_state_check",
    "manageChannel": "manage_channel",

    # local
    "playBack": "playback",
    "record": "record",
    "backup": "backup",

    # remote
    "preview": "preview",
    "voiceTalk": "voice_talk",
    "alarmOutOrUpload": "alarm_out_or_upload",
    "contorlLocalOut": "control_local_out",
    "transParentChannel": "transparent_channel",
}


from sqlalchemy.orm import Session
from sqlalchemy import select, delete

def save_permissions(
    db: Session,
    device_user_id: int,
    permission_data: dict
):
    try:
        # ======================================================
        # 1. LẤY DEVICE_ID (CHỈ 1 QUERY)
        # ======================================================
        device_id = db.execute(
            select(DeviceUser.device_id)
            .where(DeviceUser.id == device_user_id)
        ).scalar_one()

        # ======================================================
        # 2. RESET CHANNEL PERMISSIONS (BULK DELETE)
        # ======================================================
        db.execute(
            delete(UserChannelPermission)
            .where(UserChannelPermission.device_user_id == device_user_id)
        )

        # ======================================================
        # 3. GLOBAL PERMISSIONS (UPSERT)
        # ======================================================
        for scope in ("local", "remote"):
            global_perm = permission_data.get(scope, {}).get("global")
            if not global_perm:
                continue

            g = db.execute(
                select(UserGlobalPermission)
                .where(
                    UserGlobalPermission.device_user_id == device_user_id,
                    UserGlobalPermission.scope == scope
                )
            ).scalar_one_or_none()

            if not g:
                g = UserGlobalPermission(
                    device_user_id=device_user_id,
                    scope=scope
                )
                db.add(g)

            # reset toàn bộ field về False
            for field in GLOBAL_PERMISSION_MAP.values():
                setattr(g, field, False)

            # set theo dữ liệu ISAPI
            for xml_key, db_field in GLOBAL_PERMISSION_MAP.items():
                if xml_key in global_perm:
                    setattr(g, db_field, bool(global_perm[xml_key]))

        db.flush()

        # ======================================================
        # 4. CACHE CHANNEL (CHỈ 1 QUERY)
        # ======================================================
        channels = db.execute(
            select(Channel)
            .where(Channel.device_id == device_id)
        ).scalars().all()

        channel_map = {
            ch.channel_no: ch.id
            for ch in channels
        }

        # ======================================================
        # 5. BUILD CHANNEL PERMISSIONS (BATCH)
        # ======================================================
        channel_permissions: list[UserChannelPermission] = []

        for scope in ("local", "remote"):
            channel_scope = permission_data.get(scope, {}).get("channels", {})

            for perm, isapi_channel_ids in channel_scope.items():
                for isapi_ch_id in isapi_channel_ids:
                    channel_no = isapi_ch_id * 100 + 1
                    channel_id = channel_map.get(channel_no)

                    if not channel_id:
                        continue

                    channel_permissions.append(
                        UserChannelPermission(
                            device_user_id=device_user_id,
                            channel_id=channel_id,
                            scope=scope,
                            permission=perm,
                            enabled=True
                        )
                    )

        # ======================================================
        # 6. BULK INSERT CHANNEL PERMISSIONS
        # ======================================================
        if channel_permissions:
            db.bulk_save_objects(channel_permissions)

        db.commit()

    except Exception:
        db.rollback()
        raise
