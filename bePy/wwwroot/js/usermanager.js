import { API_URL } from "./config.js";

/**
 * Load user info from JWT
 */
(function loadUserInfo() {
    const token = localStorage.getItem("token");
    if (!token) return;

    const payload = JSON.parse(atob(token.split(".")[1]));

    const username =
        payload["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"]
        ?? "(unknown)";

    const role =
        payload["http://schemas.microsoft.com/ws/2008/06/identity/claims/role"]
        ?? "(unknown)";

    document.getElementById("userInfo").innerHTML = `
        <div class="user-row">
            <span class="label">Username</span>
            <span class="value">${username}</span>
        </div>

        <div class="user-row">
            <span class="label">Role</span>
            <span class="value role-${role.toLowerCase()}">${role}</span>
        </div>
    `;
})();

/**
 * Change password
 */
window.changePassword = async function () {
    const oldPassword = document.getElementById("oldPassword").value.trim();
    const newPassword = document.getElementById("newPassword").value.trim();
    const msg = document.getElementById("pwMsg");

    msg.textContent = "";
    msg.className = "text-sm mt-2";

    if (!oldPassword || !newPassword) {
        msg.textContent = "Please fill all fields";
        msg.classList.add("text-red-500");
        return;
    }

    try {
        await apiFetch(`${API_URL}/api/auth/change-password`, {
            method: "POST",
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        msg.textContent = "Password updated successfully";
        msg.classList.add("text-green-600");

        document.getElementById("oldPassword").value = "";
        document.getElementById("newPassword").value = "";

    } catch (err) {
        msg.textContent = err?.message || "Update failed";
        msg.classList.add("text-red-500");
    }
};
