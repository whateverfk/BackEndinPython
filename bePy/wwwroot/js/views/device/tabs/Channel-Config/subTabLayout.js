import { hasLive, stopLiveAndCleanup } from "./subTabs/liveController.js";

// --- Bind sub-tabs với device ---
export function bindSubTabs(device, map) {
    let currentSubTab = Object.keys(map)[0]; // mặc định sub-tab đầu tiên

    document.querySelectorAll("[data-subtab]").forEach(btn => {
        btn.onclick = async () => {
            const next = btn.dataset.subtab;

            // Nếu đang ở live tab, dừng live trước khi đổi
            // Nếu đang có live và rời khỏi config → stop
            if (hasLive() && currentSubTab === "config" && next !== "config") {
                await stopLiveAndCleanup();
            }


            // Chuyển giao diện sub-tab
            setActive(next);

            // Xóa nội dung cũ
            document.getElementById("channelSubContent").innerHTML = "";

            currentSubTab = next;

            // Render nội dung sub-tab
            await map[next]?.(device);

            // Cập nhật subtab vào URL
            const url = new URL(window.location);
            url.searchParams.set("subtab", next);
            window.history.replaceState(null, "", url);
        };
    });
}

// --- Render nút sub-tab ---
function subTabBtn(id, label, active = false) {
    return `
        <button
            data-subtab="${id}"
            class="flex-1 text-center pb-2 font-semibold ${
                active
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-blue-600"
            }"
        >
            ${label}
        </button>
    `;
}

// --- Render layout sub-tab ---
export function renderSubTabLayout() {
    return `
        <div class="flex border-b mb-4">
            ${subTabBtn("config", "Config")}
            ${subTabBtn("schedule", "Schedule")}
            
        </div>

        <div id="channelSubContent"></div>
    `;
}

// --- Chọn active sub-tab ---
export function setActive(tab) {
    // Xóa class active từ tất cả sub-tab
    document.querySelectorAll("[data-subtab]").forEach(b => {
        b.classList.remove("border-b-2", "border-blue-500", "text-blue-600");
        b.classList.add("text-gray-500");
    });

    // Thêm class active cho sub-tab đang chọn
    document.querySelector(`[data-subtab="${tab}"]`)?.classList.add(
        "border-b-2",
        "border-blue-500",
        "text-blue-600"
    );
}
