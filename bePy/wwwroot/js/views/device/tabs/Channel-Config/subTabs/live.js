


import { API_URL } from "../../../../../config.js";
const liveContainerId = "channelSubContent";
let currentHls = null;
export async function renderLiveViewTab(device) {
    const box = document.getElementById(liveContainerId);
    if (!box) return;

    // fetch channel list
    const resp = await apiFetch(`${API_URL}/api/devices/${device.id}/channels`);
    const channels = await resp;

    if (!channels || channels.length === 0) {
        box.innerHTML = `<div class="p-4 bg-gray-50 border rounded text-gray-500">
            No channels available for this device
        </div>`;
        return;
    }

    box.innerHTML = `
        <div class="p-4 bg-gray-50 border rounded text-gray-500">
            <label for="channelSelect" class="block font-semibold mb-2">Select Channel:</label>
            <select id="channelSelect" class="border p-1 rounded mb-4 w-full"></select>
            <video
                id="liveVideo"
                controls
                autoplay
                class="w-full rounded border"
                style="height:360px;"
            ></video>
        </div>
    `;

    const channelSelect = document.getElementById("channelSelect");
    const videoEl = document.getElementById("liveVideo");

    // Render dropdown
    channels.forEach(ch => {
        const option = document.createElement("option");
        option.value = ch.id;
        option.textContent = ch.name;
        channelSelect.appendChild(option);
    });

    // Hàm fetch HLS URL
    async function fetchLiveHls(channelId) {
        const resp = await apiFetch(`${API_URL}/api/device/${device.id}/channel/${channelId}/live`);
        const data = await resp;
        console.log(data.hls_url)
        const fullUrl = `${API_URL}${data.hls_url}`;
        console.log(fullUrl)
        return fullUrl;
    }

    // Hàm play HLS
    function playHls(url) {
        if (currentHls) {
            currentHls.destroy();
            currentHls = null;
        }

        if (Hls.isSupported()) {
            const hls = new Hls();
            hls.loadSource(url);
            hls.attachMedia(videoEl);
            currentHls = hls;
        } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
            videoEl.src = url;
        }
    }

    channelSelect.addEventListener("change", async () => {
        const channelId = channelSelect.value;
        const url = await fetchLiveHls(channelId);
        playHls(url);
    });

    // auto play first channel
    const firstUrl = await fetchLiveHls(channels[0].id);
    playHls(firstUrl);
}
