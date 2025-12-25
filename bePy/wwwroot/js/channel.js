/*************************************************
 * GLOBAL STATE
 *************************************************/
let currentDeviceId = null;

// tháng đang xem (luôn normalize ngày 1, 00:00)
let currentMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

// tháng nhỏ nhất có record (từ backend)
let oldestMonth = null;

// tháng hiện tại thực tế (không cho vượt quá)
const maxMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);


/*************************************************
 * INIT
 *************************************************/
document.addEventListener("DOMContentLoaded", () => {
    loadDeviceList();
    updateMonthLabel();
    bindMonthButtons();
});


/*************************************************
 * DEVICE LIST
 *************************************************/
async function loadDeviceList() {
    const ul = document.getElementById("deviceList");
    if (!ul) return;

    ul.innerHTML = "<li>Loading...</li>";

    try {
        const res = await fetch("http://127.0.0.1:8000/api/devices", {
            headers: {
                Authorization: "Bearer " + localStorage.getItem("token"),
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

        devices.forEach(device => {
            const li = document.createElement("li");
            li.className =
                "device-row flex justify-between items-center p-3 rounded-md border mb-3 cursor-pointer";

            li.innerHTML = `
                <div class="min-w-0">
                    <div class="font-semibold truncate">${escapeHtml(device.ip_web)}</div>
                    <div class="text-sm text-gray-600 truncate">${escapeHtml(device.username || "")}</div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                    <button
                        class="text-sm bg-blue-600 text-white px-3 py-1 rounded"
                        onclick="getNewestData('${device.id}'); event.stopPropagation();"
                    >
                        Get all Data
                    </button>
                </div>
            `;

            li.addEventListener("click", () => selectDevice(device, li));
            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading devices</li>";
    }
}

function selectDevice(device, li) {
    document.querySelectorAll(".device-row").forEach(el =>
        el.classList.remove("ring-2", "ring-blue-300", "bg-blue-50")
    );

    li.classList.add("ring-2", "ring-blue-300", "bg-blue-50");

    currentDeviceId = device.id;
    currentMonth = new Date(maxMonth); // reset về tháng hiện tại
    oldestMonth = null;

    loadCurrentMonth();
}


/*************************************************
 * MONTH NAVIGATION
 *************************************************/
function bindMonthButtons() {
    document.getElementById("prevMonthBtn")?.addEventListener("click", () => {
        changeMonth(-1);
    });

    document.getElementById("nextMonthBtn")?.addEventListener("click", () => {
        changeMonth(1);
    });

    document.getElementById("openConfigBtn")?.addEventListener("click", () => {
        alert("Open config window");
    });
}

function changeMonth(delta) {
    if (!currentDeviceId) return;

    const newMonth = new Date(
        currentMonth.getFullYear(),
        currentMonth.getMonth() + delta,
        1
    );

    // không nhỏ hơn oldest
    if (oldestMonth && isBeforeMonth(newMonth, oldestMonth)) return;

    // không lớn hơn hiện tại
    if (isAfterMonth(newMonth, maxMonth)) return;

    currentMonth = newMonth;
    loadCurrentMonth();
}

function loadCurrentMonth() {
    const monthStr = formatMonth(currentMonth);
    loadChannelMonthData(currentDeviceId, monthStr);
}

function updateMonthLabel() {
    const label = document.getElementById("currentMonthLabel");
    if (!label) return;

    label.innerText =
        `${String(currentMonth.getMonth() + 1).padStart(2, "0")} / ${currentMonth.getFullYear()}`;
}

function updateMonthButtons() {
    const prevBtn = document.getElementById("prevMonthBtn");
    const nextBtn = document.getElementById("nextMonthBtn");

    if (prevBtn && oldestMonth) {
        prevBtn.disabled = isSameMonth(currentMonth, oldestMonth);
        prevBtn.classList.toggle("opacity-40", prevBtn.disabled);
    }

    if (nextBtn) {
        nextBtn.disabled = isSameMonth(currentMonth, maxMonth);
        nextBtn.classList.toggle("opacity-40", nextBtn.disabled);
    }
}


/*************************************************
 * LOAD CHANNEL DATA
 *************************************************/
async function loadChannelMonthData(deviceId, monthStr) {
    const wrapper = document.getElementById("channelTableWrapper");
    wrapper.innerHTML = "Loading channel data...";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/channels/month_data/${monthStr}`,
            {
                headers: {
                    Authorization: "Bearer " + localStorage.getItem("token")
                }
            }
        );

        if (!res.ok) throw new Error("Load channel data failed");

        const data = await res.json();

        // set oldest month (chỉ 1 lần)
        if (data.oldest_record_month && !oldestMonth) {
            const [y, m] = data.oldest_record_month.split("-");
            oldestMonth = new Date(Number(y), Number(m) - 1, 1);
        }

        renderChannelTable(data.channels, monthStr);
        updateMonthLabel();
        updateMonthButtons();
        debugMonthState();

    } catch (err) {
        console.error(err);
        wrapper.innerHTML = "Error loading channel data";
    }
}


/*************************************************
 * TABLE RENDER
 *************************************************/
function renderChannelTable(channels, monthStr) {
    const wrapper = document.getElementById("channelTableWrapper");
    wrapper.innerHTML = "";

    const [year, month] = monthStr.split("-").map(Number);
    const daysInMonth = new Date(year, month, 0).getDate();

    const table = document.createElement("table");
    table.className = "border-collapse min-w-max bg-white shadow rounded";

    /* THEAD */
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

    /* TBODY */
    const tbody = document.createElement("tbody");

    channels.forEach(item => {
        const recordMap = {};
        item.record_days.forEach(rd => {
            recordMap[rd.record_date] = rd;
        });

        const tr = document.createElement("tr");

        const tdChannel = document.createElement("td");
        tdChannel.className =
            "border p-2 sticky left-0 bg-white font-semibold z-10";
        tdChannel.innerText = item.channel.name;
        tr.appendChild(tdChannel);

        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr =
                `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;

            const rd = recordMap[dateStr];
            const info = analyzeRecordDay(rd);

            const td = document.createElement("td");
            td.className =
                "border p-1 text-center cursor-pointer hover:bg-gray-100";

            td.addEventListener("click", () => showTimeRanges(rd));

            const dot = document.createElement("span");
            dot.className = `inline-block w-3 h-3 rounded-full ${info.color}`;
            dot.style.pointerEvents = "none";

            td.appendChild(dot);
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
}


/*************************************************
 * TIME RANGE MODAL
 *************************************************/
function analyzeRecordDay(rd) {
    if (!rd || !rd.has_record || !rd.time_ranges.length) {
        return { color: "bg-gray-300" };
    }

    if (rd.time_ranges.length === 1) {
        const tr = rd.time_ranges[0];
        const start = tr.start_time.split("T")[1];
        const end = tr.end_time.split("T")[1];

        if (start === "00:00:00" && end === "23:59:59") {
            return { color: "bg-green-500" };
        }
    }

    return { color: "bg-yellow-400" };
}

function showTimeRanges(rd) {
    if (!rd || !rd.time_ranges.length) return;

    const modal = document.getElementById("timeRangeModal");
    const ul = document.getElementById("timeRangeList");

    ul.innerHTML = "";

    rd.time_ranges.forEach(tr => {
        ul.innerHTML +=
            `<li>⏱ ${tr.start_time.replace("T", " ")} → ${tr.end_time.replace("T", " ")}</li>`;
    });

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function closeModal() {
    const modal = document.getElementById("timeRangeModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
}


/*************************************************
 * DEVICE SYNC
 *************************************************/
async function getNewestData(deviceId) {
    if (!confirm("Get all newest record data for this device?")) return;

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/get_channels_record_info`,
            {
                method: "POST",
                headers: {
                    Authorization: "Bearer " + localStorage.getItem("token"),
                    "Content-Type": "application/json"
                }
            }
        );

        if (!res.ok) throw new Error(await res.text());
        alert("Sync started");

    } catch (err) {
        console.error(err);
        alert("Sync failed ❌");
    }
}


/*************************************************
 * HELPERS
 *************************************************/
function formatMonth(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function isSameMonth(a, b) {
    return a.getFullYear() === b.getFullYear() &&
           a.getMonth() === b.getMonth();
}

function isBeforeMonth(a, b) {
    return (
        a.getFullYear() < b.getFullYear() ||
        (a.getFullYear() === b.getFullYear() && a.getMonth() < b.getMonth())
    );
}

function isAfterMonth(a, b) {
    return (
        a.getFullYear() > b.getFullYear() ||
        (a.getFullYear() === b.getFullYear() && a.getMonth() > b.getMonth())
    );
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function debugMonthState() {
    console.group("MONTH DEBUG");
    console.log("currentMonth:", currentMonth.toISOString());
    console.log("oldestMonth:", oldestMonth?.toISOString());
    console.log("maxMonth:", maxMonth.toISOString());
    console.groupEnd();
}
