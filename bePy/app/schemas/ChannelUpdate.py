from pydantic import BaseModel

class ChannelUpdateSchema(BaseModel):
    channel_name: str
    motion_detect: bool

    resolution_width: int
    resolution_height: int
    video_codec: str
    max_frame_rate: int
    fixed_quality: int
    vbr_average_cap: int
    h265_plus: bool
    vbr_upper_cap:int