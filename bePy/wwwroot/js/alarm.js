import { API_URL } from "./config.js";

let alarmListEl;
let deleteAllBtn;

document.addEventListener("DOMContentLoaded", () => {
    alarmListEl = document.getElementById("alarmList");
    deleteAllBtn = document.getElementById("deleteAllBtn");

    if (!alarmListEl) {
        console.error("Không tìm thấy alarmList");
        return;
    }

    deleteAllBtn?.addEventListener("click", deleteAllAlarms);

    loadAlarms();
});

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
    if (!confirm("Xóa alarm này?")) return;

    try {
        await apiFetch(`${API_URL}/api/user/alarm/${id}`, {
            method: "DELETE"
        });

        showToast("Đã xóa alarm", "success");
        loadAlarms();
    } catch (err) {
        console.error(err);
        showToast("Xóa alarm thất bại", "error");
    }
}

// =======================
// DELETE ALL
// =======================
async function deleteAllAlarms() {
    if (!confirm("Xóa TẤT CẢ alarm?")) return;

    try {
        await apiFetch(`${API_URL}/api/user/alarm`, {
            method: "DELETE"
        });

        showToast("Đã xóa tất cả alarm", "success");
        loadAlarms();
    } catch (err) {
        console.error(err);
        showToast("Xóa tất cả alarm thất bại", "error");
    }
}
