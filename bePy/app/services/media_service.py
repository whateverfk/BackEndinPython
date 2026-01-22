import ffmpeg
import aiofiles
import xml.etree.ElementTree as ET
import urllib.parse
import threading
import subprocess
import os
import shutil
import time
import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, Set
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.http_client import get_http_client
from app.features.deps import build_hik_auth
from app.Models.device import Device
from app.Models.channel import Channel
from app.core.device_crypto import decrypt_device_password
from app.core.logger import app_logger

load_dotenv()
HLS_DIR = os.getenv("HLS_DIR")

class MediaService:
    HLS_ROOT = HLS_DIR
    HLS_URL_PREFIX = "/hls"

    def __init__(self):
        self.client = get_http_client()
        self.running_streams: Dict[str, Any] = {}
        self.start_cleanup_loop()

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

    def build_hls_output_path(self, device_ip: str, channel_no: int) -> str:
        safe_ip = device_ip.replace(":", "_")
        dir_path = os.path.join(self.HLS_ROOT, f"{safe_ip}", f"channel_{channel_no}")
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, "index.m3u8")

    def build_hls_url(self, device_ip: str, channel_no: int) -> str:
        safe_ip = device_ip.replace(":", "_")
        return f"{self.HLS_URL_PREFIX}/{safe_ip}/channel_{channel_no}/index.m3u8"

    async def build_ffmpeg_hls_process(
        self,
        db: AsyncSession,
        device_id: int,
        channel_id: int,
    ):
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            raise Exception("Device not found")

        result = await db.execute(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.device_id == device.id,
                Channel.is_active == True
            ).options(
                selectinload(Channel.stream_config)
            )
        )
        channel = result.scalars().first()
        if not channel:
            raise Exception("Channel not found")

        headers = build_hik_auth(device)
        rtsp_port = await self.get_rtsp_port(device=device, headers=headers)
        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = decrypt_device_password(device.password)
        password = urllib.parse.quote(password)
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"

        cfg = channel.stream_config
        fps = cfg.max_frame_rate / 100 if cfg and cfg.max_frame_rate else 20
        gop = int(fps)
        output_path = self.build_hls_output_path(ip, channel.channel_no)

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
                profile="baseline",
                level="3.1",
                pix_fmt="yuv420p",
                g=gop,
                keyint_min=gop,
                sc_threshold=0,
                bf=0,
                refs=1,
                coder="cavlc",
                threads=0,
                map="0:v:0",
                hls_time=1,
                hls_list_size=3,
                hls_flags="delete_segments+independent_segments",
            )
        )
        return stream, rtsp_url, channel.channel_no, ip

    async def is_hls_ready(self, m3u8_path: str) -> bool:
        if not os.path.exists(m3u8_path):
            return False
        try:
            async with aiofiles.open(m3u8_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
            return "#EXTINF" in content
        except Exception:
            return False

    async def acquire_channel_stream(self, db: AsyncSession, device_id: int, channel_id: int, user_id: int) -> dict:
        app_logger.info(f"[MEDIA_SERVICE] Acquiring stream for device={device_id}, channel={channel_id}, user={user_id}")
        
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            raise Exception("Device not found")

        result = await db.execute(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.device_id == device.id,
            )
        )
        channel = result.scalars().first()
        if not channel:
            raise Exception("Channel not found")

        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)
        rtsp_port = await self.get_rtsp_port(device, build_hik_auth(device))
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"
        
        masked_rtsp_url = f"rtsp://{username}:******@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"
        
        info = self.running_streams.get(rtsp_url)
        if info:
            if user_id not in info["users"]:
                info["users"].add(user_id)
                info["refcount"] += 1
                info["last_seen"][user_id] = time.time()
                app_logger.info(f"[MEDIA_SERVICE] User {user_id} joined existing stream, refcount={info['refcount']}")
        else:
            app_logger.info("[MEDIA_SERVICE] Initializing new FFmpeg process")
            safe_ip = ip.replace(":", "_")
            hls_dir = os.path.join(self.HLS_ROOT, safe_ip, f"channel_{channel.channel_no}")

            if os.path.exists(hls_dir):
                shutil.rmtree(hls_dir)
            os.makedirs(hls_dir, exist_ok=True)

            stream, _, channel_no, ip = await self.build_ffmpeg_hls_process(db, device_id, channel_id)
            cmd = stream.compile()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.running_streams[rtsp_url] = {
                "proc": proc,
                "users": {user_id},
                "refcount": 1,
                "last_seen": {user_id: time.time()}
            }
            app_logger.info(f"[MEDIA_SERVICE] FFmpeg started for {masked_rtsp_url}, user {user_id}")

            def log_ffmpeg(p):
                for line in p.stderr:
                    pass 
            threading.Thread(target=log_ffmpeg, args=(proc,), daemon=True).start()

            m3u8_path = self.build_hls_output_path(ip, channel_no)
            for _ in range(20):
                if await self.is_hls_ready(m3u8_path):
                    break
                await asyncio.sleep(0.5)
            else:
                raise Exception("HLS not ready")

        hls_url = self.build_hls_url(ip, channel.channel_no)
        return {"hls_url": hls_url}

    async def release_channel_stream(self, db: AsyncSession, device_id: int, channel_id: int, user_id: int, delay: int = 4):
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            return

        result = await db.execute(select(Channel).where(Channel.id == channel_id, Channel.device_id == device.id))
        channel = result.scalars().first()
        if not channel:
            return

        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)
        rtsp_port = await self.get_rtsp_port(device, build_hik_auth(device))
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"

        info = self.running_streams.get(rtsp_url)
        if not info:
            return

        if user_id in info["users"]:
            info["users"].remove(user_id)
            info["refcount"] -= 1
            app_logger.info(f"[MEDIA_SERVICE] User {user_id} left stream, refcount={info['refcount']}")

        if info["refcount"] <= 0:
            def terminate_stream():
                current = self.running_streams.get(rtsp_url)
                if current and current["refcount"] <= 0:
                    proc = current["proc"]
                    app_logger.info("[MEDIA_SERVICE] Terminating FFmpeg process")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    del self.running_streams[rtsp_url]
            threading.Timer(delay, terminate_stream).start()

    def heartbeat(self, user_id: int):
        for info in self.running_streams.values():
            if user_id in info["users"]:
                info["last_seen"][user_id] = time.time()

    def start_cleanup_loop(self, timeout=12):
        def loop():
            app_logger.info(f"[MEDIA_SERVICE] Cleanup loop started (timeout={timeout})")
            while True:
                now = time.time()
                for rtsp_url, info in list(self.running_streams.items()):
                    dead_users = []
                    for uid, ts in info["last_seen"].items():
                        if now - ts > timeout:
                            dead_users.append(uid)

                    for uid in dead_users:
                        app_logger.info(f"[MEDIA_SERVICE] User {uid} timeout")
                        info["users"].discard(uid)
                        info["last_seen"].pop(uid, None)
                        info["refcount"] -= 1

                    if info["refcount"] <= 0:
                        app_logger.info("[MEDIA_SERVICE] No users left, killing ffmpeg")
                        proc = info["proc"]
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        del self.running_streams[rtsp_url]
                time.sleep(5)
        threading.Thread(target=loop, daemon=True).start()

# Global instance
media_service = MediaService()
