import { API_URL } from "../../../../../config.js";

let currentHls = null;
let currentDeviceId = null;
let currentChannelId = null;
let stopTimer = null;

export function setLiveContext({ hls, deviceId, channelId }) {
    currentHls = hls;
    currentDeviceId = deviceId;
    currentChannelId = channelId;
}

export function hasLive() {
    return !!(currentHls && currentChannelId && currentDeviceId);
}

export async function stopLiveAndCleanup(delayMs = 5000) {
    if (!hasLive()) return;

    // capture context TẠI THỜI ĐIỂM STOP ĐƯỢC LÊN LỊCH
    const deviceId = currentDeviceId;
    const channelId = currentChannelId;
    const hls = currentHls;

    if (stopTimer) {
        clearTimeout(stopTimer);
        stopTimer = null;
    }

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
            hls?.destroy?.();
        } catch {}

        // chỉ clear global state nếu nó VẪN là channel đó
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
        stopTimer = setTimeout(doStop, delayMs);
    } else {
        await doStop();
    }
}
