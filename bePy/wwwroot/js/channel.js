
document.addEventListener("DOMContentLoaded", () => {
    loadDeviceList();
});

async function loadDeviceList() {
    const ul = document.getElementById("deviceList");
    ul.innerHTML = "<li>Loading...</li>";

    try {
        const res = await fetch("http://127.0.0.1:8000/api/devices", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token"),
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            throw new Error("Load devices failed");
        }

        const devices = await res.json();
        ul.innerHTML = "";

        if (!devices.length) {
            ul.innerHTML = "<li>No devices</li>";
            return;
        }

        devices.forEach(d => {
            const li = document.createElement("li");
            li.className = "device-row";

            li.innerHTML = `
                <div class="device-info">
                    <div class="device-ip">${d.ip_web}</div>
                    <div class="device-user">${d.username}</div>
                </div>

                <div class="device-actions">
                    

                    <button class="device-btn newest"
                            onclick="getNewestData('${d.id}')">
                        Get all Data
                    </button>
                </div>
            `;

            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading devices</li>";
    }
}


/**
 * Nút mới – Get Newest Data
***/
async function getNewestData(deviceId) {
    if (!confirm("Get all newest record data for this device? It gonna take a while, ( few minutes atleast) U sure ?.")) return;

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/get_channels_record_info`,
            {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token"),
                    "Content-Type": "application/json"
                }
            }
        );

        if (!res.ok) {
            const err = await res.text();
            throw new Error(err);
        }

        alert("Sync channel record info successfully ");

        // reload channel list
        loadChannels(deviceId);

    } catch (err) {
        let currentDeviceId = null;

        document.addEventListener("DOMContentLoaded", () => {
            loadDeviceList();
        });

        async function loadDeviceList() {
            const ul = document.getElementById("deviceList");
            ul.innerHTML = "<li>Loading...</li>";

            try {
                const res = await fetch("/api/devices", {
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
                        <div>
                            <div class="font-semibold">${d.ip_web}</div>
                            <div class="text-sm text-gray-600">${d.username}</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <button class="device-btn newest text-sm" onclick="getNewestData('${d.id}'); event.stopPropagation();">Get all Data</button>
                        </div>
                    `;

                    // clicking the device row selects it (no further action for now)
                    li.addEventListener('click', () => deviceAction(d.id, li));

                    ul.appendChild(li);
                });

            } catch (err) {
                console.error(err);
                ul.innerHTML = "<li>Error loading devices</li>";
            }
        }

        function deviceAction(deviceId, liElement) {
            // mark selected visually
            document.querySelectorAll('.device-row').forEach(el=>el.classList.remove('bg-blue-50'));
            if (liElement) liElement.classList.add('bg-blue-50');
            currentDeviceId = deviceId;
            // intentionally no further action per request
        }

        /**
         * Get newest data (keeps existing behavior)
         */
        async function getNewestData(deviceId) {
            if (!confirm("Get all newest record data for this device? It may take several minutes.")) return;

            try {
                const res = await fetch(`/api/devices/${deviceId}/get_channels_record_info`, {
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
                // no automatic follow-up action per request
            } catch (err) {
                console.error(err);
                alert("Sync failed ❌");
            }
        }
                recordDayElement.appendChild(noTimeRanges);
    }
}
