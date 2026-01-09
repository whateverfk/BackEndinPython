import { renderDeviceList } from "./views/device/device-List.js";
import { renderDeviceDetail } from "./views/device/deviceDetail.js";
import { hasLive, stopLiveAndCleanup } from
    "./views/device/tabs/Channel-Config/subTabs/liveController.js";


export function initRouter() {
    window.addEventListener("hashchange", route);
    route();
}


async function route() {
    const app = document.getElementById("app");
    const hash = location.hash || "#/devices";

    app.innerHTML = "";
    if (!hash.startsWith("#/devices/") && hasLive()) {
        await stopLiveAndCleanup();
    }
    // /devices
    if (hash === "#/devices") {
        renderDeviceList(app);
        return;
    }



    // /devices/:id
    const match = hash.match(/^#\/devices\/(\d+)$/);
    if (match) {
        setLayout("detail");
        renderDeviceDetail(app, match[1]);
        return;
    }

    app.innerHTML = "<p>Not found</p>";
}



function setLayout(mode) {
    const layout = document.getElementById("layout");

    if (mode === "detail") {
        layout.className =
  "bg-white p-6 rounded-lg shadow-lg mx-auto w-full max-w-screen-xl";

    } else {
        layout.className =
            "bg-white p-6 rounded-lg shadow-lg mx-auto w-full max-w-md";
    }
}



window.addEventListener("beforeunload", (e) => {
    if (hasLive()) {
        // KHÔNG await được ở đây
        stopLiveAndCleanup();
    }
});