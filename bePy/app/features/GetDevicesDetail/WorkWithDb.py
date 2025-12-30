from sqlalchemy import select
from app.Models.device_system_info import DeviceSystemInfo
from app.db.session import get_db
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.Models.channel_extensions import ChannelExtension
from app.Models.channel_stream_config import ChannelStreamConfig
from sqlalchemy.orm import Session
from app.Models.device_storage import DeviceStorage
from app.Models.device_integration_users import DeviceIntegrationUser



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