
from logging import root
import httpx
import re
import xml.etree.ElementTree as ET
from app.features.deps import xml_text, HIK_NS
from app.Models.channel_stream_config import ChannelStreamConfig
from app.Models.channel_extensions import ChannelExtension
from app.core.http_client import get_http_client


class HikDetailService:
    def __init__(self):
        self.client = get_http_client()
    LOCAL_GLOBAL_FIELDS = [
    "upgrade",
    "parameterConfig",
    "restartOrShutdown",
    "logOrStateCheck",
    "manageChannel",
    "playBack",
    "record",
    "backup",
    ]

    REMOTE_GLOBAL_FIELDS = [
        "parameterConfig",
        "logOrStateCheck",
        "upgrade",
        "voiceTalk",
        "restartOrShutdown",
        "alarmOutOrUpload",
        "contorlLocalOut",
        "transParentChannel",
        "manageChannel",
        "preview",
        "record",
        "playBack",
    ]

    CONNECTED_TYPE_LOCAL = "local"
    CONNECTED_TYPE_PROXY = "proxy"

    async def getSystemInfo(self, device, headers):
        """
        Lấy thông tin hệ thống device (model, serial, firmware, mac)
        """
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/System/deviceInfo"

        print(f"Requesting URL: {repr(url)}")

        try:
            
                resp = await self.client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()

                root = ET.fromstring(resp.text)
                ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

                model = root.findtext("hik:model", default=None, namespaces=ns)
                serial_number = root.findtext("hik:serialNumber", default=None, namespaces=ns)
                mac_address = root.findtext("hik:macAddress", default=None, namespaces=ns)

                firmware_version = root.findtext(
                    "hik:firmwareVersion", default="", namespaces=ns
                )
                firmware_release = root.findtext(
                    "hik:firmwareReleasedDate", default="", namespaces=ns
                )

                firmware_full = f"{firmware_version} {firmware_release}".strip()

                system_info = {
                    "model": model,
                    "serial_number": serial_number,
                    "firmware_version": firmware_full,
                    "mac_address": mac_address
                }

                print("System info fetched:", system_info)
                return system_info

        except Exception as ex:
            print(f"Error fetching system info from {url}: {ex}")
            return None

    async def fetch_stream_config(
        self,
        device,
        channel,
        headers,
    ):
        base_url = f"http://{device.ip_web}"

        if channel.connected_type == self.CONNECTED_TYPE_LOCAL:
            url = f"{base_url}/ISAPI/Streaming/channels/{channel.channel_no}"
        else:
            url = f"{base_url}/ISAPI/ContentMgmt/StreamingProxy/channels/{channel.channel_no}"

        
        resp = await self.client.get(url, headers=headers)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)

        video = root.find(".//hik:Video", HIK_NS)
        if video is None:
            return None
        print("----- HIK STREAM CONFIG XML -----")
        print(resp.text)
        print("--------------------------------")


        return {
            "resolution_width": int(xml_text(video, "hik:videoResolutionWidth")),
            "resolution_height": int(xml_text(video, "hik:videoResolutionHeight")),
            "video_codec": xml_text(video, "hik:videoCodecType"),
            "max_frame_rate": int(xml_text(video, "hik:maxFrameRate")),
            "fixed_quality": int(xml_text(video, "hik:fixedQuality"))
                if xml_text(video, "hik:fixedQuality") else None,
            "vbr_average_cap": int(xml_text(video, "hik:vbrAverageCap"))
                if xml_text(video, "hik:vbrAverageCap") else None,
        }

    def calc_input_channel_index(self,channel_no: int) -> int:
        return (channel_no - 1) // 100
    
    
    async def fetch_motion_detection(
        self,
        device,
        channel,
        headers,
    ):
        base_url = f"http://{device.ip_web}"
        index = self.calc_input_channel_index(channel.channel_no)

        if channel.connected_type == self.CONNECTED_TYPE_LOCAL:
            url = f"{base_url}/ISAPI/System/Video/inputs/channels/{index}/motionDetection"
        else:
            url = f"{base_url}/ISAPI/ContentMgmt/InputProxy/channels/{index}/video/motionDetection"

       
        resp = await self.client.get(url, headers=headers)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        enabled = xml_text(root, "hik:enabled")

        return enabled.lower() == "true" if enabled else False
    

    async def put_motion_detection(
    self,
    device,
    channel,
    enabled: bool,
    headers
):
        base_url = f"http://{device.ip_web}"
        input_id = (channel.channel_no - 1) // 100

        if channel.connected_type == "local":
            url = f"{base_url}/ISAPI/System/Video/inputs/channels/{input_id}/motionDetection"
            sensitivity = 2
        else:
            url = f"{base_url}/ISAPI/ContentMgmt/InputProxy/channels/{input_id}/video/motionDetection"
            sensitivity = 3

        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <MotionDetection xmlns="{HIK_NS}" version="1.0">
        <enabled>{"true" if enabled else "false"}</enabled>
        <enableHighlight>true</enableHighlight>
        <samplingInterval>5</samplingInterval>
        <startTriggerTime>1000</startTriggerTime>
        <endTriggerTime>1000</endTriggerTime>
        <regionType>grid</regionType>
        <Grid>
            <rowGranularity>18</rowGranularity>
            <columnGranularity>22</columnGranularity>
        </Grid>
        <MotionDetectionLayout xmlns="{HIK_NS}" version="1.0">
            <sensitivityLevel>{sensitivity}</sensitivityLevel>
            <layout>
                <gridMap></gridMap>
            </layout>
        </MotionDetectionLayout>
        <discardFalseAlarm opt="true,false">false</discardFalseAlarm>
    </MotionDetection>
    """

       
        resp = await self.client.put(url, content=payload, headers=headers)
        resp.raise_for_status()

    async def put_channel_name_local(self,device, channel, new_name, headers):
        base_url = f"http://{device.ip_web}"
        input_id = (channel.channel_no - 1) // 100

        payload = f"""<?xml version="1.0" encoding="utf-8"?>
    <VideoInputChannel xmlns="{HIK_NS}" version="1.0">
        <id>{input_id}</id>
        <inputPort>{input_id}</inputPort>
        <videoInputEnabled>true</videoInputEnabled>
        <name>{new_name}</name>
        <videoFormat>PAL</videoFormat>
        <resDesc>1080P25</resDesc>
    </VideoInputChannel>
    """

        
        resp = await self.client.put(
                f"{base_url}/ISAPI/System/Video/inputs/channels/{input_id}",
                content=payload,
                headers=headers
            )
        resp.raise_for_status()

    async def put_channel_name_proxy(self,device, channel, new_name, headers):
        base_url = f"http://{device.ip_web}"
        input_id = (channel.channel_no - 1) // 100
        url = f"{base_url}/ISAPI/ContentMgmt/InputProxy/channels/{input_id}"

        
        get_resp = await self.client.get(url, headers=headers)
        get_resp.raise_for_status()

        xml = get_resp.text
        xml = xml.replace(
                "<name>", "<name>").replace("</name>", "</name>"
            )

            # replace name content
        
        xml = re.sub(
            r"<name>.*?</name>",
            f"<name>{new_name}</name>",
            xml
            )

        put_resp = await self.client.put(url, content=xml, headers=headers)
        put_resp.raise_for_status()

    async def put_stream_config_proxy(self, device, channel, cfg, headers):
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/ContentMgmt/StreamingProxy/channels/{channel.channel_no}"

        print("\n===== PUT STREAM PROXY =====")
        print("URL:", url)

        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <StreamingChannel xmlns="{HIK_NS}" version="1.0">
        <id>{channel.channel_no}</id>
        <channelName>{channel.channel_no}</channelName>
        <enabled>true</enabled>
        <Transport>
            <ControlProtocolList>
                <ControlProtocol>
                    <streamingTransport>RTSP</streamingTransport>
                </ControlProtocol>
            </ControlProtocolList>
        </Transport>
        <Video xmlns="">
            <enabled>true</enabled>
            <dynVideoInputChannelID>{(channel.channel_no-1)//100}</dynVideoInputChannelID>
            <videoCodecType>{cfg.video_codec}</videoCodecType>
            <videoResolutionWidth>{cfg.resolution_width}</videoResolutionWidth>
            <videoScanType>progressive</videoScanType>
            <videoResolutionHeight>{cfg.resolution_height}</videoResolutionHeight>
            <videoQualityControlType>vbr</videoQualityControlType>
            <fixedQuality>{cfg.fixed_quality}</fixedQuality>
            <maxFrameRate>{cfg.max_frame_rate}</maxFrameRate>
        </Video>
    </StreamingChannel>
    """

        print("----- REQUEST XML -----")
        print(payload)
        print("-----------------------")

        resp = await self.client.put(url, content=payload, headers=headers)

        print("----- RESPONSE -----")
        print("Status:", resp.status_code)
        print("Body:\n", resp.text)
        print("--------------------")

        resp.raise_for_st

    async def put_stream_config_local(self, device, channel, cfg, headers):
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/Streaming/channels/{channel.channel_no}"

        print("\n===== PUT STREAM LOCAL =====")
        print("URL:", url)
        print("CFG:",
            "codec=", cfg.video_codec,
            "w=", cfg.resolution_width,
            "h=", cfg.resolution_height,
            "fps=", cfg.max_frame_rate,
            "fixedQ=", cfg.fixed_quality,
            "vbrCap=", cfg.vbr_average_cap,
        )

        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <StreamingChannel xmlns="{HIK_NS}" version="1.0">
        <id>{channel.channel_no}</id>
        <channelName>{channel.channel_no}</channelName>
        <enabled>true</enabled>
        <Transport>
            <ControlProtocolList>
                <ControlProtocol>
                    <streamingTransport>RTSP</streamingTransport>
                </ControlProtocol>
            </ControlProtocolList>
        </Transport>
        <Video>
            <enabled>true</enabled>
            <videoInputChannelID>{(channel.channel_no-1)//100}</videoInputChannelID>
            <videoCodecType>{cfg.video_codec}</videoCodecType>
            <videoResolutionWidth>{cfg.resolution_width}</videoResolutionWidth>
            <videoScanType>progressive</videoScanType>
            <videoResolutionHeight>{cfg.resolution_height}</videoResolutionHeight>
            <videoQualityControlType>vbr</videoQualityControlType>
            <fixedQuality>{cfg.fixed_quality}</fixedQuality>
            <maxFrameRate>{cfg.max_frame_rate}</maxFrameRate>
            <vbrAverageCap>{cfg.vbr_average_cap}</vbrAverageCap>
        </Video>
    </StreamingChannel>
    """

        print("----- REQUEST XML -----")
        print(payload)
        print("-----------------------")

        resp = await self.client.put(url, content=payload, headers=headers)

        print("----- RESPONSE -----")
        print("Status:", resp.status_code)
        print("Body:\n", resp.text)
        print("--------------------")

        resp.raise_for_status()




    async def push_channel_config_to_device(self, device, channel, headers):
        print(" PUSH START",
            "device=", device.id,
            "channel=", channel.channel_no,
            "type=", channel.connected_type)

        print(" MOTION")
        await self.put_motion_detection(
            device, channel, channel.extension.motion_detect_enabled, headers
        )
        print(" MOTION OK")

        print(" NAME")
        if channel.connected_type == "local":
            await self.put_channel_name_local(device, channel, channel.name, headers)
        else:
            await self.put_channel_name_proxy(device, channel, channel.name, headers)

        print(" STREAM")
        if channel.stream_config:
            if channel.connected_type == "local":
                await self.put_stream_config_local(device, channel, channel.stream_config, headers)
            else:
                await self.put_stream_config_proxy(device, channel, channel.stream_config, headers)

        print(" PUSH DONE")

    def hik_find(self,parent, tag):
        return parent.find(f"hik:{tag}", HIK_NS)


    def parse_opt_list(self,opt_str: str):
        if not opt_str:
            return []
        return [int(x) for x in opt_str.split(",") if x.isdigit()]


    async def get_streaming_capabilities(self, device, channel, headers):
        if channel.connected_type == "local":
            url = f"http://{device.ip_web}/ISAPI/Streaming/channels/{channel.channel_no}/capabilities"
        else:
            url = f"http://{device.ip_web}/ISAPI/ContentMgmt/StreamingProxy/channels/{channel.channel_no}/capabilities"

        
        
        resp = await self.client.get(url, headers=headers)
        resp.raise_for_status()

        

        root = ET.fromstring(resp.text)
        video = self.hik_find(root, "Video")

        if video is None:
            print("⚠ Video node not found in XML")
            return {
                "resolutions": [],
                "video_codec": [],
                "max_frame_rates": [],
                "vbr": {"upper_cap": {"min": 0, "max": 0}, "lower_cap": {"min": 0, "max": 0}}
            }

        # -------- Resolution (OPT LIST) --------
        width_node = self.hik_find(video, "videoResolutionWidth")
        height_node = self.hik_find(video, "videoResolutionHeight")

        # if width_node is None:
        #     print(" videoResolutionWidth node missing")
        # if height_node is None:
        #     print(" videoResolutionHeight node missing")

        resolutions = []
        if width_node is not None and height_node is not None:
            widths = width_node.attrib.get("opt", "")
            heights = height_node.attrib.get("opt", "")
            #print(f" Width OPT: {widths}, Height OPT: {heights}")

            widths_list = [w for w in widths.split(",") if w.isdigit()] or [width_node.text]
            heights_list = [h for h in heights.split(",") if h.isdigit()] or [height_node.text]
            #print(f" Width list: {widths_list}, Height list: {heights_list}")

            resolutions = [
                {"width": int(w), "height": int(h)}
                for w, h in zip(widths_list, heights_list)
            ]
        #print(f"✔ Parsed resolutions: {resolutions}")

        # -------- Codec --------
        codec_node = self.hik_find(video, "videoCodecType")
        if codec_node is None:
            print(" videoCodecType node missing")
            video_codecs = []
        else:
            video_codecs = codec_node.attrib.get("opt", "").split(",") or [codec_node.text]
        #print(f" Parsed video codecs: {video_codecs}")
                # -------- Fixed Quality (ENUM) --------
        fixed_q_node = self.hik_find(video, "fixedQuality")

        if fixed_q_node is None:
            print(" fixedQuality node missing")
            fixed_quality = {
                "options": [],
                "current": None,
                "default": None
            }
        else:
            opt = fixed_q_node.attrib.get("opt", "")
            options = [
                int(v) for v in opt.split(",")
                if v.isdigit()
            ]

            current = int(fixed_q_node.text) if fixed_q_node.text and fixed_q_node.text.isdigit() else None

            fixed_quality = {
                "options": options,
                "current": current,
                "default": current or (options[-1] if options else None)
            }

        #print(f"✔ Fixed quality: {fixed_quality}")


        # -------- FPS --------
        fps_node = self.hik_find(video, "maxFrameRate")
        if fps_node is None:
            #print(" maxFrameRate node missing")
            max_frame_rates = []
        else:
            opt_fps = fps_node.attrib.get("opt", "")
            max_frame_rates = self.parse_opt_list(opt_fps) or [int(fps_node.text)]
        #print(f" Parsed max frame rates: {max_frame_rates}")

        # -------- VBR --------
        upper = self.hik_find(video, "vbrUpperCap")
        lower = self.hik_find(video, "vbrLowerCap")

        upper_min = int(upper.attrib.get("min", 0)) if upper is not None else 0
        upper_max = int(upper.attrib.get("max", 0)) if upper is not None else 0

        lower_val = 0
        if lower is not None:
            lower_val = int(lower.attrib.get("opt", lower.text or 0))

        #print(f" VBR upper: {upper_min}-{upper_max}, lower: {lower_val}")

        return {
            "resolutions": resolutions,
            "video_codec": video_codecs,
            "max_frame_rates": max_frame_rates,
            "fixed_quality": fixed_quality,
            "vbr": {
                "upper_cap": {"min": upper_min, "max": upper_max},
                "lower_cap": {"min": lower_val, "max": lower_val},
            }
            
        }

  

    async def get_device_storage(self,device, headers):
        """
        Lấy thông tin storage từ thiết bị ISAPI (async)

        Args:
            device: object chứa thông tin device (device.ip_web, device.id,...)
            headers: dict headers nếu cần xác thực

        Returns:
            list of dict: mỗi dict là 1 HDD
        """
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/ContentMgmt/Storage"

        print(f"Requesting URL: {repr(url)}")

        try:
            
                resp = await self.client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()

                root = ET.fromstring(resp.text)
                ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

                storage_list = []
                hdd_list = root.find("hik:hddList", ns)
                if hdd_list is not None:
                    for hdd in hdd_list.findall("hik:hdd", ns):
                        storage_info = {
                            "device_id": device.id,
                            "hdd_id": int(hdd.findtext("hik:id", default="0", namespaces=ns)),
                            "hdd_name": hdd.findtext("hik:hddName", default="", namespaces=ns),
                            "status": hdd.findtext("hik:status", default="", namespaces=ns),
                            "hdd_type": hdd.findtext("hik:hddType", default="", namespaces=ns),
                            "capacity": int(hdd.findtext("hik:capacity", default="0", namespaces=ns)),
                            "free_space": int(hdd.findtext("hik:freeSpace", default="0", namespaces=ns)),
                            "property": hdd.findtext("hik:property", default="", namespaces=ns)
                        }
                        storage_list.append(storage_info)

                
                return storage_list

        except Exception as ex:
            print(f"Error fetching storage info from {url}: {ex}")
            return []


    async def get_device_onvif_users(self, device, headers):
        """
        Lấy danh sách ONVIF users từ thiết bị
        """
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/Security/ONVIF/users"

        try:
            
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

            users = []
            for u in root.findall("hik:User", ns):
                users.append({
                    "device_id": device.id,
                    "user_id": int(u.findtext("hik:id", "0", ns)),
                    "username": u.findtext("hik:userName", "", ns),
                    "level": u.findtext("hik:userType", "", ns),
                })

            
            return users

        except Exception as ex:
            print(f"[ONVIF][User] Error: {ex}")
            return []


    async def fetch_device_users(self,device, headers):
        """
        Lấy danh sách user từ ISAPI:
        GET /ISAPI/Security/users
        """
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/Security/users"

        try:
            
                resp = await self.client.get(url, headers=headers, timeout=10)
                resp.raise_for_status()

                root = ET.fromstring(resp.text)
                ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

                users = []

                for user_el in root.findall("hik:User", ns):
                    user_id = user_el.findtext("hik:id", default=None, namespaces=ns)
                    user_name = user_el.findtext("hik:userName", default=None, namespaces=ns)
                    user_level = user_el.findtext("hik:userLevel", default=None, namespaces=ns)

                    if not user_id or not user_name:
                        continue

                    users.append({
                        "user_id": int(user_id),
                        "user_name": user_name,
                        "role": user_level.lower() if user_level else None
                    })

                return users

        except Exception as ex:
            print(f"[ISAPI][USERS] Error fetching users from {url}: {ex}")
            return []

    def xml_bool(self,el, tag, ns):
        v = el.findtext(tag, default="false", namespaces=ns)
        return v.lower() == "true"

    
    async def fetch_permission_for_1_user(
        self,
        device,
        headers,
        user_id: int
    ):
        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/Security/UserPermission/{user_id}"

        ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

        try:
            
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)

            result = {
                "user_id": user_id,
                "user_type": root.findtext("hik:userType", namespaces=ns),
                "local": {
                    "global": {},
                    "channels": {}
                },
                "remote": {
                    "global": {},
                    "channels": {}
                }
            }

            # ========== LOCAL ==========
            local_el = root.find("hik:localPermission", ns)
            if local_el is not None:
                # global permissions
                for f in self.LOCAL_GLOBAL_FIELDS:
                    result["local"]["global"][f] = self.xml_bool(local_el, f"hik:{f}", ns)

                # videoChannelPermissionList
                for vc in local_el.findall(
                    "hik:videoChannelPermissionList/hik:videoChannelPermission",
                    ns
                ):
                    ch_id = int(vc.findtext("hik:id", namespaces=ns))

                    for perm in ["playBack", "record", "backup"]:
                        if self.xml_bool(vc, f"hik:{perm}", ns):
                            result["local"]["channels"].setdefault(
                                perm.lower(), []
                            ).append(ch_id)

                # ptz
                for pc in local_el.findall(
                    "hik:ptzChannelPermissionList/hik:ptzChannelPermission",
                    ns
                ):
                    if self.xml_bool(pc, "hik:ptzControl", ns):
                        ch_id = int(pc.findtext("hik:id", namespaces=ns))
                        result["local"]["channels"].setdefault(
                            "ptz_control", []
                        ).append(ch_id)

            # ========== REMOTE ==========
            remote_el = root.find("hik:remotePermission", ns)
            if remote_el is not None:
                for f in self.REMOTE_GLOBAL_FIELDS:
                    result["remote"]["global"][f] = self.xml_bool(
                        remote_el, f"hik:{f}", ns
                    )

                for vc in remote_el.findall(
                    "hik:videoChannelPermissionList/hik:videoChannelPermission",
                    ns
                ):
                    ch_id = int(vc.findtext("hik:id", namespaces=ns))

                    for perm in ["preview", "record", "playBack"]:
                        if self.xml_bool(vc, f"hik:{perm}", ns):
                            result["remote"]["channels"].setdefault(
                                perm.lower(), []
                            ).append(ch_id)

                for pc in remote_el.findall(
                    "hik:ptzChannelPermissionList/hik:ptzChannelPermission",
                    ns
                ):
                    if self.xml_bool(pc, "hik:ptzControl", ns):
                        ch_id = int(pc.findtext("hik:id", namespaces=ns))
                        result["remote"]["channels"].setdefault(
                            "ptz_control", []
                        ).append(ch_id)

            return result

        except Exception as ex:
            print(f"[ISAPI][USER_PERMISSION] Error fetching from {url}: {ex}")
            return None
        
        