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

    // nếu có ?id= → edit
    const params = new URLSearchParams(window.location.search);
    if (params.has("id")) {
        loadDeviceForEdit(params.get("id"));
        addBtn.innerText = "Update";
    }
});

// =======================
// LOAD DEVICE ĐỂ EDIT
// =======================
async function loadDeviceForEdit(id) {
    const d = await apiFetch(`${API_URL}/api/devices/${id}`);
    if (!d) return;

    ipNvr.value = d.ip_nvr;
    ipWeb.value = d.ip_web;
    userName.value = d.username;
    password.value = d.password;
    brand.value = d.brand;

    editingId = d.id;
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

    if (!device.ip_nvr) {
        alert("IP NVR is required");
        return;
    }

    try {
        if (editingId) {
            // UPDATE
            await apiFetch(`${API_URL}/api/devices/${editingId}`, {
                method: "PUT",
                body: JSON.stringify(device)
            });
        } else {
            // CREATE
            await apiFetch(`${API_URL}/api/devices`, {
                method: "POST",
                body: JSON.stringify(device)
            });
        }

        clearForm();
        window.location.href = "./list.html";

    } catch (err) {
        console.error(err);
        alert("Error while saving device");
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
