let devicesCache = [];

async function loadDevices() {
    devicesCache = await apiFetch('http://127.0.0.1:8000/api/devices');
    if (!devicesCache) return;

    const list = document.getElementById('list');
    list.innerHTML = '';

    devicesCache.forEach(d => {
        const li = document.createElement('li');
        li.id = `row-${d.id}`;

        li.innerHTML = `
        <div class="device-header">
            <div class="device-title">
                IP: ${d.ip_web} - ${d.brand}
            </div>
            <button onclick="editDevice(${d.id})">Edit</button>
        </div>

        <div class="device-actions">
            <label>
                <input type="checkbox"
                       data-id="${d.id}"
                       ${d.is_checked ? 'checked' : ''}
                       onchange="toggleActive(this)">
                Active
            </label>

            <label>
                <input type="checkbox"
                       data-id="${d.id}"
                       onchange="toggleDelete(this)">
                Delete
            </label>
        </div>
        `;

        list.appendChild(li);
    });
}

function editDevice(id) {
    location.href = `./index.html?id=${id}`;
}

function toggleActive(chk) {
    if (!chk.checked) return;

    const row = chk.closest('li');
    const del = row.querySelector('input[type="checkbox"]:not(:checked)');
    if (del) del.checked = false;
}

function toggleDelete(chk) {
    const row = chk.closest('li');
    chk.checked
        ? row.classList.add('mark-delete')
        : row.classList.remove('mark-delete');
}

async function confirmChanges() {

    // ✅ UPDATE is_checked
    for (let d of devicesCache) {
        const chk = document.querySelector(`input[data-id="${d.id}"]`);

        if (chk && chk.checked !== d.is_checked) {
            d.is_checked = chk.checked;

            // ✅ Gửi đúng snake_case
            const payload = {
                ip_nvr: d.ip_nvr,
                ip_web: d.ip_web,
                username: d.username,
                password: d.password,
                brand: d.brand,
                is_checked: d.is_checked
            };

            await apiFetch(`http://127.0.0.1:8000/api/devices/${d.id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
        }
    }

    // ✅ DELETE
    const deleteRows = document.querySelectorAll('.mark-delete');
    for (let row of deleteRows) {
        const id = row.id.replace('row-', '');
        await apiFetch(`http://127.0.0.1:8000/api/devices/${id}`, { method: 'DELETE' });
    }

    loadDevices();
}

loadDevices();
