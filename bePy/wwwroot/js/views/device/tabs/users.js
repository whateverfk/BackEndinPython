import { API_URL } from "../../../config.js";

// Thêm vào đầu file user.js hoặc trong renderUsers()

// Inject CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slide-out {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
`;

if (!document.getElementById('permission-animations')) {
    style.id = 'permission-animations';
    document.head.appendChild(style);
}

/* =========================
   State
========================= */
let currentDevice = null;
let currentPermissionData = null;
let currentUserId = null;
let modifiedPermissions = null; // Track changes
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
    alarm_out_or_upload: "Notify Surveillance Center / Trigger Alarm Output",
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
    viewer: "User",
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
    currentUserId = user.id;
    const modal = document.getElementById("userModal");

    modal.innerHTML = `
        <div class="bg-white w-[960px] max-h-[90vh] rounded-lg shadow-lg p-6 flex flex-col">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">
                    User Permission – ${user.user_name}
                </h3>
                <button onclick="window.closeUserModal()">✕</button>
            </div>

            <div class="flex justify-between mb-3">
                <button
                    onclick="window.savePermissions()"
                    class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-semibold">
                     Save Changes
                </button>
                
                <button
                    onclick="window.syncUserPermission(${user.id})"
                    class="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
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
    

    renderPermissionUI(perm);
};

window.closeUserModal = function () {
    const modal = document.getElementById("userModal");
    modal.classList.add("hidden");
    modal.innerHTML = "";
    modifiedPermissions = null;
    currentUserId = null;
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
   

    renderPermissionUI(perm);
};

/* =========================
   Render permissions
========================= */
function renderPermissionUI(data) {
    currentPermissionData = JSON.parse(JSON.stringify(data)); // Deep copy
    modifiedPermissions = JSON.parse(JSON.stringify(data)); // Working copy
    selectedPermission = { scope: null, permission: null };

    const box = document.getElementById("permissionList");

    box.innerHTML = `
        ${renderScope("Local", "local")}
        ${renderScope("Remote", "remote")}
    `;

    document.getElementById("channelPanel").innerHTML =
        `<div class="text-gray-400">Select a permission to view channels</div>`;
}

function renderScope(title, scopeKey) {
    const allowed = SCOPE_PERMISSION_WHITELIST[scopeKey] || [];

    return `
        <div class="mb-5">
            <h4 class="font-semibold mb-2">${title} Permissions</h4>

            <div class="space-y-2">
                ${allowed.map(key => {
                    const enabled = isPermissionEnabled(modifiedPermissions[scopeKey], key);
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
            class="flex items-center justify-between px-3 py-2 border rounded
                   ${isSelected ? "bg-blue-50 border-blue-500 ring-1 ring-blue-300" : ""}">

            <label 
                onclick="window.selectPermission('${scope}', '${key}')"
                class="flex-1 cursor-pointer">
                ${permissionLabel(scope, key)}
            </label>

            <input
                type="checkbox"
                class="accent-blue-600 cursor-pointer w-5 h-5"
                ${enabled ? "checked" : ""}
                onchange="window.toggleGlobalPermission('${scope}', '${key}', this.checked)"
            />
        </div>
    `;
}

function permissionLabel(scope, key) {
    return `${scope.toUpperCase()}: ${PERMISSION_LABELS[key] ?? key}`;
}

/* =========================
   Toggle permissions
========================= */
window.toggleGlobalPermission = function (scope, permission, checked) {
    if (!CHANNEL_BASED_PERMISSIONS.includes(permission)) {
        // Global permission
        modifiedPermissions[scope].global[permission] = checked;
    } else {
        // Channel-based: toggle all channels
        if (checked) {
            modifiedPermissions[scope].channels[permission] = deviceChannels.map(ch => ch.id);
        } else {
            modifiedPermissions[scope].channels[permission] = [];
        }
    }

    // Re-render to update UI
    const box = document.getElementById("permissionList");
    box.innerHTML = `
        ${renderScope("Local", "local")}
        ${renderScope("Remote", "remote")}
    `;

    // If this permission is selected, update channel panel
    if (selectedPermission.scope === scope && selectedPermission.permission === permission) {
        window.selectPermission(scope, permission);
    }
};

window.toggleChannelPermission = function (scope, permission, channelId, checked) {
    if (!modifiedPermissions[scope].channels[permission]) {
        modifiedPermissions[scope].channels[permission] = [];
    }

    const channels = modifiedPermissions[scope].channels[permission];
    const index = channels.indexOf(channelId);

    if (checked && index === -1) {
        channels.push(channelId);
    } else if (!checked && index !== -1) {
        channels.splice(index, 1);
    }

    // Update main checkbox state
    const box = document.getElementById("permissionList");
    box.innerHTML = `
        ${renderScope("Local", "local")}
        ${renderScope("Remote", "remote")}
    `;
};

/* =========================
   Channel panel
========================= */
window.selectPermission = function (scope, permission) {
    selectedPermission = { scope, permission };

    // Re-render permission list to highlight
    const box = document.getElementById("permissionList");
    box.innerHTML = `
        ${renderScope("Local", "local")}
        ${renderScope("Remote", "remote")}
    `;

    const panel = document.getElementById("channelPanel");

    // Global permission → no channels
    if (!CHANNEL_BASED_PERMISSIONS.includes(permission)) {
        panel.innerHTML = `
            <div class="text-gray-400 text-center">
                This permission is global and does not apply to individual channels
            </div>
        `;
        return;
    }

    const scopeData = modifiedPermissions?.[scope];
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
                    scope,
                    permission,
                    ch.id,
                    ch.name ?? `Channel ${ch.id}`,
                    enabledSet.has(Number(ch.id))
                )
            ).join("")}
        </div>
    `;
};

function renderChannelCheckbox(scope, permission, channelId, label, checked) {
    return `
        <label class="flex items-center gap-3 px-3 py-2 border rounded cursor-pointer hover:bg-gray-50">
            <input
                type="checkbox"
                class="accent-blue-600 w-5 h-5"
                ${checked ? "checked" : ""}
                onchange="window.toggleChannelPermission('${scope}', '${permission}', ${channelId}, this.checked)"
            />
            <span>${label}</span>
        </label>
    `;
}

/* =========================
   Save permissions
========================= */
/* =========================
   Save permissions
========================= */

/* =========================
   Save permissions
========================= */
window.savePermissions = async function () {
    const result = {
        device_id: currentDevice.id,
        device_user_id: currentUserId,
        permissions: modifiedPermissions
    };
    
    
    
    // Disable button và hiển thị loading
    const saveBtn = event.target;
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '⏳ Saving...';
    
    try {
        const response = await apiFetch(
            `${API_URL}/api/device/${currentDevice.id}/user/${currentUserId}/permissions`,
            {
                method: "PUT",
                body: JSON.stringify(result)
            }
        );
        
        // Xử lý kết quả
        if (response.success) {
            // Thành công
            showNotification('success', '✓ Permission updated successfully!');
            
            // Refresh lại data từ server
            const updatedPerm = await apiFetch(
                `${API_URL}/api/device/${currentDevice.id}/user/${currentUserId}/permissions`
            );
            renderPermissionUI(updatedPerm);
            
        } else {
            // Xử lý các loại lỗi
            if (response.code === 'LOW_PRIVILEGE') {
                showNotification('error', ' Insufficient privileges: You do not have enough permissions to change user permissions on this device.');
            } else if (response.code === 'INVALID_OPERATION') {
                showNotification('error', ' Invalid operation: The permission change request is invalid.');
            } else {
                showNotification('error', ` Error: ${response.message || 'Unknown error occurred'}`);
            }
        }
        
    } catch (error) {
        console.error('Save permission error:', error);
        showNotification('error', ' Network error: Unable to save permissions. Please check your connection and try again.');
        
    } finally {
        // Restore button
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
};

/* =========================
   Show notification
========================= */
function showNotification(type, message) {
    // Remove existing notification if any
    const existing = document.getElementById('permissionNotification');
    if (existing) {
        existing.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.id = 'permissionNotification';
    
    const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
    
    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-[9999] flex items-center gap-3 animate-slide-in`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200 font-bold">✕</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slide-out 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 3000);
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

    // Channel-based permission
    const channels = scopeData.channels?.[permission] || [];
    return channels.length > 0;
}