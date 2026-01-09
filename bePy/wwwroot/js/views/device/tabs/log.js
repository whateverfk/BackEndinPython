export function renderLog(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = `
        <div class="space-y-4 max-w-3xl">

            <h3 class="text-lg font-semibold">Device Log</h3>

            <div class="flex gap-4 items-end">
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

    bindLogSearch();
}

function bindLogSearch() {
    const fromInput = document.getElementById("logFrom");
    const toInput = document.getElementById("logTo");
    const result = document.getElementById("logResult");

    // From thay đổi → To >= From
    fromInput.onchange = () => {
        toInput.min = fromInput.value;

        if (toInput.value && toInput.value < fromInput.value) {
            toInput.value = fromInput.value;
        }
    };

    // To thay đổi → From <= To
    toInput.onchange = () => {
        fromInput.max = toInput.value;

        if (fromInput.value && fromInput.value > toInput.value) {
            fromInput.value = toInput.value;
        }
    };

    document.getElementById("btnLogSearch").onclick = () => {
        const from = fromInput.value;
        const to = toInput.value;

        if (!from || !to) {
            result.innerHTML =
                `<span class="text-red-500">Please select both From and To</span>`;
            return;
        }

        result.innerHTML = `
            <div class="space-y-2">
                <div><b>From:</b> ${from}</div>
                <div><b>To:</b> ${to}</div>
            </div>
        `;
    };
}
