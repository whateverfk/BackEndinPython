    import { API_URL } from "./config.js";

let editingId = null;

// DOM elements
let ipNvr, ipWeb, userName, password, brand, addBtn;

document.addEventListener("DOMContentLoaded", () => {
    ipNvr = document.getElementById("ipNvr");
    ipWeb = document.getElementById("ipWeb");
    userName = document.getElementById("userName");
    password = document.getElementById("password");
    brand = document.getElementById("brand");
    addBtn = document.getElementById("addBtn");

    if (!addBtn) {
        console.error("Không tìm thấy addBtn");
        return;
    }

    addBtn.addEventListener("click", addDevice);

    // Nếu có ?id= → edit
    const params = new URLSearchParams(window.location.search);
    if (params.has("id")) {
        loadDeviceForEdit(params.get("id"));
        addBtn.innerText = "Update";
    }

    // ENTER → focus field tiếp theo
    const formFields = [ipNvr, ipWeb, userName, password, brand];
    formFields.forEach((field, idx) => {
        field.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                const nextField = formFields[idx + 1];
                nextField ? nextField.focus() : addBtn.focus();
            }
        });
    });

    // Toggle show/hide password
    const togglePassword = document.getElementById("togglePassword");
    const eyeOpen = document.getElementById("eyeOpen");
    const eyeClosed = document.getElementById("eyeClosed");

    togglePassword.addEventListener("click", () => {
        password.type = password.type === "password" ? "text" : "password";
        eyeOpen.classList.toggle("hidden");
        eyeClosed.classList.toggle("hidden");
    });
});

// =======================
// LOAD DEVICE ĐỂ EDIT
// =======================
async function loadDeviceForEdit(id) {
    try {
        const d = await apiFetch(`${API_URL}/api/devices/${id}`);
        if (!d) return;

        ipNvr.value = d.ip_nvr || "";
        ipWeb.value = d.ip_web || "";
        userName.value = d.username || "";
        password.value = d.password || "";
        brand.value = d.brand || "";

        editingId = d.id;
    } catch (err) {
        console.error(err);
        showToast("Failed to load device info", "error");
    }
}

// =======================
// ADD / UPDATE DEVICE
// =======================
async function addDevice() {
    const device = {
        ip_nvr: ipNvr.value.trim(),
        ip_web: ipWeb.value.trim(),
        username: userName.value.trim(),
        password: password.value,
        brand: brand.value,
        is_checked: false
    };

    if (!device.ip_web || !device.username || !device.password) {
        showToast("IP Web, Username, Password are required", "warning");
        return;
    }

    try {
        addBtn.disabled = true;
        showToast("Testing connection...", "info");

        // 1. TEST CONNECTION
        const testResult = await testDeviceConnection(device);

        if (!testResult?.ip_reachable) {
            showToast("Cannot reach device IP", "error");
            return;
        }

        if (!testResult?.auth_ok) {
            showToast("Authentication failed", "error");
            return;
        }

        showToast("Connection OK. Saving device...", "success");

        // 2. SAVE
        if (editingId) {
            await apiFetch(`${API_URL}/api/devices/${editingId}`, {
                method: "PUT",
                body: JSON.stringify(device)
            });
        } else {
            await apiFetch(`${API_URL}/api/devices`, {
                method: "POST",
                body: JSON.stringify(device)
            });
        }

        showToast("Device saved successfully", "success");

        setTimeout(() => {
            clearForm();
            window.location.href = "./list.html";
        }, 800);

    } catch (err) {
        console.error(err);
        showToast("Unexpected error while saving device", "error");
    } finally {
        addBtn.disabled = false;
    }
}

// =======================
function clearForm() {
    ipNvr.value = "";
    ipWeb.value = "";
    userName.value = "";
    password.value = "";
    brand.selectedIndex = 0;
    editingId = null;
}

// =======================
async function testDeviceConnection(device) {
    return await apiFetch(`${API_URL}/api/devices/test-connection`, {
        method: "POST",
        body: JSON.stringify({
            ip_web: device.ip_web,
            username: device.username,
            password: device.password,
            brand: device.brand
        })
    });
}

// =======================
// TOAST
// =======================
function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");

    const baseClass =
        "px-4 py-2 rounded shadow text-sm flex items-center gap-2 animate-slide-in";

    let typeClass = "bg-blue-600 text-white";
    let icon = "ℹ️";

    if (type === "success") {
        typeClass = "bg-green-600 text-white";
        icon = "✅";
    } else if (type === "error") {
        typeClass = "bg-red-600 text-white";
        icon = "❌";
    } else if (type === "warning") {
        typeClass = "bg-yellow-500 text-black";
        icon = "⚠️";
    }

    toast.className = `${baseClass} ${typeClass}`;
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("animate-slide-out");
        toast.addEventListener("animationend", () => toast.remove());
    }, duration);
}
