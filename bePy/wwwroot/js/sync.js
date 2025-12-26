import { API_URL } from "./config.js";

// LOAD CONFIG
async function loadSetting() {
    const setting = await apiFetch(`${API_URL}/api/sync/setting`);
    if (!setting) return;

    enableSync.checked = setting.is_enabled;
    interval.value = setting.interval_minutes;
}

// SAVE CONFIG
async function saveSetting() {
    const setting = {
        is_enabled: enableSync.checked,
        interval_minutes: parseInt(interval.value)
    };

    await apiFetch(`${API_URL}/api/sync/setting`, {
        method: 'POST',
        body: JSON.stringify(setting)
    });

    alert("Setting saved");
}

// SYNC NOW
async function syncNow() {
    const status = document.getElementById('syncStatus');
    status.innerText = 'Syncing...';

    const result = await apiFetch(`${API_URL}/api/sync/now`, {
        method: 'POST'
    });

    status.innerText = result?.message || result || 'Sync done';
    loadLogs();
}

// LOAD LOGS
async function loadLogs() {
    const logs = await apiFetch(`${API_URL}/api/logs`);
    if (!logs) return;

    const list = document.getElementById('logList');
    list.innerHTML = '';

    logs.forEach(l => {
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${new Date(l.sync_time).toLocaleString()}</strong><br/>
            ${l.message}
        `;
        list.appendChild(li);
    });
}

// INIT
document.addEventListener("DOMContentLoaded", () => {
    document
      .getElementById("btnSaveSetting")
      .addEventListener("click", saveSetting);

    document
      .getElementById("btnSyncNow")
      .addEventListener("click", syncNow);

    loadSetting();
    loadLogs();
});
