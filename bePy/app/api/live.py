# app/api/live.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import subprocess
from app.api.deps import get_current_user, CurrentUser
from app.db.session import get_db
from app.features.Live_View.live_view import LiveView  # class LiveView bạn đã có

router = APIRouter( prefix="/api/device/{device_id}/channel/{channel_id}",
    tags=["Live"])
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
    user_id = user.user_id
    try:
        print("start lấy hls and shit")
        result = await live_manager.acquire_channel_stream(db, device_id, channel_id)
        print( result["hls_url"] )
        return {"status": "ok", "hls_url": result["hls_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_live(
    device_id: int,
    channel_id: int,
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Release live stream, terminate ffmpeg nếu không còn user nào xem
    """
    try:
        live_manager.release_channel_stream(db, user_id, device_id, channel_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
