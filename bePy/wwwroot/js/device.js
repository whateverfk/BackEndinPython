let editingId = null;

// dùng khi quay lại từ list để edit
async function loadDeviceForEdit(id) {
    const d = await apiFetch(`http://127.0.0.1:8000/api/devices/${id}`);
    if (!d) return;

    ipNvr.value = d.ip_nvr;
    ipWeb.value = d.ip_web;
    userName.value = d.username;
    password.value = d.password;
    brand.value = d.brand;

    editingId = d.id;
}

async function addDevice() {
    const device = {
        ip_nvr: ipNvr.value,
        ip_web: ipWeb.value,
        username: userName.value,
        password: password.value,
        brand: brand.value,
        is_checked: false
    };

    // Sửa lỗi validate
    if (!device.ip_nvr) {
        alert("IP NVR is required");
        return;
    }

    try {
        if (editingId) {
            // UPDATE
            await apiFetch(`http://127.0.0.1:8000/api/devices/${editingId}`, {
                method: 'PUT',
                body: JSON.stringify(device)
            });
        } else {
            // CREATE
            await apiFetch('http://127.0.0.1:8000/api/devices', {
                method: 'POST',
                body: JSON.stringify(device)
            });
        }

        clearForm();
        location.href = "./list.html";

    } catch (err) {
        alert("Error while saving device");
    }
}

function clearForm() {
    ipNvr.value = '';
    ipWeb.value = '';
    userName.value = '';
    password.value = '';
    brand.selectedIndex = 0;
    editingId = null;
}

// nếu có ?id= trên url → edit
const params = new URLSearchParams(window.location.search);
if (params.has('id')) {
    loadDeviceForEdit(params.get('id'));
}
