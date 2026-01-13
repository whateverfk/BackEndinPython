import ffmpeg
import xml.etree.ElementTree as ET
import urllib.parse
import threading
import subprocess
from sqlalchemy.orm import Session
from app.core.http_client import get_http_client
from app.features.deps import build_hik_auth
from app.Models.user import User
from app.Models.device import Device
from app.Models.channel import Channel
import psutil
import shutil
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()  # load .env

HLS_DIR = os.getenv("HLS_DIR")


class LiveView:
    HLS_ROOT = HLS_DIR
    HLS_URL_PREFIX = "/hls"

    def __init__(self):
        self.client = get_http_client()
        self.running_streams = {}
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


        return stream, rtsp_url, channel.channel_no,ip

    def is_hls_ready(self, m3u8_path: str) -> bool:
        if not os.path.exists(m3u8_path):
            return False

        try:
            with open(m3u8_path, "r", encoding="utf-8") as f:
                content = f.read()
            return "#EXTINF" in content
        except Exception:
            return False


    # =========================
    # Lấy STREAM Rồi decode các thứ
    # =========================
    async def acquire_channel_stream(self, db, device_id: int, channel_id: int, user_id: int) -> dict:
        """
        Bắt đầu stream cho user. Nếu stream đang chạy, chỉ tăng refcount/user set.
        """
        # Xây RTSP URL
        print("aubot to FFmpeg")
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise Exception("Device not found")

        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.device_id == device.id,
        ).first()
        if not channel:
            raise Exception("Channel not found")

        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)
        rtsp_port = await self.get_rtsp_port(device, build_hik_auth(device))
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"
        print(f"rtsp {rtsp_url}")
        info = self.running_streams.get(rtsp_url)
        print(f"infor {info}")
        if info:
            # Nếu user chưa có trong set, thêm vào
            if user_id not in info["users"]:
                info["users"].add(user_id)
                info["refcount"] += 1
                print(f"[ACQUIRE] User {user_id} joined stream {rtsp_url}, refcount = {info['refcount']}")
        else:
            # Tạo process FFmpeg
            print("fk error in build_ffmpeg_hls_process ")
            safe_ip = ip.replace(":", "_")
            hls_dir = os.path.join(self.HLS_ROOT, safe_ip, f"channel_{channel.channel_no}")

            if os.path.exists(hls_dir):
                shutil.rmtree(hls_dir)

            os.makedirs(hls_dir, exist_ok=True)
            stream, rtsp_url, channel_no ,ip= await self.build_ffmpeg_hls_process(db, device_id, channel_id)
            print("fk error in complie ")
            cmd = stream.compile()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.running_streams[rtsp_url] = {
                "proc": proc,
                "users": {user_id},
                "refcount": 1,
                 "last_seen": {
                 user_id: time.time()
        }
            }
            print(f"[ACQUIRE] FFmpeg started for {rtsp_url}, user {user_id}, refcount = 1")

            # Log FFmpeg output
            def log_ffmpeg(p):
                for line in p.stderr:
                    print("[FFMPEG]", line.decode(errors="ignore"))

            threading.Thread(target=log_ffmpeg, args=(proc,), daemon=True).start()
            m3u8_path = self.build_hls_output_path(ip, channel_no)
            for _ in range(20):  # ~10s
                if self.is_hls_ready(m3u8_path):
                    break
                time.sleep(0.5)
            else:
                raise Exception("HLS not ready")

            time.sleep(0.5)

        hls_url = self.build_hls_url(ip, channel.channel_no)
        return {"hls_url": hls_url}

    async def release_channel_stream(self, db, device_id: int, channel_id: int, user_id: int, delay: int = 4):

        """
        Giảm refcount stream cho user. Terminate FFmpeg nếu không còn user nào xem.
        """
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            print("Device not found")
            return

        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.device_id == device.id,
        ).first()
        if not channel:
            print("Channel not found")
            return

        ip = device.ip_nvr or device.ip_web
        username = urllib.parse.quote(device.username)
        password = urllib.parse.quote(device.password)
        rtsp_port = await self.get_rtsp_port(device, build_hik_auth(device))
        rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}/ISAPI/Streaming/channels/{channel.channel_no}"

        info = self.running_streams.get(rtsp_url)
        if not info:
            print(f"[RELEASE] Stream {rtsp_url} chưa chạy hoặc đã release")
            return

        if user_id in info["users"]:
            info["users"].remove(user_id)
            info["refcount"] -= 1
            print(f"[RELEASE] User {user_id} left stream {rtsp_url}, refcount = {info['refcount']}")
        else:
            print(f"[RELEASE] User {user_id} không có trong stream {rtsp_url}")
            return

        if info["refcount"] <= 0:
            # Timer delayed terminate FFmpeg
            def terminate_stream():
                current = self.running_streams.get(rtsp_url)
                if current and current["refcount"] <= 0:
                    proc = current["proc"]
                    print(f"[TERMINATE] Killing FFmpeg for {rtsp_url}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        print(f"[TERMINATE] FFmpeg killed for {rtsp_url}")
                    del self.running_streams[rtsp_url]
                    print(f"[TERMINATE] FFmpeg terminated for {rtsp_url} after {delay}s delay")

            t = threading.Timer(delay, terminate_stream)
            t.start()

    def heartbeat(self, device_id: int, channel_id: int, user_id: int):
        for info in self.running_streams.values():
            if user_id in info["users"]:
                info["last_seen"][user_id] = time.time()
                return

    def start_cleanup_loop(self, timeout=12):
        def loop():
            print("[CLEANUP] cleanup loop started, timeout =", timeout)
            while True:
                now = time.time()
                
                for rtsp_url, info in list(self.running_streams.items()):
                    print(f"[CLEANUP] checking stream {rtsp_url}")
                    print(f"  users      = {info['users']}")
                    print(f"  last_seen  = {info['last_seen']}")
                    print(f"  refcount   = {info['refcount']}")

                    dead_users = []
                    for uid, ts in info["last_seen"].items():
                        delta = now - ts
                        print(f"    user {uid}: last_seen {delta:.1f}s ago")
                        if delta > timeout:
                            dead_users.append(uid)

                    for uid in dead_users:
                        print(f"[CLEANUP] user {uid} TIMEOUT → remove")
                        info["users"].discard(uid)
                        info["last_seen"].pop(uid, None)
                        info["refcount"] -= 1

                    if info["refcount"] <= 0:
                        print(f"[CLEANUP] refcount <= 0 → kill ffmpeg {rtsp_url}")
                        proc = info["proc"]
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            print("[CLEANUP] ffmpeg force killed")

                        del self.running_streams[rtsp_url]
                        print("[CLEANUP] stream removed")

                time.sleep(5)

        threading.Thread(target=loop, daemon=True).start()
