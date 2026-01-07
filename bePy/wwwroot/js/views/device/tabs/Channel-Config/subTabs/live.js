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

    // ===============================
    // Fetch HLS URL với retry khi chưa sẵn sàng
    // ===============================
    async function fetchLiveHlsWithRetry(channelId, retries = 10, delayMs = 1000) {
        for (let i = 0; i < retries; i++) {
            try {
                const resp = await apiFetch(`${API_URL}/api/device/${device.id}/channel/${channelId}/live`);
                if (resp && resp.hls_url) {
                    const fullUrl = `${API_URL}${resp.hls_url}`;
                    return fullUrl;
                }
            } catch (err) {
                // ignore lỗi network
            }
            console.log(`HLS not ready, retrying in ${delayMs}ms... (${i+1}/${retries})`);
            await new Promise(res => setTimeout(res, delayMs));
        }
        throw new Error("HLS URL not ready after retries");
    }

    // ===============================
    // Play HLS và tự retry playlist khi chưa có segment
    // ===============================
    function playHls(url) {
        if (currentHls) {
            currentHls.destroy();
            currentHls = null;
        }

        if (Hls.isSupported()) {
            const hls = new Hls({
                liveSyncDurationCount: 3,
                maxBufferLength: 10,
                maxMaxBufferLength: 20
            });
            hls.loadSource(url);
            hls.attachMedia(videoEl);
            hls.on(Hls.Events.ERROR, function (event, data) {
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response && data.response.code === 404) {
                    console.log("Playlist not ready, retrying...");
                    setTimeout(() => hls.loadSource(url), 1000);
                }
            });
            currentHls = hls;
        } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
            videoEl.src = url;
        }
    }

    channelSelect.addEventListener("change", async () => {
        const channelId = channelSelect.value;
        try {
            const url = await fetchLiveHlsWithRetry(channelId);
            playHls(url);
        } catch (err) {
            console.error("Cannot play HLS:", err);
        }
    });

    // auto play first channel
    try {
        const firstUrl = await fetchLiveHlsWithRetry(channels[0].id);
        playHls(firstUrl);
    } catch (err) {
        console.error("Cannot play first HLS channel:", err);
    }
}
