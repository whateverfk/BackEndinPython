import { API_URL } from "./config.js";


let devicesCache = [];

function renderDevices() {
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
                <button class="btn-edit" data-id="${d.id}">Edit</button>
            </div>

            <div class="device-actions">
                <label>
                    <input type="checkbox"
                           class="chk-active"
                           data-id="${d.id}"
                           ${d.is_checked ? 'checked' : ''}>
                    Active
                </label>

                <label>
                    <input type="checkbox"
                           class="chk-delete"
                           data-id="${d.id}">
                    Delete
                </label>
            </div>
        `;

        list.appendChild(li);
    });
}

async function loadDevices() {
    devicesCache = await apiFetch(`${API_URL}/api/devices`);
    if (!devicesCache) return;
    renderDevices();
}

function handleListClick(e) {
    const btn = e.target.closest('.btn-edit');
    if (!btn) return;

    const id = btn.dataset.id;
    location.href = `./index.html?id=${id}`;
}

function handleActiveChange(e) {
    if (!e.target.classList.contains('chk-active')) return;

    if (!e.target.checked) return;

    const row = e.target.closest('li');
    const del = row.querySelector('.chk-delete');
    if (del) del.checked = false;
}

function handleDeleteChange(e) {
    if (!e.target.classList.contains('chk-delete')) return;

    const row = e.target.closest('li');
    e.target.checked
        ? row.classList.add('mark-delete')
        : row.classList.remove('mark-delete');
}

async function confirmChanges() {

    // UPDATE
    for (let d of devicesCache) {
        const chk = document.querySelector(`.chk-active[data-id="${d.id}"]`);
        if (chk && chk.checked !== d.is_checked) {

            const payload = {
                ip_nvr: d.ip_nvr,
                ip_web: d.ip_web,
                username: d.username,
                password: d.password,
                brand: d.brand,
                is_checked: chk.checked
            };

            await apiFetch(`${API_URL}/api/devices/${d.id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
        }
    }

    // DELETE
    const deleteRows = document.querySelectorAll('.mark-delete');
    for (let row of deleteRows) {
        const id = row.id.replace('row-', '');
        await apiFetch(`${API_URL}/api/devices/${id}`, { method: 'DELETE' });
    }

    loadDevices();
}

// INIT
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('list')
        .addEventListener('click', handleListClick);

    document.getElementById('list')
        .addEventListener('change', handleActiveChange);

    document.getElementById('list')
        .addEventListener('change', handleDeleteChange);

    document.getElementById('btnConfirm')
        .addEventListener('click', confirmChanges);

    loadDevices();
});
