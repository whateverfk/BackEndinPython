/* =========================
   MOCK DATA
========================= */

const mockDevices = [
    {
        id: 1,
        ip: "128.1.7.1:701",
        username: "admin",
        channels: [
            {
                id: 101,
                name: "Camera 1",
                time_ranges: [
                    { start: "2021-06-05 01:12:10", end: "2021-06-05 05:45:00" },
                    { start: "2021-06-05 07:10:00", end: "2021-06-05 11:00:30" }
                ]
            },
            {
                id: 201,
                name: "Camera 2",
                time_ranges: [
                    { start: "2022-02-11 00:00:00", end: "2022-02-11 23:59:59" }
                ]
            },
            {
                id: 301,
                name: "Camera 3",
                time_ranges: []
            }
        ]
    },
    {
        id: 2,
        ip: "192.168.1.50",
        username: "root",
        channels: [
            {
                id: 101,
                name: "Front Gate",
                time_ranges: []
            },
            {
                id: 102,
                name: "Back Yard",
                time_ranges: [
                    { start: "2023-01-10 09:00:00", end: "2023-01-10 10:30:00" },
                    { start: "2023-01-10 14:00:00", end: "2023-01-10 18:20:00" }
                ]
            }
        ]
    }
];

/* =========================
   ELEMENTS
========================= */

const deviceListEl = document.getElementById("deviceList");
const channelListEl = document.getElementById("channelList");
const channelTitleEl = document.getElementById("channelTitle");

/* =========================
   INIT
========================= */

renderDevices();

/* =========================
   DEVICE LIST
========================= */

function renderDevices() {
    deviceListEl.innerHTML = "";

    mockDevices.forEach((device, index) => {
        const li = document.createElement("li");
        li.className = "device-item" + (index === 0 ? " active" : "");

        li.innerHTML = `
            <div class="device-title">${device.ip}</div>
            <div class="mono">${device.username}</div>
        `;

        li.onclick = () => selectDevice(device, li);
        deviceListEl.appendChild(li);

        if (index === 0) {
            renderChannels(device);
        }
    });
}

/* =========================
   SELECT DEVICE
========================= */

function selectDevice(device, el) {
    document
        .querySelectorAll(".device-item")
        .forEach(x => x.classList.remove("active"));

    el.classList.add("active");
    renderChannels(device);
}

/* =========================
   CHANNEL LIST
========================= */

function renderChannels(device) {
    channelTitleEl.innerText = `Channels - ${device.ip}`;
    channelListEl.innerHTML = "";

    device.channels.forEach(ch => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${ch.id}</td>
            <td>${ch.name}</td>
            <td>${renderTimeRanges(ch.time_ranges)}</td>
        `;

        channelListEl.appendChild(tr);
    });
}

/* =========================
   TIME RANGE RENDER
========================= */

function renderTimeRanges(ranges) {
    if (!ranges || ranges.length === 0) {
        return "<span style='color:#9ca3af'>—</span>";
    }

    return `
        <div class="time-range">
            ${ranges.map(r => `
                <div>${r.start} → ${r.end}</div>
            `).join("")}
        </div>
    `;
}
