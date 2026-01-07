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
    # HLS PATH (theo IP + channel_no)
    # =========================
    def build_hls_output_path(self, device_ip: str, channel_no: int) -> str:
        """
        Tạo đường dẫn HLS dựa trên IP thiết bị + channel_no.
        Nếu file index.m3u8 chưa tồn tại, tạo placeholder rỗng hợp lệ.
        """
        # Thay dấu : trong IP để tránh lỗi tên folder
        safe_ip = device_ip.replace(":", "_")
        dir_path = os.path.join(self.HLS_ROOT, f"{safe_ip}", f"channel_{channel_no}")
        os.makedirs(dir_path, exist_ok=True)

        output_file = os.path.join(dir_path, "index.m3u8")

        # Nếu file chưa tồn tại → tạo placeholder
        if not os.path.exists(output_file):
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
            except Exception as e:
                print(f"Không thể tạo placeholder HLS: {e}")

        return output_file



    def build_hls_url(self, device_ip: str, channel_no: int) -> str:
        """
        URL frontend sẽ load HLS
        """
        safe_ip = device_ip.replace(":", "_")
        return f"{self.HLS_URL_PREFIX}/{safe_ip}/channel_{channel_no}/index.m3u8"

    # =========================
    # BUILD FFmpeg PIPELINE
    # =========================
    async def build_ffmpeg_hls_process(
        self,
        db: Session,
        device_id: int,
        channel_id: int,
    ):
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

        # RTSP
        rtsp_port = await self.get_rtsp_port(device=device, headers=headers)
        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"

        # Stream config
        cfg = channel.stream_config
        fps = cfg.max_frame_rate / 100 if cfg and cfg.max_frame_rate else 20
        gop = int(fps)

        # Output path
        output_path = self.build_hls_output_path(ip, channel.channel_no)

        # FFmpeg pipeline
        stream = (
            ffmpeg
            .input(
                rtsp_url,
                rtsp_transport="tcp",
                fflags="genpts",
                flags="low_delay",
                analyzeduration=2000000,
                probesize=500000,
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
                profile="baseline",
                level="4.1",
                hls_time=1,
                hls_list_size=3,
                hls_flags="delete_segments+independent_segments",
                hls_allow_cache=0,
                map="0:v:0",
                err_detect="ignore_err"  # bỏ qua NALU lỗi
            )
        )

        return stream, rtsp_url, ip, channel.channel_no

    # =========================
    # ACQUIRE STREAM
    # =========================
    async def acquire_channel_stream(self, db: Session, device_id: int, channel_id: int) -> dict:
        stream, rtsp_url, ip, channel_no = await self.build_ffmpeg_hls_process(db, device_id, channel_id)

        if rtsp_url in self.running_streams:
            self.running_streams[rtsp_url]["refcount"] += 1
        else:
            cmd = stream.compile()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.running_streams[rtsp_url] = {"proc": proc, "refcount": 1}

            def log_ffmpeg(p):
                for line in p.stderr:
                    print("[FFMPEG]", line.decode(errors="ignore"))

            threading.Thread(target=log_ffmpeg, args=(proc,), daemon=True).start()
            time.sleep(0.5)

        hls_url = self.build_hls_url(ip, channel_no)
        return {"hls_url": hls_url}

