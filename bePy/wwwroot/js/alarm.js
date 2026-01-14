import { API_URL } from "./config.js";

const PAGE_SIZE = 25;

let alarmListEl;
let deleteAllBtn;
let loadMoreBtn;
let prevBtn;
let nextBtn;

// cursor history (để đi lùi)
let cursorStack = []; // mỗi phần tử: { cursor_time, cursor_id }

let deleteAllModal;
let confirmDeleteAllBtn;
let cancelDeleteAllBtn;

// cursor paging
let lastCursorTime = null;
let lastCursorId = null;
let hasMore = true;
let isLoading = false;

document.addEventListener("DOMContentLoaded", () => {
    alarmListEl = document.getElementById("alarmList");
    deleteAllBtn = document.getElementById("deleteAllBtn");
    loadMoreBtn = document.getElementById("loadMoreBtn");
    prevBtn = document.getElementById("prevBtn");
    nextBtn = document.getElementById("nextBtn");

    deleteAllModal = document.getElementById("confirmDeleteAllModal");
    confirmDeleteAllBtn = document.getElementById("confirmDeleteAllBtn");
    cancelDeleteAllBtn = document.getElementById("cancelDeleteAllBtn");

    deleteAllBtn?.addEventListener("click", openDeleteAllModal);
    confirmDeleteAllBtn?.addEventListener("click", confirmDeleteAll);
    cancelDeleteAllBtn?.addEventListener("click", closeDeleteAllModal);
    loadMoreBtn?.addEventListener("click", loadNextPage);
    prevBtn?.addEventListener("click", loadPrevPage);
    nextBtn?.addEventListener("click", loadNextPage);

    loadAlarms(true);
});

// =======================
// MODAL
// =======================
function openDeleteAllModal() {
    deleteAllModal?.classList.remove("hidden");
    deleteAllModal?.classList.add("flex");
}

function closeDeleteAllModal() {
    deleteAllModal?.classList.add("hidden");
    deleteAllModal?.classList.remove("flex");
}

async function confirmDeleteAll() {
    closeDeleteAllModal();
    await deleteAllAlarms();
}

// =======================
// LOAD ALARMS
// =======================
async function loadAlarms(reset = false) {
    if (isLoading || (!hasMore && !reset)) return;

    isLoading = true;

    if (reset) {
        cursorStack = [];
        alarmListEl.innerHTML = `<div class="p-4 text-gray-500 text-sm">Đang tải alarm...</div>`;
        lastCursorTime = null;
        lastCursorId = null;
        hasMore = true;
        loadMoreBtn?.classList.add("hidden");
    }

    try {
        let url = `${API_URL}/api/user/alarm?t=${Date.now()}`; // tránh cache

        if (lastCursorTime && lastCursorId) {
            url += `&cursor_time=${encodeURIComponent(lastCursorTime)}&cursor_id=${lastCursorId}`;
        }

        const res = await apiFetch(url);
        const alarms = res.items || [];

        if (!reset) {
            cursorStack.push({
                cursor_time: lastCursorTime,
                cursor_id: lastCursorId,
            });
        }

        renderAlarms(alarms, true);

        hasMore = res.has_more === true;
        lastCursorTime = res.next_cursor_time;
        lastCursorId = res.next_cursor_id;

        // toggle buttons
        prevBtn?.classList.toggle("hidden", cursorStack.length === 0);
        nextBtn?.classList.toggle("hidden", !hasMore);

    } catch (err) {
        console.error(err);
        alarmListEl.innerHTML = `<div class="p-4 text-red-500 text-sm">Không tải được alarm</div>`;
    } finally {
        isLoading = false;
    }
}

// =======================
// RENDER
// =======================
function renderAlarms(alarms, reset = true) {
    if (reset) {
        alarmListEl.innerHTML = "";
    }

    if (!alarms.length && reset) {
        alarmListEl.innerHTML = `<div class="p-4 text-gray-500 text-sm">Không có alarm</div>`;
        return;
    }

    alarms.forEach(alarm => {
        const row = document.createElement("div");
        row.dataset.id = alarm.id;
        row.className = "flex justify-between items-start p-3 hover:bg-gray-50 border-b";

        row.innerHTML = `
            <div class="text-sm">
                <div class="text-gray-700">${alarm.message}</div>
                <div class="text-xs text-gray-400 mt-1">${new Date(alarm.created_at).toLocaleString()}</div>
            </div>
            <button class="ml-3 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600">Xóa</button>
        `;

        row.querySelector("button").addEventListener("click", () =>
            deleteSingleAlarm(alarm.id, row)
        );

        alarmListEl.appendChild(row);
    });
}

// =======================
// DELETE ONE
// =======================
async function deleteSingleAlarm(alarmId, rowEl) {
    try {
        await apiFetch(`${API_URL}/api/user/alarm/${alarmId}`, { method: "DELETE" });
        rowEl.remove();
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
        await apiFetch(`${API_URL}/api/user/alarm`, { method: "DELETE" });
        lastCursorTime = null;
        lastCursorId = null;                
        hasMore = false;
        cursorStack = [];
        alarmListEl.innerHTML = `<div class="p-4 text-gray-500 text-sm">Không có alarm</div>`;
        loadMoreBtn?.classList.add("hidden");
        prevBtn?.classList.add("hidden");
        nextBtn?.classList.add("hidden");
        showToast("Đã xóa tất cả alarm", "success");
    } catch (err) {
        console.error(err);
        showToast("Xóa tất cả alarm thất bại", "error");
    }
}

// =======================
// PAGING
// =======================
function loadNextPage() {
    if (!hasMore || isLoading) return;
    loadAlarms(false);
}

function loadPrevPage() {
    if (cursorStack.length === 0 || isLoading) return;
    const prev = cursorStack.pop();
    lastCursorTime = prev.cursor_time;
    lastCursorId = prev.cursor_id;
    hasMore = true;
    loadAlarms(true);
}
