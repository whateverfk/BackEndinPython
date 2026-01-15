from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, CurrentUser
from app.db.session import get_db
from app.features.Live_View.live_view import LiveView
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/api/device/{device_id}/channel/{channel_id}",
    tags=["Live"]
)
live_manager = LiveView()


@router.get("/live")
async def start_live(
    device_id: int,
    channel_id: int, 
    user: CurrentUser = Depends(get_current_user),          # user_id từ token 
    db: Session = Depends(get_db),
):
    """
    Start live HLS cho channel, trả về URL index.m3u8
    """
   
    try:
        logger.info(f"Starting HLS stream for device_id={device_id}, channel_id={channel_id}")
        result = await live_manager.acquire_channel_stream(db, device_id, channel_id, user.user_id)
        logger.info(f"HLS URL: {result['hls_url']}")
        return {"status": "ok", "hls_url": result["hls_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_live(
    device_id: int,
    channel_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Release live stream, loai bo ffmpeg nếu không còn user nào xem
    """
    try:
        user_id = user.user_id
        logger.info(f"Stopping live stream for device_id={device_id}, channel_id={channel_id}")
        await live_manager.release_channel_stream(db, device_id, channel_id, user_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/heartbeat")
async def heartbeat(
    device_id: int,
    channel_id: int,
    user: CurrentUser = Depends(get_current_user),
):
    live_manager.heartbeat(device_id, channel_id, user.user_id)
    return {"status": "ok"}
