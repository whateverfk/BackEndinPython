
from logging import root
import httpx
import xml.etree.ElementTree as ET
from app.features.GetDevicesDetail.deps import xml_text, HIK_NS
from app.Models.channel_stream_config import ChannelStreamConfig
from app.Models.channel_extensions import ChannelExtension


class HikDetailService:
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
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
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

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
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

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        enabled = xml_text(root, "hik:enabled")

        return enabled.lower() == "true" if enabled else False
    

    async def put_motion_detection(
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

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(url, content=payload, headers=headers)
            resp.raise_for_status()


    async def put_channel_name_local(device, channel, new_name, headers):
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

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{base_url}/ISAPI/System/Video/inputs/channels/{input_id}",
                content=payload,
                headers=headers
            )
            resp.raise_for_status()

    async def put_channel_name_proxy(device, channel, new_name, headers):
        base_url = f"http://{device.ip_web}"
        input_id = (channel.channel_no - 1) // 100
        url = f"{base_url}/ISAPI/ContentMgmt/InputProxy/channels/{input_id}"

        async with httpx.AsyncClient(timeout=10) as client:
            get_resp = await client.get(url, headers=headers)
            get_resp.raise_for_status()

            xml = get_resp.text
            xml = xml.replace(
                "<name>", "<name>").replace("</name>", "</name>"
            )

            # replace name content
            import re
            xml = re.sub(
                r"<name>.*?</name>",
                f"<name>{new_name}</name>",
                xml
            )

            put_resp = await client.put(url, content=xml, headers=headers)
            put_resp.raise_for_status()

    async def put_stream_config_local(device, channel, cfg, headers):
        base_url = f"http://{device.ip_web}"

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
            <videoResolutionHeight>{cfg.resolution_height}</videoResolutionHeight>
            <videoQualityControlType>vbr</videoQualityControlType>
            <fixedQuality>{cfg.fixed_quality}</fixedQuality>
            <maxFrameRate>{cfg.max_frame_rate}</maxFrameRate>
            <vbrAverageCap>{cfg.vbr_average_cap}</vbrAverageCap>
        </Video>
    </StreamingChannel>
    """

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{base_url}/ISAPI/Streaming/channels/{channel.channel_no}",
                content=payload,
                headers=headers
            )
            resp.raise_for_status()

    async def put_stream_config_proxy(device, channel, cfg, headers):
        base_url = f"http://{device.ip_web}"

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
            <dynVideoInputChannelID>{(channel.channel_no-1)//100}</dynVideoInputChannelID>
            <videoCodecType>{cfg.video_codec}</videoCodecType>
            <videoResolutionWidth>{cfg.resolution_width}</videoResolutionWidth>
            <videoResolutionHeight>{cfg.resolution_height}</videoResolutionHeight>
            <videoQualityControlType>vbr</videoQualityControlType>
            <fixedQuality>{cfg.fixed_quality}</fixedQuality>
            <maxFrameRate>{cfg.max_frame_rate}</maxFrameRate>
        </Video>
    </StreamingChannel>
    """

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{base_url}/ISAPI/ContentMgmt/StreamingProxy/channels/{channel.channel_no}",
                content=payload,
                headers=headers
            )
            resp.raise_for_status()

    async def push_channel_config_to_device(
        self,
        device,
        channel,
        headers
    ):
        # Motion
        await self.put_motion_detection(
            device,
            channel,
            channel.extension.motion_detect_enabled,
            headers
        )

        # Name
        if channel.connected_type == "local":
            await self.put_channel_name_local(device, channel, channel.name, headers)
        else:
            await self.put_channel_name_proxy(device, channel, channel.name, headers)

        # Streaming
        if channel.stream_config:
            if channel.connected_type == "local":
                await self.put_stream_config_local(device, channel, channel.stream_config, headers)
            else:
                await self.put_stream_config_proxy(device, channel, channel.stream_config, headers)

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

        print(f"▶ Fetching URL: {url}")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        print(f"▶ Raw XML response:\n{resp.text}\n{'-'*40}")

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

        if width_node is None:
            print("⚠ videoResolutionWidth node missing")
        if height_node is None:
            print("⚠ videoResolutionHeight node missing")

        resolutions = []
        if width_node is not None and height_node is not None:
            widths = width_node.attrib.get("opt", "")
            heights = height_node.attrib.get("opt", "")
            print(f"▶ Width OPT: {widths}, Height OPT: {heights}")

            widths_list = [w for w in widths.split(",") if w.isdigit()] or [width_node.text]
            heights_list = [h for h in heights.split(",") if h.isdigit()] or [height_node.text]
            print(f"▶ Width list: {widths_list}, Height list: {heights_list}")

            resolutions = [
                {"width": int(w), "height": int(h)}
                for w, h in zip(widths_list, heights_list)
            ]
        print(f"✔ Parsed resolutions: {resolutions}")

        # -------- Codec --------
        codec_node = self.hik_find(video, "videoCodecType")
        if codec_node is None:
            print("⚠ videoCodecType node missing")
            video_codecs = []
        else:
            video_codecs = codec_node.attrib.get("opt", "").split(",") or [codec_node.text]
        print(f"✔ Parsed video codecs: {video_codecs}")

        # -------- FPS --------
        fps_node = self.hik_find(video, "maxFrameRate")
        if fps_node is None:
            print("⚠ maxFrameRate node missing")
            max_frame_rates = []
        else:
            opt_fps = fps_node.attrib.get("opt", "")
            max_frame_rates = self.parse_opt_list(opt_fps) or [int(fps_node.text)]
        print(f"✔ Parsed max frame rates: {max_frame_rates}")

        # -------- VBR --------
        upper = self.hik_find(video, "vbrUpperCap")
        lower = self.hik_find(video, "vbrLowerCap")

        upper_min = int(upper.attrib.get("min", 0)) if upper is not None else 0
        upper_max = int(upper.attrib.get("max", 0)) if upper is not None else 0

        lower_val = 0
        if lower is not None:
            lower_val = int(lower.attrib.get("opt", lower.text or 0))

        print(f"✔ VBR upper: {upper_min}-{upper_max}, lower: {lower_val}")

        return {
            "resolutions": resolutions,
            "video_codec": video_codecs,
            "max_frame_rates": max_frame_rates,
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
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10)
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

                print("Storage info fetched:", storage_list)
                return storage_list

        except Exception as ex:
            print(f"Error fetching storage info from {url}: {ex}")
            return []
