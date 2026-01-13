import { API_URL } from "../../../../../config.js";

let currentHls = null;
let currentDeviceId = null;
let currentChannelId = null;
let stopTimer = null;
let heartbeatTimer = null;

export function startHeartbeat(deviceId, channelId) {
    stopHeartbeat();

    heartbeatTimer = setInterval(async () => {
        try {
            await apiFetch(
                `${API_URL}/api/device/${deviceId}/channel/${channelId}/heartbeat`,
                { method: "POST" }
            );
        } catch (e) {
            console.warn("[LIVE] heartbeat failed");
        }
    }, 5000); // 5s
}

export function stopHeartbeat() {
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
}

export function setLiveContext({ hls, deviceId, channelId }) {
    currentHls = hls;
    currentDeviceId = deviceId;
    currentChannelId = channelId;
}

export function hasLive() {
    return !!(currentHls && currentChannelId && currentDeviceId);
}

export async function stopLiveAndCleanup(delayMs = 0) {
    stopHeartbeat();

    if (!hasLive()) return;

    const deviceId = currentDeviceId;
    const channelId = currentChannelId;
    const hls = currentHls;

    const doStop = async () => {
        try {
            await apiFetch(
                `${API_URL}/api/device/${deviceId}/channel/${channelId}/stop`,
                { method: "POST" }
            );
            console.log("[LIVE] stopped", channelId);
        } catch (err) {
            console.warn("[LIVE] stop failed", err);
        }

        try { 
            hls?.stopLoad?.(); 
            hls?.detachMedia?.();
            hls?.destroy?.();

        } catch {}

        const video = document.getElementById("liveVideo");
        if (video) {
            
            video.src = "";
            //video.removeAttribute("src"); 
            video.load();
        }

        if (
            currentDeviceId === deviceId &&
            currentChannelId === channelId
        ) {
            currentHls = null;
            currentDeviceId = null;
            currentChannelId = null;
        }
    };

    if (delayMs > 0) {
        setTimeout(doStop, delayMs);
    } else {
        await doStop();
    }
}

