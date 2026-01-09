import { API_URL } from "../../../../../config.js";

const MODE_LABEL_MAP = {
    CMR: "Continuous",
    MOTION: "Motion",
    ALARM: "Alarm",
    EDR: "Motion | Alarm",
    ALARMANDMOTION: "Motion & Alarm",
    AllEvent: "Event"
};
const data =null

const DAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
];

const MODE_COLOR_MAP = {
    CMR: "#10B981",
    MOTION: "#3B82F6",
    ALARM: "#EF4444",
    EDR: "#F59E0B",
    ALARMANDMOTION: "#8B5CF6",
    AllEvent: "#9CA3AF"
};

export async function renderScheduleTab(device) {
    const box = document.getElementById("channelSubContent");
    if (!box) return;

    const channelsResp = await apiFetch(
        `${API_URL}/api/devices/${device.id}/channels`
    );
    const channels = channelsResp;

    if (!channels.length) {
        box.innerHTML = `<div>No channel</div>`;
        return;
    }

    box.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center gap-4">
                <select id="scheduleChannelSelect"
                    class="border rounded px-3 py-1">
                    ${channels.map(ch =>
                        `<option value="${ch.id}">${ch.name}</option>`
                    ).join("")}
                </select>

                <label class="flex items-center gap-2 text-sm">
                    <input type="checkbox" id="scheduleEnableCheckbox" disabled />
                    Enable Schedule
                </label>

                <div class="text-sm">
                    Default Mode:
                    <span id="defaultMode" class="font-semibold"></span>
                </div>

                <button id="syncScheduleBtn"
                    class="ml-auto px-3 py-1 border rounded
                        bg-blue-600 text-white text-sm
                        hover:bg-blue-700">
                    Sync from Device
                </button>
            </div>

            <div id="scheduleTimeline" class="space-y-2"></div>

            <div class="flex gap-4 text-sm flex-wrap">
                ${Object.entries(MODE_COLOR_MAP).map(
                    ([mode, color]) => `
                    <div class="flex items-center gap-2">
                        <span class="w-4 h-4 rounded"
                            style="background:${color}"></span>
                        ${MODE_LABEL_MAP[mode] || mode}
                    </div>`).join("")}
            </div>
        </div>
    `;

    const select = document.getElementById("scheduleChannelSelect");
    const syncBtn = document.getElementById("syncScheduleBtn");

    select.addEventListener("change", () => {
        loadChannelSchedule(device.id, select.value);
    });

    syncBtn.addEventListener("click", async () => {
        await syncFromNvr(device.id);
        await loadChannelSchedule(device.id, select.value);
    });

    // load mặc định
    const firstChannelId = channels[0].id;
    let data = await apiFetch(
        `${API_URL}/api/device/${device.id}/channel/${firstChannelId}/infor/recording-mode`
    );

    // Nếu chưa có timeline hoặc rỗng → tự sync 1 lần
    if (!data || !data.timeline || data.timeline.length === 0) {
        await syncFromNvr(device.id);
        data = await apiFetch(
            `${API_URL}/api/device/${device.id}/channel/${firstChannelId}/infor/recording-mode`
        );
    }

    // Cập nhật UI
    document.getElementById("defaultMode").textContent =
        MODE_LABEL_MAP[data.default_mode] || "-";

    const checkbox = document.getElementById("scheduleEnableCheckbox");
    if (checkbox) {
        checkbox.checked = !!data.schedule_enable;
    }

    renderTimeline(data.timeline);
}



async function loadChannelSchedule(deviceId, channelId) {
    const resp = await apiFetch(
        `${API_URL}/api/device/${deviceId}/channel/${channelId}/infor/recording-mode`
    );
    const data = resp;

    // Cập nhật default mode
    document.getElementById("defaultMode").textContent =
        MODE_LABEL_MAP[data.default_mode] || "-";

    // Cập nhật checkbox
    const checkbox = document.getElementById("scheduleEnableCheckbox");
    if (checkbox) {
        //checkbox.checked = !!data.schedule_enable; // true/false
        checkbox.checked = !!data.schedule_enable;
    }

    // Vẽ timeline
    renderTimeline(data.timeline);
}

function renderTimeline(timeline) {
    const container = document.getElementById("scheduleTimeline");
    container.innerHTML = "";

    DAYS.forEach(day => {
        const row = document.createElement("div");
        row.className = "flex items-center gap-2 relative";

        row.innerHTML = `
            <div class="w-24 text-sm">${day}</div>
            <div class="relative flex-1 h-6 bg-gray-200 rounded"></div>
        `;

        const bar = row.querySelector(".relative");

        timeline.forEach(t => {
            // same-day
            if (t.day_start === t.day_end && t.day_start === day) {
                let start = timeToPercent(t.time_start);
                let end = timeToPercent(t.time_end);

                if (start === end) end = 100;

                drawSegment(
                    bar,
                    start,
                    end,
                    t.mode,
                    `${t.time_start} - ${t.time_end} (${MODE_LABEL_MAP[t.mode]})`
                );
            }

            // cross-day: phần day_start
            if (t.day_start === day && t.day_start !== t.day_end) {
                drawSegment(
                    bar,
                    timeToPercent(t.time_start),
                    100,
                    t.mode,
                    `${t.time_start} - 24:00 (${MODE_LABEL_MAP[t.mode]})`
                );
            }

            // cross-day: phần day_end
            if (t.day_end === day && t.day_start !== t.day_end) {
                drawSegment(
                    bar,
                    0,
                    timeToPercent(t.time_end),
                    t.mode,
                    `00:00 - ${t.time_end} (${MODE_LABEL_MAP[t.mode]})`
                );
            }
        });

        container.appendChild(row);
    });
}





function timeToPercent(timeStr) {
    const [h, m, s] = timeStr.split(":").map(Number);
    const total = h * 3600 + m * 60 + (s || 0);
    return (total / 86400) * 100;
}


async function syncFromNvr(deviceId) {
    const btn = document.getElementById("syncScheduleBtn");

    try {
        btn.disabled = true;
        btn.textContent = "Syncing...";

        await apiFetch(
            `${API_URL}/api/device/${deviceId}/channels/recording-mode/sync`,
            { method: "POST" }
        );


    } catch (err) {
        alert("Sync failed");
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = "Sync from device";
    }
}
function drawSegment(bar, startPercent, endPercent, mode, tooltip) {
    if (endPercent <= startPercent) return;

    const seg = document.createElement("div");
    seg.className = "absolute h-full rounded cursor-pointer transition duration-150";
    seg.style.left = `${startPercent}%`;
    seg.style.width = `${endPercent - startPercent}%`;
    seg.style.background = MODE_COLOR_MAP[mode] || "#000";
    seg.title = tooltip;

    bar.appendChild(seg);
}
