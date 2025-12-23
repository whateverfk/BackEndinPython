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
 * Nút cũ – tạm thời chưa có tác dụng
 */
function deviceAction(deviceId) {
    console.log("Device action:", deviceId);
    alert("Action device: " + deviceId);
}

/**
 * Nút mới – Get Newest Data
 * Sau này gắn API thật
 */
function getNewestData(deviceId) {
    console.log("Get newest data for device:", deviceId);
    alert("Get newest data: " + deviceId);

    // ví dụ tương lai:
    // await fetch(`/api/devices/${deviceId}/newest-data`, { method: "POST" })
}
