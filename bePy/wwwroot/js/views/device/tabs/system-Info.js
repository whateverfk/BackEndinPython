import { API_URL } from "../../../config.js";

let syncing = false; // chặn loop vô hạn

export async function renderSystemInfo(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `
        <div class="text-gray-500">Loading system info...</div>
    `;

    try {
        const info = await apiFetch(
            `${API_URL}/api/device/${device.id}/infor`
        );

        box.innerHTML = renderInfo(info, device.ip_web);
    }
    catch (err) {
        // CHỈ auto-sync khi 404 và chưa sync lần nào
        if (err?.status === 404 && !syncing) {
            syncing = true;
            await autoSync(device);
            syncing = false;
            return;
        }

        // lỗi khác
        alert("Failed to load system info");
        box.innerHTML = `
            <div class="text-red-500">Unable to load system info</div>
        `;
    }
}
async function autoSync(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `
        <div class="text-gray-500">
            Syncing system info from device...
        </div>
    `;

    try {
        await apiFetch(
            `${API_URL}/api/device/${device.id}/infor/sync`,
            { method: "POST" }
        );

        // sync OK → load lại
        const info = await apiFetch(
            `${API_URL}/api/device/${device.id}/infor`
        );

        box.innerHTML = renderInfo(info, device.ip_web);
    }
    catch {
        alert("Sync system info failed");
        box.innerHTML = `
            <div class="text-red-500">
                Sync failed. Please check device connection.
            </div>
        `;
    }
}
function renderInfo(info, ipWeb) {
    return `
        <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border">
            ${Info("Web IP", ipWeb)}
            ${Info("Model", info.model)}
            ${Info("Serial Number", info.serial_number)}
            ${Info("Firmware Version", info.firmware_version)}
            ${Info("MAC Address", info.mac_address)}
        </div>
    `;
}

function Info(label, value) {
    return `
        <div>
            <p class="text-xs text-gray-500">${label}</p>
            <p class="font-semibold">${value || "-"}</p>
        </div>
    `;
}
