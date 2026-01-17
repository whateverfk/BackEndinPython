import { API_URL } from "../../config.js";


let devicesCache = [];

export async function renderDeviceList(container) {
    container.innerHTML = `
        <h2 class="text-2xl font-bold mb-4">Device List</h2>
        <ul id="list" class="mb-4"></ul>
        <button id="btnConfirm"
            class="w-full px-3 py-3 bg-teal-500 text-white rounded-md">
            Confirm Changes
        </button>
    `;

    await loadDevices();
    bindEvents();
}

async function loadDevices() {
    devicesCache = await apiFetch(`${API_URL}/api/devices`);
    console.log = (devicesCache);
    renderDevices();
}

function renderDevices() {
    const list = document.getElementById("list");
    list.innerHTML = "";

    devicesCache.forEach(d => {
        const li = document.createElement("li");
        li.id = `row-${d.id}`;
        li.className = "border p-3 mb-3 rounded";

        li.innerHTML = `
            <div class="flex justify-between items-center">
                <div>IP: ${d.ip_web} - ${d.brand}</div>

                <div class="flex gap-2">
                    <button class="btn-detail text-blue-600"
                            data-id="${d.id}">
                        Details
                    </button>

                    <button class="btn-edit text-green-600"
                            data-id="${d.id}">
                        Edit
                    </button>
                </div>
            </div>

            <div class="flex gap-4 mt-2">
                <label>
                    <input type="checkbox"
                        class="chk-active"
                        data-id="${d.id}"
                        ${d.is_checked ? "checked" : ""}>
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


function bindEvents() {
    const list = document.getElementById("list");

    // CLICK: Details + Edit
    list.addEventListener("click", e => {

        // DETAILS → SPA
        const detailBtn = e.target.closest(".btn-detail");
        if (detailBtn) {
            location.hash = `#/devices/${detailBtn.dataset.id}`;
            return;
        }

        // EDIT → trang cũ
        const editBtn = e.target.closest(".btn-edit");
        if (editBtn) {
            location.href = `./index.html?id=${editBtn.dataset.id}`;
            return;
        }
    });

    // CHANGE: Active + Delete
    list.addEventListener("change", e => {
    const row = e.target.closest("li");
    if (!row) return;

    // --- Active checkbox ---
    if (e.target.classList.contains("chk-active")) {
        if (!e.target.checked) return;

        const del = row.querySelector(".chk-delete");
        if (del) del.checked = false;        // Bỏ check Delete
        row.classList.remove("mark-delete"); // Xóa highlight
    }

    // --- Delete checkbox ---
    if (e.target.classList.contains("chk-delete")) {
        if (e.target.checked) {
            row.classList.add("mark-delete");

            // Nếu đang check Active → bỏ check Active
            const activeChk = row.querySelector(".chk-active");
            if (activeChk) activeChk.checked = false;
        } else {
            row.classList.remove("mark-delete");
        }
    }
});


    document.getElementById("btnConfirm")
        .addEventListener("click", confirmChanges);
}


async function confirmChanges() {

    // UPDATE
    for (let d of devicesCache) {
        const chk = document.querySelector(`.chk-active[data-id="${d.id}"]`);
        if (chk && chk.checked !== d.is_checked) {
            await apiFetch(`${API_URL}/api/devices/${d.id}`, {
                method: "PUT",
                body: JSON.stringify({ ...d, is_checked: chk.checked })
            });
        }
    }

    // DELETE ( quan trọng)
    const rows = document.querySelectorAll(".mark-delete");
    for (const row of rows) {
        const id = row.id.replace("row-", "");
        await apiFetch(`${API_URL}/api/devices/${id}`, {
            method: "DELETE"
        });
    }

    //  reload SAU KHI delete xong
    await loadDevices();
}

