import { API_URL } from "../../../../../config.js";

import { setLiveContext, stopLiveAndCleanup, startHeartbeat, stopHeartbeat } from "./liveController.js";


const liveContainerId = "channelSubContent";

export async function renderLiveViewTab(device) {
    const box = document.getElementById(liveContainerId);
    if (!box) return;

    box.innerHTML = `
        <div class="p-4 bg-gray-50 border rounded">
            <label class="block font-semibold mb-2">Select Channel</label>
            <select id="channelSelect" class="border p-1 rounded mb-4 w-full"></select>

            <video id="liveVideo"
                controls autoplay
                class="w-full rounded border"
                style="height:360px"></video>
        </div>
    `;

    const videoEl = document.getElementById("liveVideo");
    const channelSelect = document.getElementById("channelSelect");

    const channels = await apiFetch(`${API_URL}/api/devices/${device.id}/channels`);
    if (!channels?.length) return;

    channels.forEach(ch => {
        const opt = document.createElement("option");
        opt.value = ch.id;
        opt.textContent = ch.name;
        channelSelect.appendChild(opt);
    });

    
async function startLive(channelId) {
    await stopLiveAndCleanup();

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


    channelSelect.onchange = async () => {
        await startLive(channelSelect.value);
    };

    // auto play first
    await startLive(channels[0].id);
}
