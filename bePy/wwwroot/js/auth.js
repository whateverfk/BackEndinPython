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

    // ===== AUTH =====
    if (res.status === 401) {
        logout();
        return;
    }

    if (res.status === 403) {
        alert("Bạn không có quyền thực hiện chức năng này");
        return;
    }

    // ===== NO CONTENT =====
    if (res.status === 204) {
        return null;
    }

    // ===== PARSE BODY =====
    let data = null;
    try {
        data = await res.json();
    } catch {
        // ignore
    }

    // ===== THROW FOR ERROR (QUAN TRỌNG) =====
    if (!res.ok) {
        const err = new Error(data?.detail || "API Error");
        err.status = res.status;
        err.data = data;
        throw err;
    }

    return data;
}
