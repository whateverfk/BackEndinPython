(function loadUserInfo() {

    const token = localStorage.getItem("token");
    if (!token) return;

    const payload = JSON.parse(atob(token.split('.')[1]));

    const username =
        payload["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"]
        ?? "(unknown)";

    const role =
        payload["http://schemas.microsoft.com/ws/2008/06/identity/claims/role"]
        ?? "(unknown)";

    const userId =
        payload["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"]
        ?? "(unknown)";

    const superAdminId = payload.superAdminId ?? "(unknown)";

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

function logout() {
    localStorage.removeItem("token");
    location.href = "./login.html";
}
