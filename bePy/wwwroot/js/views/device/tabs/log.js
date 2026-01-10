
import { API_URL } from "../../../config.js";
let currentLogs = [];
let currentPage = 1;
const PAGE_SIZE = 50;


export function renderLog(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `
        <div class="space-y-4 max-w-4xl">

            <h3 class="text-lg font-semibold">Device Log</h3>

            <div class="flex gap-4 items-end flex-wrap">
                <div>
                    <label class="block text-sm mb-1">From</label>
                    <input
                        type="datetime-local"
                        id="logFrom"
                        class="border p-2 rounded w-60"
                    />
                </div>

                <div>
                    <label class="block text-sm mb-1">To</label>
                    <input
                        type="datetime-local"
                        id="logTo"
                        class="border p-2 rounded w-60"
                    />
                </div>

               <div>
    <label class="block text-sm mb-1">
        Max Results
        <span
            id="logMaxLabel"
            class="text-gray-500 ml-1"
        >
            (max 2000)
        </span>
    </label>

    <input
        type="number"
        id="logMaxResults"
        min="1"
        max="2000"
        value="1000"
        class="border p-2 rounded w-32"
    />
</div>


                <div>
                    <label class="block text-sm mb-1">Major Type</label>
                    <select
                        id="logMajorType"
                        class="border p-2 rounded w-44"
                    >
                        <option value="ALL">All</option>
                        <option value="EXCEPTION">Exception</option>
                        <option value="ALARM">Alarm</option>
                        <option value="INFORMATION">Infomation</option>
                        <option value="OPERATION">Operation</option>
                    </select>
                </div>

                <button
                    id="btnLogSearch"
                    class="px-4 py-2 bg-blue-600 text-white rounded"
                >
                    Search
                </button>
            </div>

            <div
                id="logResult"
                class="border rounded p-3 bg-gray-50 text-sm"
            >
                Select time range and click Search
            </div>
        </div>
    `;

    bindLogSearch(device);
}

function bindLogSearch(device) {
    const fromInput = document.getElementById("logFrom");
    const toInput = document.getElementById("logTo");
    const maxInput = document.getElementById("logMaxResults");
    const majorSelect = document.getElementById("logMajorType");
    const result = document.getElementById("logResult");

    // From → To >= From
    fromInput.onchange = () => {
        toInput.min = fromInput.value;
        if (toInput.value && toInput.value < fromInput.value) {
            toInput.value = fromInput.value;
        }
    };

    // To → From <= To
    toInput.onchange = () => {
        fromInput.max = toInput.value;
        if (fromInput.value && fromInput.value > toInput.value) {
            fromInput.value = toInput.value;
        }
    };

    document.getElementById("btnLogSearch").onclick = async () => {
        const from = fromInput.value;
        const to = toInput.value;
        let maxResults = parseInt(maxInput.value, 10);
        const majorType = majorSelect.value;

        if (!from || !to) {
            result.innerHTML =
                `<span class="text-red-500">Please select both From and To</span>`;
            return;
        }

        if (isNaN(maxResults) || maxResults < 1) {
            maxResults = 100;
        }

        if (maxResults > 2000) {
            maxResults = 2000;
            maxInput.value = 2000;
        }

        // Payload gửi backend
        const payload = {
            from,           // datetime-local string
            to,
            maxResults,
            majorType
        };

        //  DEBUG
        console.log("[LOG SEARCH] device:", device.id);
        console.log("[LOG SEARCH] payload:", payload);

        result.innerHTML = `<span class="text-gray-500">Searching logs...</span>`;

        try {
            const resp = await apiFetch(`${API_URL}/api/logs/device/${device.id}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await resp;

            // Tạm hiển thị raw để debug
            currentLogs = data.logs || [];
            currentPage = 1;

            if (!currentLogs.length) {
                result.innerHTML = `<span class="text-gray-500">No logs found</span>`;
                return;
            }

            renderLogTable(result);

        } catch (err) {
            console.error(err);
            result.innerHTML =
                `<span class="text-red-500">Failed to fetch logs</span>`;
        }
    };
}


function renderLogTable(container) {
    const totalPages = Math.ceil(currentLogs.length / PAGE_SIZE);
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageLogs = currentLogs.slice(start, end);

    container.innerHTML = `
        <div class="space-y-2 w-full">

            <!-- Paging -->
            <div class="flex items-center justify-between text-xs">
                <div>
                    Showing ${start + 1}-${Math.min(end, currentLogs.length)}
                    of ${currentLogs.length}
                </div>

                <div class="flex items-center gap-1">
                    <button
                        id="logFirst"
                        class="px-2 py-1 border rounded disabled:opacity-40"
                        ${currentPage === 1 ? "disabled" : ""}
                        title="First page"
                    >
                        ⏮
                    </button>

                    <button
                        id="logPrev"
                        class="px-2 py-1 border rounded disabled:opacity-40"
                        ${currentPage === 1 ? "disabled" : ""}
                        title="Previous page"
                    >
                        ◀
                    </button>

                    <span class="px-2">
                        Page ${currentPage} / ${totalPages}
                    </span>

                    <button
                        id="logNext"
                        class="px-2 py-1 border rounded disabled:opacity-40"
                        ${currentPage === totalPages ? "disabled" : ""}
                        title="Next page"
                    >
                        ▶
                    </button>

                    <button
                        id="logLast"
                        class="px-2 py-1 border rounded disabled:opacity-40"
                        ${currentPage === totalPages ? "disabled" : ""}
                        title="Last page"
                    >
                        ⏭
                    </button>
                </div>
            </div>

            <!-- Table -->
            <div class="overflow-auto border rounded max-h-[65vh]">
                <table class="w-full min-w-full text-xs border-collapse">
                    <thead class="bg-gray-100 sticky top-0 z-10">
                        <tr>
                            <th class="border px-1 py-1 w-10 text-center">#</th>
                            <th class="border px-1 py-1 w-40">Time</th>
                            <th class="border px-1 py-1 w-28">Major</th>
                            <th class="border px-1 py-1 w-48">Minor</th>
                            <th class="border px-1 py-1 w-24 text-center">Channel no</th>
                            <th class="border px-1 py-1 w-32">User</th>
                            <th class="border px-1 py-1 w-36">Remote IP</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${pageLogs.map((log, idx) => `
                            <tr class="hover:bg-gray-50">
                                <td class="border px-1 py-[2px] text-center">
                                    ${start + idx + 1}
                                </td>

                                <td class="border px-1 py-[2px] font-mono whitespace-nowrap">
                                    ${log.time || ""}
                                </td>

                                <td class="border px-1 py-[2px]">
                                    ${log.majorType || ""}
                                </td>

                                <td class="border px-1 py-[2px] truncate">
                                    ${log.minorType || ""}
                                </td>

                                <td class="border px-1 py-[2px] text-center">
                                    ${log.localId || ""}
                                </td>

                                <td class="border px-1 py-[2px] truncate">
                                    ${log.userName || ""}
                                </td>

                                <td class="border px-1 py-[2px] font-mono">
                                    ${log.ipAddress || ""}
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // bind paging
    document.getElementById("logFirst")?.addEventListener("click", () => {
        if (currentPage !== 1) {
            currentPage = 1;
            renderLogTable(container);
        }
    });

    document.getElementById("logPrev")?.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderLogTable(container);
        }
    });

    document.getElementById("logNext")?.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderLogTable(container);
        }
    });

    document.getElementById("logLast")?.addEventListener("click", () => {
        if (currentPage !== totalPages) {
            currentPage = totalPages;
            renderLogTable(container);
        }
    });
}

