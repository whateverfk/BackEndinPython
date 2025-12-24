
// device list interactions for channel.html

let currentDeviceId = null;

document.addEventListener("DOMContentLoaded", () => {
    loadDeviceList();
});

async function loadDeviceList() {
    const ul = document.getElementById("deviceList");
    if (!ul) return;
    ul.innerHTML = "<li>Loading...</li>";

    try {
        const res = await fetch("http://127.0.0.1:8000/api/devices", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token"),
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) throw new Error("Load devices failed");

        const devices = await res.json();
        ul.innerHTML = "";

        if (!devices.length) {
            ul.innerHTML = "<li>No devices</li>";
            return;
        }

        devices.forEach(d => {
            const li = document.createElement("li");
            li.className = "device-row flex justify-between items-center p-3 rounded-md border mb-3 cursor-pointer";

            li.innerHTML = `
                <div class="min-w-0">
                    <div class="font-semibold truncate">${escapeHtml(d.ip_web)}</div>
                    <div class="text-sm text-gray-600 truncate">${escapeHtml(d.username || '')}</div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                    <button class="device-btn newest text-sm bg-blue-600 text-white px-3 py-1 rounded" onclick="getNewestData('${d.id}'); event.stopPropagation();">Get all Data</button>
                </div>
            `;

            // clicking the device row selects it and shows an alert
            li.addEventListener('click', () => deviceAction(d, li));

            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading devices</li>";
    }
}

function deviceAction(device, liElement) {
    // clear previous selection styling
    document.querySelectorAll('.device-row').forEach(el => {
        el.classList.remove('ring-2', 'ring-blue-300', 'bg-blue-50');
    });

    // apply selection styling
    if (liElement) {
        liElement.classList.add('ring-2', 'ring-blue-300', 'bg-blue-50');
    }

    currentDeviceId = device.id;

    // show alert with selected device name/ip
    alert(`Selected device: ${device.ip_web} ${device.username ? '(' + device.username + ')' : ''}`);
}

/**
 * Trigger device-wide sync (keeps existing behavior).
 * Button click stops propagation so it won't trigger row click.
 */
async function getNewestData(deviceId) {
    if (!confirm("Get all newest record data for this device? It may take several minutes.")) return;

    try {
        const res = await fetch(`http://127.0.0.1:8000/api/devices/${deviceId}/get_channels_record_info`, {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token"),
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            const err = await res.text();
            throw new Error(err);
        }

        alert("Sync channel record info started");
    } catch (err) {
        console.error(err);
        alert("Sync failed ❌");
    }
}

// small helper to avoid injection when inserting raw values
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
