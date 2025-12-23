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
                    <button class="device-btn"
                            onclick="deviceAction('${d.id}')">
                        Action
                    </button>

                    <button class="device-btn newest"
                            onclick="getNewestData('${d.id}')">
                        Get newest data
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
 * Nút  – tạm thời chưa có tác dụng
 */
function deviceAction(deviceId) {
    loadChannels(deviceId);
}

async function loadChannels(deviceId) {
    const ul = document.getElementById("channelList");
    ul.innerHTML = "<li>Loading channels...</li>";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/channels`,
            {
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token")
                }
            }
        );

        if (!res.ok) throw new Error("Load channels failed");

        const channels = await res.json();
        ul.innerHTML = "";

        if (!channels.length) {
            ul.innerHTML = "<li>No channels</li>";
            return;
        }

        channels.forEach(ch => {
            const li = document.createElement("li");
            li.className = "channel-row";
            li.textContent = `${ch.channel_no} - ${ch.name}`;

            li.onclick = () => selectChannel(ch);

            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading channels</li>";
    }
}

/**
 * Nút mới – Get Newest Data
***/
async function getNewestData(deviceId) {
    if (!confirm("Sync newest record data for this device?")) return;

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

        alert("Sync channel record info successfully ✅");

        // reload channel list
        loadChannels(deviceId);

    } catch (err) {
        console.error(err);
        alert("Sync failed ❌");
    }
}


function selectChannel(channel) {
    document.getElementById("channelTitle").innerText =
        `Record Time – ${channel.name}`;

    console.log("Selected channel:", channel);

    // tương lai:
    // loadChannelRecordDays(channel.id)
}
