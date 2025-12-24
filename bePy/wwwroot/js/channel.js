
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
    document.querySelectorAll('.device-row').forEach(el => {
        el.classList.remove('ring-2', 'ring-blue-300', 'bg-blue-50');
    });

    liElement.classList.add('ring-2', 'ring-blue-300', 'bg-blue-50');
    currentDeviceId = device.id;

    // Load channel table cho tháng hiện tại
    const now = new Date();
    const monthStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    loadChannelMonthData(device.id, monthStr);
}

async function loadChannelMonthData(deviceId, monthStr) {
    const wrapper = document.getElementById("channelTableWrapper");
    wrapper.innerHTML = "Loading channel data...";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/channels/month_data/${monthStr}`,
            {
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token")
                }
            }
        );

        if (!res.ok) throw new Error("Load channel data failed");

        const data = await res.json();
        renderChannelTable(data, monthStr);

    } catch (err) {
        console.error(err);
        wrapper.innerHTML = "Error loading channel data";
    }
}

function renderChannelTable(data, monthStr) {
    
    const wrapper = document.getElementById("channelTableWrapper");

    const [year, month] = monthStr.split("-").map(Number);
    const daysInMonth = new Date(year, month, 0).getDate();

    const table = document.createElement("table");
    table.className = "border-collapse min-w-max bg-white shadow rounded";

    /* ===== THEAD ===== */
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");

    const thChannel = document.createElement("th");
    thChannel.className = "border p-2 sticky left-0 top-0 bg-white z-20";
    thChannel.innerText = "Channel";
    headRow.appendChild(thChannel);

    for (let d = 1; d <= daysInMonth; d++) {
        const th = document.createElement("th");
        th.className = "border p-2 text-xs sticky top-0 bg-gray-100 z-10";
        th.innerText = d;
        headRow.appendChild(th);
    }

    thead.appendChild(headRow);
    table.appendChild(thead);

    /* ===== TBODY ===== */
    const tbody = document.createElement("tbody");

    data.forEach(item => {
        const ch = item.channel;

        const recordMap = {};
        item.record_days.forEach(rd => {
            recordMap[rd.record_date] = rd;
        });

        const tr = document.createElement("tr");

        // Channel cell (sticky left)
        const tdChannel = document.createElement("td");
        tdChannel.className = "border p-2 sticky left-0 bg-white font-semibold z-10";
        tdChannel.innerText = ` ${ch.name}`;
        tr.appendChild(tdChannel);

        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            const rd = recordMap[dateStr];

            const cellInfo = analyzeRecordDay(rd);

            const td = document.createElement("td");
            td.className = `
                border p-1 text-center
                cursor-pointer
                relative z-0
                hover:bg-gray-100
            `;

            // CLICK HANDLER (đúng cách)

            td.addEventListener("click", () => {
                showTimeRanges(rd);
            });

            const dot = document.createElement("span");
            dot.className = `
                inline-block w-3 h-3 rounded-full
                ${cellInfo.color}
                pointer-events-none
            `;

            td.appendChild(dot);
            tr.appendChild(td);

        }

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);

    wrapper.innerHTML = "";
    wrapper.appendChild(table);
    
}


function analyzeRecordDay(rd) {
    if (!rd || !rd.has_record || !rd.time_ranges.length) {
        return { color: "bg-gray-300" }; // xám
    }

    if (rd.time_ranges.length === 1) {
        const tr = rd.time_ranges[0];
        const start = tr.start_time.split("T")[1];
        const end = tr.end_time.split("T")[1];

        if (start === "00:00:00" && end === "23:59:59") {
            return { color: "bg-green-500" }; // xanh
        }
    }

    return { color: "bg-yellow-400" }; // vàng
}
function showTimeRanges(rd) {
    if (!rd || !rd.time_ranges.length) return;

    const modal = document.getElementById("timeRangeModal");
    const ul = document.getElementById("timeRangeList");
    ul.innerHTML = "";

    rd.time_ranges.forEach(tr => {
        ul.innerHTML += `
            <li>⏱ ${tr.start_time.replace("T"," ")} → ${tr.end_time.replace("T"," ")}</li>
        `;
    });

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function closeModal() {
    const modal = document.getElementById("timeRangeModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
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

let currentMonth = new Date();

document.addEventListener("DOMContentLoaded", () => {
    updateMonthLabel();

    document.getElementById("prevMonthBtn")?.addEventListener("click", () => {
        alert("Prev month clicked");
    });

    document.getElementById("nextMonthBtn")?.addEventListener("click", () => {
        alert("Next month clicked");
    });

    document.getElementById("openConfigBtn")?.addEventListener("click", () => {
        alert("Open config window");
    });
});

function updateMonthLabel() {
    const label = document.getElementById("currentMonthLabel");
    if (!label) return;

    const month = currentMonth.getMonth() + 1;
    const year = currentMonth.getFullYear();

    label.innerText = `${String(month).padStart(2, "0")} / ${year}`;
}
