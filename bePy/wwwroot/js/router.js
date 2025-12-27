import { renderDeviceList } from "./views/device/device-List.js";
import { renderDeviceDetail } from "./views/device/deviceDetail.js";

export function initRouter() {
    window.addEventListener("hashchange", route);
    route();
}

function route() {
    const app = document.getElementById("app");
    const hash = location.hash || "#/devices";

    app.innerHTML = "";

    // /devices
    if (hash === "#/devices") {
        renderDeviceList(app);
        return;
    }

    // /devices/:id
    const match = hash.match(/^#\/devices\/(\d+)$/);
    if (match) {
        renderDeviceDetail(app, match[1]);
        return;
    }

    app.innerHTML = "<p>Not found</p>";
}
