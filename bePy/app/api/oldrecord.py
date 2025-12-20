from fastapi import APIRouter, Depends, HTTPException
from app.api.device import get_devices

router = APIRouter(prefix="/api/oldrecord", tags=["Record"])

# =========================
# GET: api/sync/oldrecord
# =========================
@router.get("/oldrecord")
def get_setting(
    
):
    return {"message": "Old record endpoint"}
    
    
