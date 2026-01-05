import { API_URL } from "../../../config.js";

/* =========================
   State
========================= */
let currentDevice = null;
let currentPermissionData = null;
let selectedPermission = {
    scope: null,
    permission: null,
};
let deviceChannels = [];

/* =========================
   Permission config
========================= */
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
         "ptz_control",
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
         "ptz_control",
    ],
};
const CHANNEL_BASED_PERMISSIONS = [
    "preview",
    "playback",
    "record",
    "backup",
     "ptz_control",
    "voice_talk",
];


const PERMISSION_LABELS = {
    upgrade: "Upgrade / Format",
    parameter_config: "Parameter Configuration",
    restart_or_shutdown: "Shutdown / Reboot",
    log_or_state_check: "Log / Status Check",
    manage_channel: "Camera Management",

    playback: "Playback",
    record: "Manual Record",
    backup: "Video Export",
    ptz_control: "PTZ Control",
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

     deviceChannels = await apiFetch(
        `${API_URL}/api/devices/${device.id}/channels`
    );
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

        <div class="grid grid-cols-2 gap-4 px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b">
            <div>User name</div>
            <div>Role</div>
        </div>

        <div id="userList" class="divide-y"></div>

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

    if (!users || users.length === 0) {
        await window.syncDeviceUsers();
        users = await apiFetch(
            `${API_URL}/api/device/${currentDevice.id}/user`
        );
    }

    listBox.innerHTML = users.map(renderUserItem).join("");
}

/* =========================
   Render user row
========================= */
const ROLE_LABELS = {
administrator: "Admin",
    operator: "Operator",
    viewer: "User", // 👈 viewer hiển thị là user
};

function renderUserItem(user) {
    const roleLabel = ROLE_LABELS[user.role] ?? user.role ?? "-";

    return `
        <div
            onclick='window.openUserModal(${JSON.stringify(user)})'
            class="grid grid-cols-2 gap-4 px-3 py-3 cursor-pointer hover:bg-gray-50">

            <div class="font-medium text-gray-800">
                ${user.user_name}
            </div>

            <div class="text-sm text-gray-500">
                ${roleLabel}
            </div>
        </div>
    `;
}


/* =========================
   Modal
========================= */
window.openUserModal = async function (user) {
    const modal = document.getElementById("userModal");

   modal.innerHTML = `
    <div class="bg-white w-[960px] max-h-[90vh] rounded-lg shadow-lg p-6 flex flex-col">
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

        <!-- BODY -->
        <div class="grid grid-cols-2 gap-4 flex-1 overflow-hidden">

            <!-- LEFT -->
            <div
                id="permissionList"
                class="border rounded p-3 overflow-y-auto">
            </div>

            <!-- RIGHT -->
            <div
                id="channelPanel"
                class="border rounded p-3 overflow-y-auto text-gray-400 flex items-center justify-center">
                Select a channel-based permission
            </div>

        </div>
    </div>
`;


    modal.classList.remove("hidden");

    const perm = await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${user.id}/permissions`
    );
    console.log("user id" + user.id)
    console.log(perm);

    renderPermissionUI(perm);
};

window.closeUserModal = function () {
    const modal = document.getElementById("userModal");
    modal.classList.add("hidden");
    modal.innerHTML = "";
};

/* =========================
   Sync permission
========================= */
window.syncUserPermission = async function (userId) {
    await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${userId}/permissions/sync`,
        { method: "POST" }
    );

    const perm = await apiFetch(
        `${API_URL}/api/device/${currentDevice.id}/user/${userId}/permissions`
    );
    console.log(perm);

    

    renderPermissionUI(perm);
};

/* =========================
   Render permissions
========================= */
function renderPermissionUI(data) {
    currentPermissionData = data;
    selectedPermission = { scope: null, permission: null };

    const box = document.getElementById("permissionList");

    box.innerHTML = `
        ${renderScope("Local", data.local)}
        ${renderScope("Remote", data.remote)}
    `;

    document.getElementById("channelPanel").innerHTML =
        `<div class="text-gray-400">Select a permission to view channels</div>`;
}

function renderScope(title, scopeData) {
    const scopeKey = title.toLowerCase();
    const allowed = SCOPE_PERMISSION_WHITELIST[scopeKey] || [];

    return `
        <div class="mb-5">
            <h4 class="font-semibold mb-2">${title} Permissions</h4>

            <div class="space-y-2">
                ${allowed.map(key => {
                    const enabled = isPermissionEnabled(scopeData, key);
                    return renderPermissionItem(scopeKey, key, enabled);
                }).join("")}
            </div>
        </div>
    `;
}


function renderPermissionItem(scope, key, enabled) {
    const isSelected =
        selectedPermission.scope === scope &&
        selectedPermission.permission === key;

    return `
        <div
            onclick="window.selectPermission('${scope}', '${key}')"
            class="flex items-center justify-between px-3 py-2 border rounded cursor-pointer
                   hover:bg-gray-50
                   ${isSelected ? "bg-blue-50 border-blue-500 ring-1 ring-blue-300" : ""}">

            <span>${permissionLabel(scope, key)}</span>

            <span class="${enabled ? "text-green-600" : "text-gray-300"}">
                ${enabled ? "✔" : "—"}
            </span>
        </div>
    `;
}



function permissionLabel(scope, key) {
    return `${scope.toUpperCase()}: ${PERMISSION_LABELS[key] ?? key}`;
}

/* =========================
   Channel panel
========================= */
window.selectPermission = function (scope, permission) {
    selectedPermission = { scope, permission };

    // 👉 RENDER LẠI permission list để highlight
    renderPermissionUI(currentPermissionData);

    const panel = document.getElementById("channelPanel");

    // ===== Global permission → không có channel =====
    if (!CHANNEL_BASED_PERMISSIONS.includes(permission)) {
        panel.innerHTML = `
            <div class="text-gray-400 text-center">
                This permission is global and does not apply to individual channels
            </div>
        `;
        return;
    }

    const scopeData = currentPermissionData?.[scope];
    if (!scopeData) return;

    const enabledChannels = scopeData.channels?.[permission] || [];
    const enabledSet = new Set(enabledChannels.map(Number));

    panel.innerHTML = `
        <h4 class="font-semibold mb-3">
            ${scope.toUpperCase()} → ${PERMISSION_LABELS[permission] ?? permission}
        </h4>

        <div class="space-y-2 max-h-[360px] overflow-auto">
            ${deviceChannels.map(ch =>
                renderChannelCheckbox(
                    ch.id,
                    ch.name ?? `Channel ${ch.id}`,
                    enabledSet.has(Number(ch.id))
                )
            ).join("")}
        </div>
    `;
};



function renderChannelCheckbox(channelId, label, checked) {
    return `
        <label class="flex items-center gap-3 px-3 py-2 border rounded cursor-pointer hover:bg-gray-50">
            <input
                type="checkbox"
                class="accent-blue-600"
                ${checked ? "checked" : ""}
                disabled
            />
            <span>${label}</span>
        </label>
    `;
}


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

/* =========================
   Click outside modal
========================= */
document.addEventListener("click", (e) => {
    const modal = document.getElementById("userModal");
    if (!modal) return;

    if (!modal.classList.contains("hidden") && e.target === modal) {
        window.closeUserModal();
    }
});


function isPermissionEnabled(scopeData, permission) {
    if (!scopeData) return false;

    // Global permission
    if (!CHANNEL_BASED_PERMISSIONS.includes(permission)) {
        return Boolean(scopeData.global?.[permission]);
    }

    //  Channel-based permission (PTZ, preview, playback...)
    const channels = scopeData.channels?.[permission] || [];
    return channels.length > 0;
}
