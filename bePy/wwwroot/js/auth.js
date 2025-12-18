/* =========================
   AUTH HELPERS
========================= */

function getToken() {
    return localStorage.getItem("token");
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "./login.html";
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = "./login.html";
    }
}

/* =========================
   API FETCH WRAPPER
========================= */

async function apiFetch(url, options = {}) {
    const token = getToken();

    if (!token) {
        logout();
        return;
    }

    const res = await fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        }
    });

    if (res.status === 401) {
        logout();
        return;
    }

    if (res.status === 403) {
        alert("Bạn không có quyền thực hiện chức năng này");
        return;
    }

    if (res.status === 204) {
        return null;
    }

    const text = await res.text();
    return text ? JSON.parse(text) : null;
}
