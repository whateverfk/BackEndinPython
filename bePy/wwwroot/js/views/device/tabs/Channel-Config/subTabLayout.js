import { hasLive, stopLiveAndCleanup } from "./subTabs/liveController.js";

export function bindSubTabs(device, map) {
    let currentSubTab = Object.keys(map)[0];

    document.querySelectorAll("[data-subtab]").forEach(btn => {
        btn.onclick = async () => {
            const next = btn.dataset.subtab;

            if (currentSubTab === "live" && hasLive()) {
                await stopLiveAndCleanup();
            }

            setActive(next);
            document.getElementById("channelSubContent").innerHTML = "";

            currentSubTab = next;
            await map[next]?.(device);
        };
    });
}


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



function setActive(tab) {
    document.querySelectorAll("[data-subtab]").forEach(b => {
        b.classList.remove("border-b-2", "border-blue-500", "text-blue-600");
        b.classList.add("text-gray-500");
    });

    document
        .querySelector(`[data-subtab="${tab}"]`)
        .classList.add("border-b-2", "border-blue-500", "text-blue-600");
}
