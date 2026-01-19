import { API_URL } from "../../../../../config.js";
let capabilitiesCache = {}; // key: channelId, value: capabilities
let currentChannelId = null;

let currentChannel = null;
import {
  setLiveContext,
  stopLiveAndCleanup,
  startHeartbeat
} from "./liveController.js";

const FIXED_QUALITY_LABELS = {
    90: "Highest",
    75: "Higher",
    60: "Medium",
    45: "Low",
    30: "Lower",
    20: "Lowest"
};
let avgBitrateValue = null;
let maxBitrateValue = null;

let currentInfo = null;
let currentCap = null;

export async function renderConfigTab(device) {
    const box = document.getElementById("channelSubContent");

    box.innerHTML = `<div class="text-gray-500">Loading channels...</div>`;

    const channels = await apiFetch(
        `${API_URL}/api/devices/${device.id}/channels`
    );

    if (!channels || channels.length === 0) {
        box.innerHTML = `<div>No channels found</div>`;
        return;
    }

    currentChannel = channels[0];
    currentChannelId = currentChannel.id;

    box.innerHTML = `
        <div class="space-y-4">
            ${renderChannelSelector(channels)}

            <div class="grid grid-cols-2 gap-4">
                <div id="liveBox"
                     class="bg-gray-50 border rounded p-2"></div>

                <div id="channelForm"></div>
            </div>
        </div>
    `;

    // ⚠️ CHỈ render live + form SAU KHI DOM ĐÃ CÓ liveBox
    await renderLiveInConfig(device, currentChannelId);
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
  if (currentChannelId === channelId) return;

  await stopLiveAndCleanup();

  currentChannelId = Number(channelId);

  await renderLiveInConfig(window.currentDevice, currentChannelId);
  await loadChannelForm(window.currentDevice, { id: currentChannelId });
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
    window.onH265PlusChange();
}



function renderChannelForm(info, cap, device, channel) {

    currentInfo = info;
    currentCap = cap;

    avgBitrateValue =
        info?.vbr_average_cap ?? cap.vbr.upper_cap.min;

    maxBitrateValue =
        info?.vbr_upper_cap ?? cap.vbr.upper_cap.max;
    const resolutions = cap.resolutions.map(r => `${r.width}x${r.height}`);

    // Giá trị hiện tại (fallback)
    const curResolution = info?.resolution_width && info?.resolution_height
        ? `${info.resolution_width}x${info.resolution_height}`
        : resolutions[0];

    const curCodec = info?.video_codec || cap.video_codec[0];
    const curFps = info?.max_frame_rate || cap.max_frame_rates[0];
    const curVbr = info?.vbr_average_cap ?? info?.vbr_upper_cap;
    const curMotion = info?.motion_detect ?? false;
    const curH265Plus = info?.h265_plus ?? false;

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
            <span>Video encoding</span>
            <select id="codec" class="border p-2 w-full">
                ${cap.video_codec.map(c => `
                    <option value="${c}" ${c === curCodec ? "selected" : ""}>${c}</option>
                `).join("")}
            </select>
        </label>

        <label class="block">
            <span>Max Frame Rate</span>
            <select id="fps" class="border p-2 w-full">
                ${cap.max_frame_rates.map(f => {
                    const isFull = f === 0;
                    const display = isFull ? "Full Frame Rate" : (f / 100);

                    return `
                        <option value="${f}" ${f === curFps ? "selected" : ""}>
                            ${display}
                        </option>
                    `;
                }).join("")}


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
            <span>H.265+ Mode</span>
            <select id="h265_plus" class="border p-2 w-full" onchange="onH265PlusChange()">
                <option value="true" ${curH265Plus ? "selected" : ""}>On (Average Bitrate)</option>
                <option value="false" ${!curH265Plus ? "selected" : ""}>Off (Max Bitrate)</option>
            </select>
        </label>



        <label class="block">
            <span id="bitrateLabel"></span>
            <input id="bitrate"
                type="number"
                class="border p-2 w-full"/>

            <p id="bitrateWarning"
            class="text-sm text-red-500 mt-1 hidden">
                Bitrate must be within allowed range
            </p>
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


window.onH265PlusChange = function () {
    const isH265Plus =
        document.getElementById("h265_plus").value === "true";

    const label = document.getElementById("bitrateLabel");
    const input = document.getElementById("bitrate");

    const min = currentCap.vbr.upper_cap.min;
    const max = currentCap.vbr.upper_cap.max;

    input.min = min;
    input.max = max;

    if (isH265Plus) {
        label.innerText = `Average Bitrate (${min} – ${max})`;
        input.value = avgBitrateValue;
    } else {
        label.innerText = `Max Bitrate (${min} – ${max})`;
        input.value = maxBitrateValue;
    }
    document.getElementById("bitrateWarning")?.classList.add("hidden");
    document.getElementById("bitrate")?.classList.remove("border-red-500");

};

document.addEventListener("input", (e) => {
    if (e.target.id !== "bitrate") return;

    const input = e.target;
    const warning = document.getElementById("bitrateWarning");

    const v = Number(input.value);
    const min = Number(input.min);
    const max = Number(input.max);

    if (Number.isNaN(v)) {
        warning.classList.add("hidden");
        input.classList.remove("border-red-500");
        return;
    }

    const outOfRange = v < min || v > max;

    if (outOfRange) {
        warning.textContent = `Allowed range: ${min} – ${max}`;
        warning.classList.remove("hidden");
        input.classList.add("border-red-500");
    } else {
        warning.classList.add("hidden");
        input.classList.remove("border-red-500");
    }

    const isH265Plus =
        document.getElementById("h265_plus").value === "true";

    if (isH265Plus) {
        avgBitrateValue = v;
    } else {
        maxBitrateValue = v;
    }
});





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

    const isH265Plus = document.getElementById("h265_plus").value === "true";
    const bitrateValue = Number(document.getElementById("bitrate").value);
    const bitrateInput = document.getElementById("bitrate");
    const v = Number(bitrateInput.value);
    const min = Number(bitrateInput.min);
    const max = Number(bitrateInput.max);

    if (Number.isNaN(v) || v < min || v > max) {
        const warning = document.getElementById("bitrateWarning");
        warning.textContent = `Bitrate must be between ${min} and ${max}`;
        warning.classList.remove("hidden");
        bitrateInput.classList.add("border-red-500");
        return; // 
    }

    const payload = {
        channel_name: document.getElementById("name").value,
        resolution_width: Number(w),
        resolution_height: Number(h),
        video_codec: document.getElementById("codec").value,
        max_frame_rate: Number(document.getElementById("fps").value) ,
        fixed_quality: Number(document.getElementById("fixed_quality").value),
        motion_detect: document.getElementById("motion_detect").checked,

        h265_plus: isH265Plus,
        vbr_average_cap: avgBitrateValue,
        vbr_upper_cap: maxBitrateValue,
    };


    console.log("Payload sent to API:", payload);


    try {
    await apiFetch(
        `${API_URL}/api/device/${d.id}/channel/${c.id}/infor`,
        {
            method: "PUT",
            body: JSON.stringify(payload)
        }
    );

    showToast("Saved successfully", "success");

} catch (err) {
    console.error(err);
    showToast("Save failed", "error");
}

};
window.showToast = function (message, type = "success", duration = 3000) {
    const toast = document.createElement("div");

    const colors = {
        success: "bg-green-600",
        error: "bg-red-600",
        warning: "bg-yellow-500",
        info: "bg-blue-500"
    };

    toast.className = `
        fixed bottom-4 right-4 z-50
        px-4 py-2 rounded shadow-lg text-white
        transition-all duration-300
        ${colors[type] || colors.success}
    `;

    toast.textContent = message;

    document.body.appendChild(toast);

    // fade in
    requestAnimationFrame(() => {
        toast.classList.add("opacity-100");
    });

    // auto remove
    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

async function renderLiveInConfig(device, channelId) {
  const box = document.getElementById("liveBox");
  if (!box) return;

  box.innerHTML = `
    <video id="liveVideo"
      autoplay controls
      class="w-full rounded border"
      style="height:360px"></video>
  `;

  const videoEl = document.getElementById("liveVideo");

  const resp = await apiFetch(
    `${API_URL}/api/device/${device.id}/channel/${channelId}/live`
  );

  const hlsUrl = `${API_URL}${resp.hls_url}`;

  let hls = null;
  if (Hls.isSupported()) {
    hls = new Hls({ liveSyncDurationCount: 3 });
    hls.loadSource(`${hlsUrl}?v=${Date.now()}`);
    hls.attachMedia(videoEl);
  } else {
    videoEl.src = hlsUrl;
  }

  setLiveContext({ hls, deviceId: device.id, channelId });
  startHeartbeat(device.id, channelId);
}
