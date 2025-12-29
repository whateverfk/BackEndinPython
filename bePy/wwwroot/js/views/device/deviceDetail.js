import { API_URL } from "../../config.js";


export async function renderDeviceDetail(container, id) {
    const d = await apiFetch(`${API_URL}/api/devices/${id}`);

    container.innerHTML = `
        <button id="btnBack" class="mb-4 text-blue-600">← Back</button>

        <h2 class="text-xl font-bold mb-2">Device ${d.ip_web}</h2>

        <div class="flex gap-4 mb-4">
            <button id="tab-info" class="font-semibold">Info</button>
            
        </div>

        <div id="detailContent"></div>
    `;

    document.getElementById("btnBack").onclick =
        () => location.hash = "#/devices";

    document.getElementById("tab-info").onclick =
        () => renderInfo(d);

    ;

    renderInfo(d);
}

function renderInfo(d) {
    document.getElementById("detailContent").innerHTML = `
        <div class="space-y-2">
            <p><b>IP Web:</b> ${d.ip_web}</p>
            <p><b>Brand:</b> ${d.brand}</p>
            <p><b>Status:</b> ${d.is_checked ? "Active" : "Inactive"}</p>
        </div>
    `;
}



