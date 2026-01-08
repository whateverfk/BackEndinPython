import { API_URL } from "../../config.js";
import { renderSystemInfo } from "./tabs/system-Info.js";
//import { renderChannelConfig } from "./tabs/Channel-Config/Channel-Config.js";
import { renderChannelConfig } from "./tabs/Channel-Config/Channel-hub.js";
import { renderUsers } from "./tabs/users.js";
import { renderIntegration } from "./tabs/integration.js";
import { renderStorage } from "./tabs/storage.js";


import { hasLive, stopLiveAndCleanup } from
    "./tabs/Channel-Config/subTabs/liveController.js";

function bindTabs(device) {
    document.querySelectorAll("[data-tab]").forEach(btn => {
        btn.onclick = async () => {

            if (hasLive()) {
                await stopLiveAndCleanup();
            }

            setActiveTab(btn.dataset.tab);

            const map = {
                info: () => renderSystemInfo(device),
                channel: () => renderChannelConfig(device),
                users: () => renderUsers(device),
                integration: () => renderIntegration(device),
                storage: () => renderStorage(device)
            };

            map[btn.dataset.tab]?.();
        };
    });
}

export async function renderDeviceDetail(container, id) {

    const d = await apiFetch(`${API_URL}/api/devices/${id}`);
    window.currentDevice = d;

    container.innerHTML = `
        <button class="mb-4 text-blue-600 hover:underline"
            id="btnBack">← Back</button>

        <h2 class="text-xl font-bold mb-4">
            Device ${d.ip_web}
        </h2>

        <div class="flex gap-4 border-b mb-4">
            ${tabBtn("info", "System Info", true)}
            ${tabBtn("channel", "Channel Config")}
            ${tabBtn("users", "User & Permission")}
            ${tabBtn("integration", "Integration User")}
            ${tabBtn("storage", "Storage")}
        </div>

        <div id="detailContent" class="pt-4"></div>
    `;

    document.getElementById("btnBack").onclick =
        () => location.hash = "#/devices";

    bindTabs(d);
    renderSystemInfo(d);
}

function tabBtn(id, label, active = false) {
    return `
        <button
            data-tab="${id}"
            class="pb-2 font-semibold ${
                active
                    ? "border-b-2 border-teal-500 text-teal-600"
                    : "text-gray-500 hover:text-teal-600"
            }"
        >
            ${label}
        </button>
    `;
}


function setActiveTab(tab) {
    document.querySelectorAll("[data-tab]").forEach(b => {
        b.classList.remove("border-b-2", "border-teal-500", "text-teal-600");
        b.classList.add("text-gray-500");
    });

    const active = document.querySelector(`[data-tab="${tab}"]`);
    active.classList.add("border-b-2", "border-teal-500", "text-teal-600");
}
