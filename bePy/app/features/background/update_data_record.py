import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.device import Device
from app.features.RecordInfo.hikrecord import HikRecordService
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.Models.channel import Channel
from app.Models.channel_record_day import ChannelRecordDay
from app.Models.channel_record_time_range import ChannelRecordTimeRange
from app.features.RecordInfo.hikrecord import HikRecordService
from app.features.deps import build_hik_auth,to_date
from app.core.time_provider import TimeProvider

async def auto_sync_all_devices():
    db: Session = SessionLocal()
    

    try:
        devices = db.query(Device).filter(
            Device.is_checked == True
        ).all()
        record_service = HikRecordService()
        for device in devices:
            try:
                await record_service.sync_device_channels_data_core(
                    db=db,
                    device=device
                )
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[SYNC ERROR] Device {device.id}: {e}")

    finally:
        db.close()

def normalize_to_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise ValueError(f"Invalid date value type: {type(value)}")


async def refresh_oldest_record_of_channel(
    db: Session,
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

        # Xóa tất cả record_day + time_range cũ
        db.query(ChannelRecordTimeRange).join(ChannelRecordDay).filter(
            ChannelRecordDay.channel_id == channel.id
        ).delete(synchronize_session=False)

        db.query(ChannelRecordDay).filter(
            ChannelRecordDay.channel_id == channel.id
        ).delete(synchronize_session=False)

        db.flush()
        return

    # 3. Chuyển new_oldest về datetime.date nếu cần
    new_oldest_dt = normalize_to_date(new_oldest)


    # 4. Xóa dữ liệu cũ trước oldest mới
    db.query(ChannelRecordTimeRange).join(ChannelRecordDay).filter(
        ChannelRecordDay.channel_id == channel.id,
        ChannelRecordDay.record_date < new_oldest_dt
    ).delete(synchronize_session=False)

    db.query(ChannelRecordDay).filter(
        ChannelRecordDay.channel_id == channel.id,
        ChannelRecordDay.record_date < new_oldest_dt
    ).delete(synchronize_session=False)

    db.flush()

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
    record_day = db.query(ChannelRecordDay).filter_by(
        channel_id=channel.id,
        record_date=new_oldest_dt
    ).first()

    if not record_day:
        record_day = ChannelRecordDay(
            channel_id=channel.id,
            record_date=new_oldest_dt,
            has_record=True
        )
        db.add(record_day)
        db.flush()

    # Xóa các segment cũ của record_day (nếu có)
    db.query(ChannelRecordTimeRange).filter(
        ChannelRecordTimeRange.record_day_id == record_day.id
    ).delete(synchronize_session=False)
    db.flush()

    # Thêm lại segment mới
    for seg in segments:
        db.add(ChannelRecordTimeRange(
            record_day_id=record_day.id,
            start_time=seg.start_time,
            end_time=seg.end_time
        ))

    db.flush()
    print(f"Channel {channel.channel_no} oldest_record_date đã cập nhật: {new_oldest_dt}, {len(segments)} segments mới")


async def refresh_device_oldest_records(db: Session, device):
    """
    Refresh oldest_record_date cho tất cả channel của device
    """
    headers = build_hik_auth(device)
    channels = db.query(Channel).filter(Channel.device_id == device.id).all()
    for ch in channels:
        await refresh_oldest_record_of_channel(db, device, ch, headers)
