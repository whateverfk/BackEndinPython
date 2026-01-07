import ffmpeg
import xml.etree.ElementTree as ET
import urllib.parse
import subprocess
from sqlalchemy.orm import Session
from app.core.http_client import get_http_client
from app.features.deps import build_hik_auth
from app.Models.user import User
from app.Models.device import Device
from app.Models.channel import Channel
import psutil
import threading
import time
import os


class LiveView:
    HLS_ROOT = r"D:\Hls"
    HLS_URL_PREFIX = "/hls"

    def __init__(self):
        self.client = get_http_client()
        self.running_streams = {} 

    # =========================
    # RTSP PORT
    # =========================
    async def get_rtsp_port(self, device, headers) -> int:
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/Security/adminAccesses"

        try:
            resp = await self.client.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return 554

            root = ET.fromstring(resp.text)
            ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

            for proto in root.findall(".//hik:AdminAccessProtocol", ns):
                protocol = proto.find("hik:protocol", ns)
                port = proto.find("hik:portNo", ns)
                enabled = proto.find("hik:enabled", ns)

                if protocol is not None and protocol.text.upper() == "RTSP":
                    if enabled is None or enabled.text.lower() == "true":
                        return int(port.text)

            return 554

        except Exception:
            return 554

    # =========================
    # HLS PATH
    # =========================
    def build_hls_output_path(self, user_id, device_id, channel_id) -> str:
        dir_path = os.path.join(
            self.HLS_ROOT,
            f"user_{user_id}",
            f"device_{device_id}",
            f"channel_{channel_id}",
        )
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, "index.m3u8")


    def build_hls_url(self, user_id, device_id, channel_id) -> str:
        """
        Trả về URL HTTP để frontend load HLS
        """
        return f"{self.HLS_URL_PREFIX}/user_{user_id}/device_{device_id}/channel_{channel_id}/index.m3u8"

    # =========================
    # BUILD FFmpeg PIPELINE
    # =========================
    async def build_ffmpeg_hls_process(
        self,
        db: Session,
        user_id: str,
        device_id: int,
        channel_id: int,
    ):
        # -------- LOAD DATA --------
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        if not user:
            raise Exception("User not found")

        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise Exception("Device not found")

        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.device_id == device.id,
            Channel.is_active == True
        ).first()
        if not channel:
            raise Exception("Channel not found")

        headers = build_hik_auth(device)

        # -------- RTSP URL --------
        rtsp_port = await self.get_rtsp_port(device=device, headers=headers)  # <-- await added
        ip = device.ip_nvr or device.ip_web

        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)

        rtsp_url = (
            f"rtsp://{username}:{password}"
            f"@{ip}:{rtsp_port}"
            f"/ISAPI/Streaming/channels/{channel.channel_no}"
        )

        # -------- STREAM CONFIG --------
        cfg = channel.stream_config
        fps = cfg.max_frame_rate / 100 if cfg and cfg.max_frame_rate else 20
        gop = int(fps)

        # -------- OUTPUT --------
        output_path = self.build_hls_output_path(
            user_id, device_id, channel_id
        )

        # =========================
        # FFmpeg PIPELINE
        # =========================
        stream = (
            ffmpeg.
            input(
                rtsp_url,
                rtsp_transport="tcp",
                fflags="genpts+nobuffer",
                flags="low_delay",
                analyzeduration=5000000,  # 5s
                probesize=1000000,        # 1 MB
            )
            .output(
                output_path,
                format="hls",
                vcodec="libx264",
                preset="ultrafast",
                tune="zerolatency",
                pix_fmt="yuv420p",
                g=gop,
                keyint_min=gop,
                sc_threshold=0,
                hls_time=1,
                hls_list_size=2,
                hls_flags="delete_segments+independent_segments",
                hls_allow_cache=0,
                map="0:v:0",
                **{"profile:v": "baseline", "level": "4.1"}
            )
        )

        return stream, rtsp_url
  
   

    async def acquire_channel_stream(self, db: Session, user_id: str, device_id: int, channel_id: int) -> dict:
        """
        Start ffmpeg process nếu chưa chạy, trả về HTTP HLS URL
        """
        # Build FFmpeg pipeline + RTSP URL
        stream, rtsp_url = await self.build_ffmpeg_hls_process(db, user_id, device_id, channel_id)

        # Nếu stream đã chạy → tăng refcount
        if rtsp_url in self.running_streams:
            self.running_streams[rtsp_url]["refcount"] += 1
            print(f"Stream {rtsp_url} already running, refcount = {self.running_streams[rtsp_url]['refcount']}")
        else:
            print("Starting FFmpeg for:", rtsp_url)

            # ------------------------
            # 1️⃣ Compile FFmpeg command
            # ------------------------
            cmd = stream.compile()
            print("FFmpeg command:", " ".join(cmd))  # <-- debug command xem đúng chưa

            # ------------------------
            # 2️⃣ Spawn FFmpeg process
            # ------------------------
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.running_streams[rtsp_url] = {"proc": proc, "refcount": 1}

            # ------------------------
            # 3️⃣ Log FFmpeg output (stderr) để check có chạy hay không
            # ------------------------
            def log_ffmpeg(p):
                for line in p.stderr:
                    print("[FFMPEG]", line.decode(errors="ignore"))

            threading.Thread(target=log_ffmpeg, args=(proc,), daemon=True).start()

            # ------------------------
            # 4️⃣ Check PID sống không
            # ------------------------
            time.sleep(0.5)  # đợi FFmpeg khởi động
            if psutil.pid_exists(proc.pid):
                print(f"FFmpeg process is running, PID={proc.pid}")
            else:
                print("FFmpeg process failed to start!")

            # ------------------------
            # 5️⃣ Check HLS file đã tạo chưa
            # ------------------------
            output_path = self.build_hls_output_path(user_id, device_id, channel_id)
            for _ in range(5):
                if os.path.exists(output_path):
                    print("HLS index.m3u8 đã tạo")
                    break
                time.sleep(0.5)
            else:
                print("HLS file chưa tạo – FFmpeg có thể bị lỗi")

        # Trả về URL HTTP
        hls_url = self.build_hls_url(user_id, device_id, channel_id)
        return {"hls_url": hls_url}



    def release_channel_stream(self, db: Session, user_id: str, device_id: int, channel_id: int):
        # Lấy RTSP URL tương ứng
        stream = self.build_ffmpeg_hls_process(db, user_id, device_id, channel_id)
        rtsp_url = stream.get_args()[2]

        info = self.running_streams.get(rtsp_url)
        if not info:
            return

        # Giảm refcount → terminate nếu = 0
        info["refcount"] -= 1
        if info["refcount"] <= 0:
            info["proc"].terminate()
            try:
                info["proc"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                info["proc"].kill()
            del self.running_streams[rtsp_url]
