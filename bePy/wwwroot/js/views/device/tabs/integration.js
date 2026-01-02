import { API_URL } from "../../../config.js";

export function renderIntegration(device) {
    document.getElementById("detailContent").innerHTML = `
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <h2 class="text-lg font-semibold">
                    Integration Protocol Users
                </h2>

                <button
                    id="btnSyncIntegration"
                    class="px-4 py-2 bg-blue-600 text-white rounded"
                >
                    Sync
                </button>
            </div>

            <div class="overflow-auto border rounded">
                <table class="min-w-full text-sm">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="px-3 py-2 text-left">User ID</th>
                            <th class="px-3 py-2 text-left">Username</th>
                            <th class="px-3 py-2 text-left">Level</th>
                        </tr>
                    </thead>
                    <tbody id="integrationBody">
                        <tr>
                            <td colspan="3" class="p-4 text-center text-gray-500">
                                Loading...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    document.getElementById("btnSyncIntegration").onclick =
        () => syncIntegration(device);

    loadIntegration(device);
}

async function loadIntegration(device) {
    const body = document.getElementById("integrationBody");

    try {
        const data = await apiFetch(
            `${API_URL}/api/device/${device.id}/infor/onvif-users`
        );

        // Auto sync lần đầu
        if (!data || data.length === 0) {
            await syncIntegration(device);
            return;
        }

        body.innerHTML = data.map(u => `
            <tr class="border-t">
                <td class="px-3 py-2">${u.user_id}</td>
                <td class="px-3 py-2">${u.username}</td>
                <td class="px-3 py-2">${u.level}</td>
            </tr>
        `).join("");

    } catch (err) {
        console.error(err);
        body.innerHTML = `
            <tr>
                <td colspan="3" class="p-4 text-center text-red-500">
                    Failed to load data
                </td>
            </tr>
        `;
    }
}
async function syncIntegration(device) {
    const body = document.getElementById("integrationBody");

    body.innerHTML = `
        <tr>
            <td colspan="3" class="p-4 text-center text-gray-500">
                Syncing from device...
            </td>
        </tr>
    `;

    await apiFetch(
        `${API_URL}/api/device/${device.id}/infor/onvif-users`,
        { method: "POST" }
    );

    await loadIntegration(device);
}

