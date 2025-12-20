    /* =========================
    AUTH REQUIRED
    ========================= */

    requireAuth();

    /* =========================
    GLOBAL STATE
    ========================= */

    let devicesCache = [];
    let activeDeviceId = null;

    /* =========================
    ELEMENTS
    ========================= */

    const deviceListEl = document.getElementById("deviceList");
    const channelListEl = document.getElementById("channelList");
    const channelTitleEl = document.getElementById("channelTitle");

    /* =========================
    INIT
    ========================= */

    loadChannels();

    /* =========================
    API
    ========================= */

    async function loadChannels() {
        devicesCache = await apiFetch("http://127.0.0.1:8000/api/channels");
        if (!devicesCache || devicesCache.length === 0) {
            renderEmptyState();
            return;
        }

        renderDevices();

        // auto select first device
        selectDevice(devicesCache[0].id);
    }

    /* =========================
    DEVICE LIST
    ========================= */

    function renderDevices() {
        deviceListEl.innerHTML = "";

        devicesCache.forEach(d => {
            const li = document.createElement("li");
            li.className = "device-item";
            li.id = `device-${d.id}`;

            li.innerHTML = `
                <div><strong>IP WEB:</strong> ${d.ip}</div>
                <div class="mono">${d.username}</div>
            `;

            li.onclick = () => selectDevice(d.id);

            deviceListEl.appendChild(li);
        });
    }

    /* =========================
    SELECT DEVICE
    ========================= */

    function selectDevice(deviceId) {
        activeDeviceId = deviceId;

        document
            .querySelectorAll(".device-item")
            .forEach(x => x.classList.remove("active"));

        const activeEl = document.getElementById(`device-${deviceId}`);
        if (activeEl) activeEl.classList.add("active");

        const device = devicesCache.find(d => d.id === deviceId);
        if (!device) return;

        renderChannels(device);
    }

    /* =========================
    CHANNEL LIST
    ========================= */

    function renderChannels(device) {
        channelTitleEl.innerText = `Channels - ${device.ip}`;
        channelListEl.innerHTML = "";

        if (!device.channels || device.channels.length === 0) {
            renderNoChannels();
            return;
        }

        device.channels.forEach(ch => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${escapeHtml(ch.name)}</td>
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
                    <div>
                        ${formatDateTime(r.start)} → ${formatDateTime(r.end)}
                    </div>
                `).join("")}
            </div>
        `;
    }

    /* =========================
    EMPTY STATES
    ========================= */

    function renderEmptyState() {
        deviceListEl.innerHTML = `
            <li style="padding:10px;color:#9ca3af">
                No devices found
            </li>
        `;
        channelListEl.innerHTML = "";
        channelTitleEl.innerText = "Channels";
    }

    function renderNoChannels() {
        channelListEl.innerHTML = `
            <tr>
                <td colspan="3" style="text-align:center;color:#9ca3af">
                    No channel data
                </td>
            </tr>
        `;
    }

    /* =========================
    UTILITIES
    ========================= */

    function formatDateTime(v) {
        if (!v) return "";
        return v.replace("T", " ").replace("Z", "");
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.innerText = text;
        return div.innerHTML;
    }
