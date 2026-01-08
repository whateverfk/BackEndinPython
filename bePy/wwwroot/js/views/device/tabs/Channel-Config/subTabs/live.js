import { API_URL } from "../../../../../config.js";
const liveContainerId = "channelSubContent";
let currentHls = null;
let stopTimer = null;
let currentUserId = null; // lấy từ token hoặc login session

export async function renderLiveViewTab(device, userId) {
    currentUserId = userId;
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

    channels.forEach(ch => {
        const option = document.createElement("option");
        option.value = ch.id;
        option.textContent = ch.name;
        channelSelect.appendChild(option);
    });

    async function fetchLiveHlsWithRetry(channelId, retries = 10, delayMs = 1000) {
        for (let i = 0; i < retries; i++) {
            try {
                const resp = await apiFetch(`${API_URL}/api/device/${device.id}/channel/${channelId}/live`);
                if (resp && resp.hls_url) return `${API_URL}${resp.hls_url}`;
            } catch {}
            await new Promise(res => setTimeout(res, delayMs));
        }
        throw new Error("HLS URL not ready after retries");
    }

    function playHls(url, channelId) {
        if (currentHls) {
            currentHls.destroy();
            currentHls = null;
        }

        if (Hls.isSupported()) {
            const hls = new Hls({ liveSyncDurationCount: 3, maxBufferLength: 10, maxMaxBufferLength: 20 });
            hls.loadSource(url);
            hls.attachMedia(videoEl);
            hls.on(Hls.Events.ERROR, (event, data) => {
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response && data.response.code === 404) {
                    setTimeout(() => hls.loadSource(url), 1000);
                }
            });
            currentHls = hls;
        } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
            videoEl.src = url;
        }

        // lưu channelId hiện tại
        if (currentHls) currentHls.channelId = channelId;
    }

    // delayed stop
    async function scheduleStop(channelId, delayMs = 7000) {
        if (stopTimer) clearTimeout(stopTimer);
        stopTimer = setTimeout(async () => {
            try {
                await apiFetch(`${API_URL}/api/device/${device.id}/channel/${channelId}/stop`, {
                    method: 'POST',
                   
                    headers: { 'Content-Type': 'application/json' }
                });
                console.log("Stopped channel after delay:", channelId);
            } catch (err) {
                console.warn("Failed to stop channel", err);
            }
        }, delayMs);
    }

    channelSelect.addEventListener("change", async () => {
        // schedule stop cho channel cũ
        if (currentHls && currentHls.channelId) scheduleStop(currentHls.channelId, 7000);

        try {
            const url = await fetchLiveHlsWithRetry(channelSelect.value);
            playHls(url, channelSelect.value);
        } catch (err) {
            console.error("Cannot play HLS:", err);
        }
    });

    // auto play first channel
    try {
        const firstUrl = await fetchLiveHlsWithRetry(channels[0].id);
        playHls(firstUrl, channels[0].id);
    } catch (err) {
        console.error("Cannot play first HLS channel:", err);
    }

    // stop khi đóng tab hoặc reload
    window.addEventListener("beforeunload", async () => {
        if (currentHls && currentHls.channelId) scheduleStop(currentHls.channelId, 7000);
    });
}
