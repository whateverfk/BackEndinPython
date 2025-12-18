// LOAD CONFIG
async function loadSetting() {
    const setting = await apiFetch('http://127.0.0.1:8000/api/sync/setting');
    if (!setting) return;

    // ✅ backend trả snake_case
    enableSync.checked = setting.is_enabled;
    interval.value = setting.interval_minutes;
}

// SAVE CONFIG
async function saveSetting() {
    // ✅ gửi snake_case
    const setting = {
        is_enabled: enableSync.checked,
        interval_minutes: parseInt(interval.value)
    };

    await apiFetch('http://127.0.0.1:8000/api/sync/setting', {
        method: 'POST',
        body: JSON.stringify(setting)
    });

    alert("Setting saved");
}

// SYNC NOW
async function syncNow() {
    const status = document.getElementById('syncStatus');
    status.innerText = 'Syncing...';

    const result = await apiFetch('http://127.0.0.1:8000/api/sync/now', {
        method: 'POST'
    });

    status.innerText = result?.message || result || 'Sync done';

    loadLogs();
}

// LOAD LOGS
async function loadLogs() {
    const logs = await apiFetch('http://127.0.0.1:8000/api/logs');
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
loadSetting();
loadLogs();
