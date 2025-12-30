import { API_URL } from "../../../config.js";


let currentDevice = null;
let currentUser = null;

export async function renderUsers(device) {
    currentDevice = device;

    const box = document.getElementById("detailContent");

    box.innerHTML = `
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">Device Users</h2>

            <button
                onclick="window.syncDeviceUsers()"
                class="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                Sync from device
            </button>
        </div>

        <div id="userList" class="space-y-2"></div>

        <div id="userDetail" class="mt-6"></div>
    `;

    await loadUsers();
}

async function loadUsers() {
    const listBox = document.getElementById("userList");
    listBox.innerHTML = `<div class="text-gray-500">Loading users...</div>`;

    let users = await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user`
    );

    // Nếu chưa có → auto sync 1 lần
    if (!users || users.length === 0) {
        await window.syncDeviceUsers();
        users = await apiFetch(
            `${API_URL}/api/device/${currentDevice.id}/user`
        );
    }

    listBox.innerHTML = users.map(u => renderUserItem(u)).join("");
}
function renderUserItem(user) {
    return `
        <div
            onclick="window.selectUser(${user.user_id})"
            class="p-3 border rounded cursor-pointer hover:bg-gray-100">

            <div class="font-medium text-gray-800">
                ${user.user_name}
            </div>

            <div class="text-xs text-gray-500 uppercase">
                ${user.role}
            </div>
        </div>
    `;
}
window.selectUser = function (userId) {
    currentUser = userId;

    const detail = document.getElementById("userDetail");

    detail.innerHTML = `
        <div class="bg-gray-50 border rounded p-4 text-gray-500 text-center">
            User detail & permission editor<br/>
            <span class="text-sm">(Coming soon)</span>
        </div>
    `;
};
window.syncDeviceUsers = async function () {
    await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/sync`,
        { method: "POST" }
    );

    await loadUsers();
};
