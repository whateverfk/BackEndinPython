import { API_URL } from "../../../config.js";

export async function renderStorage(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `<div class="text-gray-500">Loading storage...</div>`;

    // 1. Lấy từ DB
    let data = await apiFetch(
        `${API_URL}/api/device/${device.id}/infor/storage`
    );

    // 2. Nếu chưa có data → auto sync 1 lần
    if (!data || data.length === 0) {
        box.innerHTML = `
            <div class="text-gray-500 text-center py-6">
                Fetching storage from device...
            </div>
        `;

        await apiFetch(
            `${API_URL}/api/device/${device.id}/infor/storage`,
            { method: "POST" }
        );

        // 3. Load lại DB sau sync
        data = await apiFetch(
            `${API_URL}/api/device/${device.id}/infor/storage`
        );
    }

    box.innerHTML = renderStorageTable(data, device);
}

function renderStorageTable(storages = [], device) {
    return `
    <div class="space-y-4">

        <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">Storage (HDD)</h3>

            <button onclick="syncStorage()"
                class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                Sync from device
            </button>
        </div>

        <div class="overflow-x-auto">
            <table class="min-w-full border bg-white text-sm">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="border px-3 py-2 text-left">HDD Name</th>
                        <th class="border px-3 py-2">Status</th>
                        <th class="border px-3 py-2">Type</th>
                        <th class="border px-3 py-2">Capacity (GB)</th>
                        <th class="border px-3 py-2">Free Space (GB)</th>
                        <th class="border px-3 py-2">Property</th>
                    </tr>
                </thead>
                <tbody>
                    ${storages.length === 0
                        ? `<tr>
                            <td colspan="6"
                                class="border px-3 py-4 text-center text-gray-400">
                                No storage found
                            </td>
                        </tr>`
                        : storages.map(s => renderStorageRow(s)).join("")
                    }
                </tbody>
            </table>
        </div>
    </div>
    `;
}
function renderStorageRow(s) {
    const toGB = v => (v / 1024).toFixed(1);

    return `
    <tr class="hover:bg-gray-50">
        <td class="border px-3 py-2">${s.hdd_name}</td>
        <td class="border px-3 py-2 text-center">
            <span class="${s.status === "ok" ? "text-green-600" : "text-red-500"}">
                ${s.status}
            </span>
        </td>
        <td class="border px-3 py-2 text-center">${s.hdd_type}</td>
        <td class="border px-3 py-2 text-right">${toGB(s.capacity)}</td>
        <td class="border px-3 py-2 text-right">${toGB(s.free_space)}</td>
        <td class="border px-3 py-2 text-center">${s.property}</td>
    </tr>
    `;
}
window.syncStorage = async function () {
    const d = window.currentDevice;

    await apiFetch(
        `${API_URL}/api/device/${d.id}/infor/storage`,
        { method: "POST" }
    );

    await renderStorage(d);
};
