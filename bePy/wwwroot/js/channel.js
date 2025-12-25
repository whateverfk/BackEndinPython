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

let cachedMonthData = null;   // lưu toàn bộ data tháng
let currentView = "month";   // "month" | "day"
let selectedDay = null;      // YYYY-MM-DD



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
        const res = await fetch("http://127.0.0.1:8000/api/devices/active", {
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
    const monthContainer = document.getElementById("monthTableContainer");
    const dayContainer = document.getElementById("dayTableContainer");
    monthContainer.innerHTML = "Loading channel data...";

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
        cachedMonthData = data;
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

    const monthContainer = document.getElementById("monthTableContainer");
    const dayContainer = document.getElementById("dayTableContainer");

    if (!monthContainer) return;

    // reset view
    monthContainer.innerHTML = "";
    dayContainer.innerHTML = "";
    dayContainer.classList.add("hidden");
    monthContainer.classList.remove("hidden");

    const [year, month] = monthStr.split("-").map(Number);
    const daysInMonth = new Date(year, month, 0).getDate();

    const table = document.createElement("table");
    table.className = "border-collapse min-w-max bg-white shadow rounded";

    /* THEAD */
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");

    const thChannel = document.createElement("th");
    thChannel.className = "border p-2 sticky left-0 top-0 bg-white z-20"    ;
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

            // const td = document.createElement("td");
            // td.className =
            //     "border p-1 text-center cursor-pointer hover:bg-gray-100";

            // td.addEventListener("click", () => showTimeRanges(rd));

            // // Hiển thị chấm màu
            // const dot = document.createElement("span");
            // dot.className = `inline-block w-3 h-3 rounded-full ${info.color}`;
            // dot.style.pointerEvents = "none";

            // td.appendChild(dot);
            
            // Hiển thị timeline ?
            const td = document.createElement("td");
            // thêm border để dễ nhìn nếu cần
            // td.className = "border cursor-pointer p-0 align-middle";
            td.className = " cursor-pointer p-0 align-middle";

            //td.addEventListener("click", () => showTimeRanges(rd));

            td.addEventListener("click", () => {  openDayTimeline(dateStr);});


            const bar = document.createElement("div");
            bar.className = `
                w-full
                h-4
                ${info.color}
                hover:opacity-80`;

                // bar không bắt event → click vẫn ăn vào td
                bar.style.pointerEvents = "none";

                td.appendChild(bar);
                tr.appendChild(td);

            

            
        }

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    monthContainer.appendChild(table);
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

// Đã thất sủng nhưng không muốn xóa hẳn
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

// Mở bảng timeline ngày ============================
function openDayTimeline(dateStr) {
    if (!cachedMonthData) return;

    selectedDay = dateStr;
    currentView = "day";

    document.getElementById("monthTableContainer").classList.add("hidden");
    document.getElementById("dayTableContainer").classList.remove("hidden");

    renderDayTimelineTable(dateStr);
}

function renderDayTimelineTable(dateStr) {
    const container = document.getElementById("dayTableContainer");
    container.innerHTML = "";

    /* ===== HEADER TITLE ===== */
    const header = document.createElement("div");
    header.className = "flex items-center justify-between mb-2";

    const title = document.createElement("div");
    title.className = "font-semibold text-lg";
    title.innerText = `Timeline ngày ${dateStr}`;

    const backBtn = document.createElement("button");
    backBtn.className = "px-3 py-1 bg-gray-600 text-white rounded";
    backBtn.innerText = "⬅ Back";
    backBtn.onclick = backToMonthView;

    header.appendChild(title);
    header.appendChild(backBtn);
    container.appendChild(header);

    /* ===== TABLE ===== */
    const table = document.createElement("table");
    table.className = "w-full border-collapse";

    /* ===== THEAD (mốc giờ nằm trong table) ===== */
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");

    const thChannel = document.createElement("th");
    thChannel.className =
        "border p-2 bg-gray-100 text-left font-semibold w-48 sticky left-0 z-10";
    thChannel.innerText = "Channel";

    const thTimeline = document.createElement("th");
    thTimeline.className =
        "border p-2 bg-gray-100 font-semibold";

    thTimeline.appendChild(buildTimeHeader());

    headRow.appendChild(thChannel);
    headRow.appendChild(thTimeline);
    thead.appendChild(headRow);
    table.appendChild(thead);

    /* ===== TBODY ===== */
    const tbody = document.createElement("tbody");

    cachedMonthData.channels.forEach(item => {
        const rd = item.record_days.find(d => d.record_date === dateStr);

        const tr = document.createElement("tr");

        const tdName = document.createElement("td");
        tdName.className =
            "border p-2 font-semibold bg-white sticky left-0";
        tdName.innerText = item.channel.name;

        const tdTimeline = document.createElement("td");
        tdTimeline.className = "border p-2";

        tdTimeline.appendChild(build24hTimeline(rd));

        tr.appendChild(tdName);
        tr.appendChild(tdTimeline);
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

function buildTimeHeader() {
    const wrapper = document.createElement("div");
    wrapper.className =
        "relative w-full h-6 flex text-xs text-gray-700";

    for (let h = 0; h < 24; h++) {
        const tick = document.createElement("div");
        tick.className =
            "flex-1 border-l border-gray-300 pl-1";
        tick.innerText = String(h).padStart(2, "0");
        wrapper.appendChild(tick);
    }

    return wrapper;
}

function build24hTimeline(rd) {
    const wrapper = document.createElement("div");
    wrapper.className =
        "relative w-full h-4 bg-gray-300 rounded overflow-hidden";

    if (!rd || !rd.time_ranges) return wrapper;

    rd.time_ranges.forEach(tr => {
        const startPercent = timeToPercent(tr.start_time);
        const endPercent = timeToPercent(tr.end_time);

        const bar = document.createElement("div");
        bar.className =
            "absolute top-0 h-full bg-green-500 hover:bg-green-600 cursor-pointer";

        bar.style.left = `${startPercent}%`;
        bar.style.width = `${Math.max(endPercent - startPercent, 0.3)}%`;

        bar.title =
            `${tr.start_time.split("T")[1]} → ${tr.end_time.split("T")[1]}`;

        wrapper.appendChild(bar);
    });

    return wrapper;
}



function timeToPercent(iso) {
    const [h, m, s] = iso.split("T")[1].split(":").map(Number);
    return ((h * 3600 + m * 60 + s) / 86400) * 100;
}
function backToMonthView() {
    currentView = "month";
    selectedDay = null;

    document.getElementById("dayTableContainer").classList.add("hidden");
    document.getElementById("monthTableContainer").classList.remove("hidden");
}
function showDayView() {
    document.getElementById("monthTableContainer").classList.add("hidden");
    document.getElementById("dayTableContainer").classList.remove("hidden");
}




// hết timeline ngày ============================

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
