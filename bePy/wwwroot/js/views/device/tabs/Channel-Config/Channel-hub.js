import { renderSubTabLayout, bindSubTabs } from "./subTabLayout.js";
import { renderConfigTab } from "./subTabs/config.js";
import { renderScheduleTab } from "./subTabs/schedule.js";
//import { renderLiveViewTab } from "./subTabs/live.js";

export async function renderChannelConfig(device) {
    const box = document.getElementById("detailContent");

    box.innerHTML = renderSubTabLayout();

    bindSubTabs(device, {
        config: renderConfigTab,
        schedule: renderScheduleTab,
        //live: renderLiveViewTab
    });

    // default sub-tab
    await renderConfigTab(device);
}
