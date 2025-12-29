
import httpx
import xml.etree.ElementTree as ET

class HikDetailService:


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
