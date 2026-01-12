import { API_URL } from "./config.js";

let alarmListEl;
let deleteAllBtn;

let deleteAllModal;
let confirmDeleteAllBtn;
let cancelDeleteAllBtn;

document.addEventListener("DOMContentLoaded", () => {
    alarmListEl = document.getElementById("alarmList");
    deleteAllBtn = document.getElementById("deleteAllBtn");

    deleteAllModal = document.getElementById("confirmDeleteAllModal");
    confirmDeleteAllBtn = document.getElementById("confirmDeleteAllBtn");
    cancelDeleteAllBtn = document.getElementById("cancelDeleteAllBtn");

    deleteAllBtn?.addEventListener("click", openDeleteAllModal);
    confirmDeleteAllBtn?.addEventListener("click", confirmDeleteAll);
    cancelDeleteAllBtn?.addEventListener("click", closeDeleteAllModal);

    loadAlarms();
});
function openDeleteAllModal() {
    deleteAllModal.classList.remove("hidden");
    deleteAllModal.classList.add("flex");
}

function closeDeleteAllModal() {
    deleteAllModal.classList.add("hidden");
    deleteAllModal.classList.remove("flex");
}
async function confirmDeleteAll() {
    closeDeleteAllModal();
    await deleteAllAlarms();
}


// =======================
// LOAD ALARMS
// =======================
async function loadAlarms() {
    alarmListEl.innerHTML = `
        <div class="p-4 text-gray-500 text-sm">Đang tải alarm...</div>
    `;

    try {
        const alarms = await apiFetch(`${API_URL}/api/user/alarm?limit=50`);
        renderAlarms(alarms || []);
    } catch (err) {
        console.error(err);
        alarmListEl.innerHTML = `
            <div class="p-4 text-red-500 text-sm">
                Không tải được alarm
            </div>
        `;
    }
}

// =======================
// RENDER
// =======================
function renderAlarms(alarms) {
    alarmListEl.innerHTML = "";

    if (!alarms.length) {
        alarmListEl.innerHTML = `
            <div class="p-4 text-gray-500 text-sm">
                Không có alarm
            </div>
        `;
        return;
    }

    alarms.forEach(alarm => {
        const row = document.createElement("div");
        row.dataset.id = alarm.id;
        row.className =
            "flex justify-between items-start p-3 hover:bg-gray-50";

        row.innerHTML = `
            <div class="text-sm">
                <div class="text-gray-700">
                    ${alarm.message}
                </div>
                <div class="text-xs text-gray-400 mt-1">
                    ${new Date(alarm.created_at).toLocaleString()}
                </div>
            </div>

            <button
                class="ml-3 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600">
                Xóa
            </button>
        `;

        row.querySelector("button").addEventListener("click", () =>
            deleteAlarm(alarm.id)
        );

        alarmListEl.appendChild(row);
    });
}

// =======================
// DELETE ONE
// =======================
async function deleteAlarm(id) {
    try {
        await apiFetch(`${API_URL}/api/user/alarm/${id}`, {
            method: "DELETE"
        });

        // remove DOM
        const row = alarmListEl.querySelector(`[data-id="${id}"]`);
        row?.remove();

        // nếu hết alarm thì hiển thị text
        if (!alarmListEl.children.length) {
            alarmListEl.innerHTML = `
                <div class="p-4 text-gray-500 text-sm">
                    Không có alarm
                </div>
            `;
        }

        showToast("Đã xóa alarm", "success");
    } catch (err) {
        console.error(err);
        showToast("Xóa alarm thất bại", "error");
    }
}


// =======================
// DELETE ALL
// =======================
async function deleteAllAlarms() {
    try {
        await apiFetch(`${API_URL}/api/user/alarm`, {
            method: "DELETE"
        });

        alarmListEl.innerHTML = `
            <div class="p-4 text-gray-500 text-sm">
                Không có alarm
            </div>
        `;

        showToast("Đã xóa tất cả alarm", "success");
    } catch (err) {
        console.error(err);
        showToast("Xóa tất cả alarm thất bại", "error");
    }
}

