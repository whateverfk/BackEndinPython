function subTabBtn(id, label, active = false) {
    return `
        <button
            data-subtab="${id}"
            class="pb-2 font-semibold ${
                active
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-blue-600"
            }"
        >
            ${label}
        </button>
    `;
}

export function renderSubTabLayout() {
    return `
        <div class="flex gap-4 border-b mb-4">
            ${subTabBtn("config", "Config", true)}
            ${subTabBtn("schedule", "Schedule")}
            ${subTabBtn("live", "Live View")}
        </div>

        <div id="channelSubContent"></div>
    `;
}

export function bindSubTabs(device, tabMap) {
    document.querySelectorAll("[data-subtab]").forEach(btn => {
        btn.onclick = async () => {
            setActive(btn.dataset.subtab);
            await tabMap[btn.dataset.subtab]?.(device);
        };
    });
}

function setActive(tab) {
    document.querySelectorAll("[data-subtab]").forEach(b => {
        b.classList.remove("border-b-2", "border-blue-500", "text-blue-600");
        b.classList.add("text-gray-500");
    });

    document
        .querySelector(`[data-subtab="${tab}"]`)
        .classList.add("border-b-2", "border-blue-500", "text-blue-600");
}
