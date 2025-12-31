import { API_URL } from "../../../config.js";

let currentDevice = null;

const SCOPE_PERMISSION_WHITELIST = {
    local: [
        "upgrade",
        "parameter_config",
        "restart_or_shutdown",
        "log_or_state_check",
        "manage_channel",
        "playback",
        "record",
        "backup",
    ],
    remote: [
        "parameter_config",
        "log_or_state_check",
        "upgrade",
        "voice_talk",
        "restart_or_shutdown",
        "alarm_out_or_upload",
        "control_local_out",
        "transparent_channel",
        "manage_channel",
        "preview",
        "record",
        "playback",
    ]
};
const PERMISSION_LABELS = {
    upgrade: "Upgrade / Format",
    parameter_config: "Parameter Configuration",
    restart_or_shutdown: "Shutdown / Reboot",
    log_or_state_check: "Log / Status Check",
    manage_channel: "Camera Management",

    playback: "Playback",
    record: "Manual Record",
    backup: "Video Export",

    preview: "Live View",
    voice_talk: "Two-way Audio",
    alarm_out_or_upload: "Trigger Alarm Output",
    control_local_out: "Video Output Control",
    transparent_channel: "Serial Port Control",
};



/* =========================
   Render main view
========================= */
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

        <!-- Header -->
        <div class="grid grid-cols-2 gap-4 px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b">
            <div>User name</div>
            <div>Role</div>
        </div>

        <!-- User list -->
        <div id="userList" class="divide-y"></div>

        <!-- Modal -->
        <div id="userModal"
             class="hidden fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        </div>
    `;

    await loadUsers();
}

/* =========================
   Load users
========================= */
async function loadUsers() {
    const listBox = document.getElementById("userList");
    listBox.innerHTML = `<div class="text-gray-500 p-3">Loading users...</div>`;

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

    listBox.innerHTML = users.map(renderUserItem).join("");
}

/* =========================
   Render user row (2 columns)
========================= */
function renderUserItem(user) {
    return `
        <div
            onclick='window.openUserModal(${JSON.stringify(user)})'
            class="grid grid-cols-2 gap-4 px-3 py-3 cursor-pointer hover:bg-gray-50">

            <div class="font-medium text-gray-800">
                ${user.user_name}
            </div>

            <div class="text-sm text-gray-500 ">
                ${user.role ?? "-"}
            </div>
        </div>
    `;
}

/* =========================
   Modal logic
========================= */
window.openUserModal = async function (user) {
    const modal = document.getElementById("userModal");

    modal.innerHTML = `
        <div class="bg-white w-[720px] rounded-lg shadow-lg p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">
                    User Permission – ${user.user_name}
                </h3>
                <button onclick="window.closeUserModal()">✕</button>
            </div>

            <div class="flex justify-end mb-3">
                <button
                    onclick="window.syncUserPermission(${user.id})"
                    class="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                    Fetch newest data 
                </button>
            </div>

            <div id="permissionBody" class="text-sm text-gray-500">
                Loading permissions...
            </div>
        </div>
    `;

    modal.classList.remove("hidden");

    const perm = await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${user.id}/permissions`
    );

    renderPermissionUI(perm);
};

window.syncUserPermission = async function (userId) {
    await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${userId}/permissions/sync`,
        { method: "POST" }
    );

    // Reload permission sau khi sync
    const perm = await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${userId}/permissions`
    );

    renderPermissionUI(perm);
};


function renderPermissionUI(data) {
    const box = document.getElementById("permissionBody");

    box.innerHTML = `
        ${renderScope("Local", data.local)}
        ${renderScope("Remote", data.remote)}
    `;
}
function renderScope(title, scopeData) {
    const scopeKey = title.toLowerCase(); // local | remote
    const allowed = SCOPE_PERMISSION_WHITELIST[scopeKey] || [];

    return `
        <div class="mb-6">
            <h4 class="font-semibold mb-2">${title} Permissions</h4>

            <div class="grid grid-cols-2 gap-2">
                ${allowed
                    .map((key) =>
                        renderPermissionItem(
                            title,
                            key,
                            Boolean(scopeData.global?.[key])
                        )
                    )
                    .join("")}
            </div>
        </div>
    `;
}


function renderPermissionItem(scope, key, enabled) {
    return `
        <div
            onclick="window.showPermissionChannels('${scope.toLowerCase()}', '${key}')"
            class="flex items-center justify-between px-3 py-2 border rounded cursor-pointer hover:bg-gray-50">

            <span>${permissionLabel(scope, key)}</span>

            <span class="${enabled ? "text-green-600" : "text-gray-300"}">
                ${enabled ? "✔" : "—"}
            </span>
        </div>
    `;
}
function permissionLabel(scope, key) {
    return `${scope}: ${PERMISSION_LABELS[key] ?? key}`;
}

window.showPermissionChannels = function (scope, permission) {
    alert(`Show channels for ${scope} → ${permission}\n(Next step: channel modal)`);
};


window.closeUserModal = function () {
    const modal = document.getElementById("userModal");
    modal.classList.add("hidden");
    modal.innerHTML = "";
};

/* Click outside modal to close */
document.addEventListener("click", (e) => {
    const modal = document.getElementById("userModal");
    if (!modal) return;

    if (!modal.classList.contains("hidden") && e.target === modal) {
        window.closeUserModal();
    }
});


/* =========================
   Sync users
========================= */
window.syncDeviceUsers = async function () {
    await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/sync`,
        { method: "POST" }
    );

    await loadUsers();
};
