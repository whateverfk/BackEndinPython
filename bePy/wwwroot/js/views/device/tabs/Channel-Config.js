import { API_URL } from "../../../config.js";
let capabilitiesCache = {}; // key: channelId, value: capabilities

let currentChannel = null;
const FIXED_QUALITY_LABELS = {
    90: "Highest",
    75: "Higher",
    60: "Medium",
    45: "Low",
    30: "Lower",
    20: "Lowest"
};


export async function renderChannelConfig(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `<div class="text-gray-500">Loading channels...</div>`;

    const channels = await apiFetch(
        `${API_URL}/api/devices/${device.id}/channels`
    );

    if (!channels || channels.length === 0) {
        box.innerHTML = `<div>No channels found</div>`;
        return;
    }

    currentChannel = channels[0];

    box.innerHTML = `
        <div class="space-y-4">
            ${renderChannelSelector(channels)}
            <div id="channelForm"></div>
        </div>
    `;

    await loadChannelForm(device, currentChannel);
}
function renderChannelSelector(channels) {
    return `
        <select id="channelSelect"
            class="border rounded p-2 w-64"
            onchange="window.__onChannelChange(this.value)">
            ${channels.map(c => `
                <option value="${c.id}">
                    Channel ${c.name}
                </option>
            `).join("")}
        </select>
    `;
}

window.__onChannelChange = async function (channelId) {
    currentChannel = { id: Number(channelId) };
    await loadChannelForm(window.currentDevice, currentChannel);
};


async function loadChannelForm(device, channel) {
    const form = document.getElementById("channelForm");

    form.innerHTML = `<div class="text-gray-500">Loading channel info...</div>`;

    // 1. Info từ DB
    const info = await apiFetch(
        `${API_URL}/api/device/${device.id}/channel/${channel.id}/infor`
    );

    // 2. Capabilities (cache theo channel)
    if (!capabilitiesCache[channel.id]) {
        capabilitiesCache[channel.id] = await apiFetch(
            `${API_URL}/api/device/${device.id}/channel/${channel.id}/infor/capabilities`
        );
    }

    form.innerHTML = renderChannelForm(info, capabilitiesCache[channel.id], device, channel);
}



function renderChannelForm(info, cap, device, channel) {
    const resolutions = cap.resolutions.map(r => `${r.width}x${r.height}`);

    // Giá trị hiện tại (fallback)
    const curResolution = info?.resolution_width && info?.resolution_height
        ? `${info.resolution_width}x${info.resolution_height}`
        : resolutions[0];

    const curCodec = info?.video_codec || cap.video_codec[0];
    const curFps = info?.max_frame_rate || cap.max_frame_rates[0];
    const curVbr = info?.vbr_average_cap ?? cap.vbr.upper_cap.min;
    const curMotion = info?.motion_detect ?? false;
    const curQuality =
    info?.fixed_quality ??
    cap.fixed_quality?.current ??
    cap.fixed_quality?.default;


    return `
    <div class="bg-gray-50 p-4 border rounded space-y-3">

        <label class="block">
            <span>Name</span>
            <input id="name" value="${info.channel_name || ""}"
                class="border p-2 w-full"/>
        </label>

        <label class="block">
            <span>Resolution</span>
            <select id="resolution" class="border p-2 w-full">
                ${resolutions.map(r => `
                    <option value="${r}" ${r === curResolution ? "selected" : ""}>
                        ${r}
                    </option>
                `).join("")}
            </select>
        </label>

        <label class="block">
            <span>Codec</span>
            <select id="codec" class="border p-2 w-full">
                ${cap.video_codec.map(c => `
                    <option value="${c}" ${c === curCodec ? "selected" : ""}>${c}</option>
                `).join("")}
            </select>
        </label>

        <label class="block">
            <span>Max Frame Rate</span>
            <select id="fps" class="border p-2 w-full">
                ${cap.max_frame_rates.map(f => `
                    <option value="${f}" ${f === curFps ? "selected" : ""}>${f}</option>
                `).join("")}
            </select>
        </label>
        <label class="block">
            <span>Video Quality</span>
            <select id="fixed_quality" class="border p-2 w-full">
                ${cap.fixed_quality.options.map(q => `
                    <option value="${q}" ${q === curQuality ? "selected" : ""}>
                        ${FIXED_QUALITY_LABELS[q] || q}
                    </option>
                `).join("")}
            </select>
        </label>


        <label class="block">
            <span>Average Bitrate (${cap.vbr.upper_cap.min} – ${cap.vbr.upper_cap.max})</span>
            <input id="vbr" type="number"
                min="${cap.vbr.upper_cap.min}"
                max="${cap.vbr.upper_cap.max}"
                value="${curVbr}"
                class="border p-2 w-full"/>
        </label>

        <label class="block flex items-center gap-2">
            <input type="checkbox" id="motion_detect" ${curMotion ? "checked" : ""}/>
            <span>Motion Detection</span>
        </label>

        <div class="flex gap-2 pt-2">
            <button onclick="syncChannel()"
                class="px-4 py-2 bg-blue-500 text-white rounded">
                Sync from device
            </button>

            <button onclick="saveChannel()"
                class="px-4 py-2 bg-green-600 text-white rounded">
                Save
            </button>
        </div>
    </div>
    `;
}




window.syncChannel = async function () {
    const d = window.currentDevice;
    const c = currentChannel;

    await apiFetch(
        `${API_URL}/api/device/${d.id}/channel/${c.id}/infor/sync`
    );

    await loadChannelForm(d, c);
};

window.saveChannel = async function () {
    const d = window.currentDevice;
    const c = currentChannel;

    const [w, h] = document.getElementById("resolution").value.split("x");

    const payload = {
        channel_name: document.getElementById("name").value,
        resolution_width: Number(w),
        resolution_height: Number(h),
        video_codec: document.getElementById("codec").value,
        max_frame_rate: Number(document.getElementById("fps").value),
        vbr_average_cap: Number(document.getElementById("vbr").value),
        fixed_quality: Number(
            document.getElementById("fixed_quality").value
        ),
        motion_detect: document.getElementById("motion_detect").checked
    };

    await apiFetch(
        `${API_URL}/api/device/${d.id}/channel/${c.id}/infor`,
        {
            method: "PUT",
            body: JSON.stringify(payload)
        }
    );

    alert("Saved successfully");
};
