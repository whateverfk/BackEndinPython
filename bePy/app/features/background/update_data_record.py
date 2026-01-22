import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.Models.device import Device
from app.features.RecordInfo.hikrecord import HikRecordService
from datetime import datetime, date
from app.Models.channel import Channel
from app.Models.channel_record_day import ChannelRecordDay
from app.Models.channel_record_time_range import ChannelRecordTimeRange
from app.features.RecordInfo.hikrecord import HikRecordService
from app.features.deps import build_hik_auth
from app.utils.date_helpers import to_date
from app.core.time_provider import TimeProvider
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def auto_sync_all_devices():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Device).where(Device.is_checked == True)
            )
            devices = result.scalars().all()
            
            record_service = HikRecordService()
            for device in devices:
                try:
                    await record_service.sync_device_channels_data_core(
                        db=db,
                        device=device
                    )
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(f"[SYNC ERROR] Device {device.id}: {e}")

        except Exception as e:
            logger.error(f"[SYNC ERROR] Global: {e}")


async def delete_records_before_date(db: AsyncSession, channel_id: int, before_date):
    subq = (
        select(ChannelRecordDay.id)
        .where(
            ChannelRecordDay.channel_id == channel_id,
            ChannelRecordDay.record_date < before_date
        )
        .scalar_subquery()
    )

    await db.execute(
        delete(ChannelRecordTimeRange)
        .where(
            ChannelRecordTimeRange.record_day_id.in_(subq)
        )
    )

    await db.execute(
        delete(ChannelRecordDay)
        .where(
            ChannelRecordDay.channel_id == channel_id,
            ChannelRecordDay.record_date < before_date
        )
    )


async def refresh_oldest_record_of_channel(
    db: AsyncSession,
    device,
    channel: Channel,
    headers: dict
):
    """
    Kiểm tra oldest_record_date hiện tại của channel:
    - Nếu oldest cũ không còn record → tìm oldest mới
    - Xóa record_day + time_range cũ
    - Cập nhật segment của oldest mới
    """

    hik_service = HikRecordService()

    if not channel.oldest_record_date:
        print(f"Channel {channel.channel_no} chưa có oldest_record_date, bỏ qua")
        return

    oldest_date = to_date(channel.oldest_record_date)

    today = TimeProvider().now().date()

    # 1. Kiểm tra trạng thái của oldest cũ
    status = await hik_service.record_status_of_channel(
        device,
        channel.channel_no,
        start_date=oldest_date,
        end_date=oldest_date,
        header=headers
    )

    if status and status[0]["has_record"]:
        print(f"Channel {channel.channel_no} oldest_record_date {oldest_date} vẫn còn record")
        return  # Không cần làm gì cả

    print(f"Channel {channel.channel_no} oldest_record_date {oldest_date} đã mất record, tìm oldest mới...")

    # 2. Lấy oldest mới từ device
    new_oldest = await hik_service.oldest_record_date(device, channel.channel_no, headers)
    if not new_oldest:
        print(f"Channel {channel.channel_no} không tìm thấy oldest record mới, đặt oldest_record_date = None")
        channel.oldest_record_date = None
        await db.flush()
        return

    # 3. Chuyển new_oldest về datetime.date nếu cần
    new_oldest_dt = to_date(new_oldest)


    # 4. Xóa dữ liệu cũ trước oldest mới
    await delete_records_before_date(db, channel.id, new_oldest_dt)


    await db.flush()

    # 5. Cập nhật oldest_record_date
    channel.oldest_record_date = new_oldest_dt

    # 6. Cập nhật segment cho oldest mới
    segments = await hik_service.get_time_ranges_segment(
        device,
        channel.channel_no,
        new_oldest_dt,
        headers
    )
    segments = await hik_service.merge_time_ranges(segments)

    # Tạo ChannelRecordDay mới nếu chưa có
    result = await db.execute(
        select(ChannelRecordDay).where(
            ChannelRecordDay.channel_id == channel.id,
            ChannelRecordDay.record_date == new_oldest_dt
        )
    )
    record_day = result.scalars().first()

    if not record_day:
        record_day = ChannelRecordDay(
            channel_id=channel.id,
            record_date=new_oldest_dt,
            has_record=True
        )
        db.add(record_day)
        await db.flush()

    # Xóa các segment cũ của record_day (nếu có)
    await db.execute(
        delete(ChannelRecordTimeRange).where(
            ChannelRecordTimeRange.record_day_id == record_day.id
        )
    )
    await db.flush()

    # Thêm lại segment mới
    for seg in segments:
        db.add(ChannelRecordTimeRange(
            record_day_id=record_day.id,
            start_time=seg.start_time,
            end_time=seg.end_time
        ))

    await db.flush()
    print(f"Channel {channel.channel_no} oldest_record_date đã cập nhật: {new_oldest_dt}, {len(segments)} segments mới")


async def refresh_device_oldest_records(db: AsyncSession, device):
    """
    Refresh oldest_record_date cho tất cả channel của device
    """
    headers = build_hik_auth(device)
    result = await db.execute(select(Channel).where(Channel.device_id == device.id))
    channels = result.scalars().all()
    
    for ch in channels:
        await refresh_oldest_record_of_channel(db, device, ch, headers)
