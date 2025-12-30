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


async def saveSystemInfo(db, system_info: dict):
    stmt = select(DeviceSystemInfo).where(
        DeviceSystemInfo.device_id == system_info["device_id"]
    )
    result =  db.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj:
        # update
        obj.model = system_info["model"]
        obj.serial_number = system_info["serial_number"]
        obj.firmware_version = system_info["firmware_version"]
        obj.mac_address = system_info["mac_address"]
    else:
        # insert
        obj = DeviceSystemInfo(**system_info)
        db.add(obj)

    await db.commit()


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
async def upsert_device_storage(db, device_id: int, storage_list: list[dict]):
    """
    Lưu hoặc cập nhật thông tin HDD vào DB.
    
    Args:
        db: AsyncSession
        device_id: ID device
        storage_list: danh sách dict, mỗi dict có keys tương ứng DeviceStorage
    """
    for storage in storage_list:
        # Kiểm tra xem HDD đã tồn tại chưa
        result =  db.execute(
            select(DeviceStorage).where(
                DeviceStorage.device_id == device_id,
                DeviceStorage.hdd_id == storage["hdd_id"]
            )
        )
        existing = result.scalars().first()

        if existing:
            # Update các field
            existing.hdd_name = storage.get("hdd_name", existing.hdd_name)
            existing.status = storage.get("status", existing.status)
            existing.hdd_type = storage.get("hdd_type", existing.hdd_type)
            existing.capacity = storage.get("capacity", existing.capacity)
            existing.free_space = storage.get("free_space", existing.free_space)
            existing.property = storage.get("property", existing.property)
        else:
            # Insert mới
            new_hdd = DeviceStorage(
                device_id=device_id,
                hdd_id=storage.get("hdd_id"),
                hdd_name=storage.get("hdd_name", ""),
                status=storage.get("status", ""),
                hdd_type=storage.get("hdd_type", ""),
                capacity=storage.get("capacity", 0),
                free_space=storage.get("free_space", 0),
                property=storage.get("property", "")
            )
            db.add(new_hdd)

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

async def upsert_device_integration_users(
    db: Session,
    device_id: int,
    users: list[dict]
):
    for u in users:
        result = db.execute(
            select(DeviceIntegrationUser).where(
                DeviceIntegrationUser.device_id == device_id,
                DeviceIntegrationUser.user_id == u["user_id"]
            )
        )
        existing = result.scalars().first()

        if existing:
            existing.username = u["username"]
            existing.level = u["level"]
        else:
            db.add(DeviceIntegrationUser(
                device_id=device_id,
                user_id=u["user_id"],
                username=u["username"],
                level=u["level"]
            ))

    db.commit()


async def upsert_device_users(
    db: Session,
    device_id: int,
    users_data: list[dict]
):
    """
    Upsert users của device vào DB
    """

    existing_users = db.query(DeviceUser).filter(
        DeviceUser.device_id == device_id
    ).all()

    existing_map = {
        u.user_id: u for u in existing_users
    }

    incoming_ids = set()

    for u in users_data:
        incoming_ids.add(u["user_id"])

        if u["user_id"] in existing_map:
            # UPDATE
            db_user = existing_map[u["user_id"]]
            db_user.user_name = u["user_name"]
            db_user.role = u["role"]
            db_user.is_active = True
        else:
            # INSERT
            db_user = DeviceUser(
                device_id=device_id,
                user_id=u["user_id"],
                user_name=u["user_name"],
                role=u["role"],
                is_active=True
            )
            db.add(db_user)

    # disable users không còn tồn tại trên device
    for db_user in existing_users:
        if db_user.user_id not in incoming_ids:
            db_user.is_active = False

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


def save_permissions(db: Session, device_user_id: int, permission_data: dict):
    """
    Lưu permissions cho device_user với debug để biết lỗi
    """

    try:
        print(f"[DEBUG] Start saving permissions for device_user_id={device_user_id}")

        # ===== GLOBAL =====
        for scope in ["local", "remote"]:
            global_perm = permission_data.get(scope, {}).get("global")
            if not global_perm:
                print(f"[DEBUG] No global permission for scope={scope}")
                continue

            g = db.query(UserGlobalPermission).filter_by(
                device_user_id=device_user_id,
                scope=scope
            ).first()

            if g:
                print(f"[DEBUG] Updating existing global permission for scope={scope}")
                g.upgrade = global_perm.get("upgrade")
                g.parameter_config = global_perm.get("parameter_config")
                g.restart_or_shutdown = global_perm.get("restart_or_shutdown")
                g.log_or_state_check = global_perm.get("log_or_state_check")
                g.manage_channel = global_perm.get("manage_channel")
                g.playback = global_perm.get("playBack")
                g.record = global_perm.get("record")
                g.backup = global_perm.get("backup")
                g.preview = global_perm.get("preview")
                g.voice_talk = global_perm.get("voiceTalk")
                g.alarm_out_or_upload = global_perm.get("alarmOutOrUpload")
                g.control_local_out = global_perm.get("contorlLocalOut")
                g.transparent_channel = global_perm.get("transParentChannel")
            else:
                print(f"[DEBUG] Inserting new global permission for scope={scope}")
                g = UserGlobalPermission(
                    device_user_id=device_user_id,
                    scope=scope,
                    upgrade=global_perm.get("upgrade"),
                    parameter_config=global_perm.get("parameter_config"),
                    restart_or_shutdown=global_perm.get("restart_or_shutdown"),
                    log_or_state_check=global_perm.get("log_or_state_check"),
                    manage_channel=global_perm.get("manage_channel"),
                    playback=global_perm.get("playBack"),
                    record=global_perm.get("record"),
                    backup=global_perm.get("backup"),
                    preview=global_perm.get("preview"),
                    voice_talk=global_perm.get("voiceTalk"),
                    alarm_out_or_upload=global_perm.get("alarmOutOrUpload"),
                    control_local_out=global_perm.get("contorlLocalOut"),
                    transparent_channel=global_perm.get("transParentChannel"),
                )
                db.add(g)

        db.flush()
        print("[DEBUG] Flushed global permissions")

        # ===== CHANNEL =====
        for scope in ["local", "remote"]:
            channels = permission_data.get(scope, {}).get("channels", {})

            for perm, channel_ids in channels.items():
                for isapi_ch_id in channel_ids:

                    channel_no = isapi_ch_id * 100 + 1
                    device_id = db.query(DeviceUser.device_id).filter_by(id=device_user_id).scalar()
                    channel = db.query(Channel).filter_by(
                        device_id=device_id,
                        channel_no=channel_no
                    ).first()

                    if not channel:
                        print(f"[WARN] Channel not found: device_user_id={device_user_id}, isapi_id={isapi_ch_id}, channel_no={channel_no}")
                        continue

                    ucp = db.query(UserChannelPermission).filter_by(
                        device_user_id=device_user_id,
                        channel_id=channel.id,
                        scope=scope,
                        permission=perm
                    ).first()

                    if ucp:
                        print(f"[DEBUG] Updating existing channel permission: channel_id={channel.id}, permission={perm}")
                        ucp.enabled = True
                    else:
                        print(f"[DEBUG] Adding new channel permission: channel_id={channel.id}, permission={perm}")
                        ucp = UserChannelPermission(
                            device_user_id=device_user_id,
                            channel_id=channel.id,
                            scope=scope,
                            permission=perm,
                            enabled=True
                        )
                        db.add(ucp)

        db.commit()
        print("[DEBUG] Commit successful")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception while saving permissions for device_user_id={device_user_id}: {e}")
        raise
