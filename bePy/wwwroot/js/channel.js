document.addEventListener("DOMContentLoaded", () => {
    loadDeviceList();
});

async function loadDeviceList() {
    const ul = document.getElementById("deviceList");
    ul.innerHTML = "<li>Loading...</li>";

    try {
        const res = await fetch("http://127.0.0.1:8000/api/devices", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token"),
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            throw new Error("Load devices failed");
        }

        const devices = await res.json();
        ul.innerHTML = "";

        if (!devices.length) {
            ul.innerHTML = "<li>No devices</li>";
            return;
        }

        devices.forEach(d => {
            const li = document.createElement("li");
            li.className = "device-row";

            li.innerHTML = `
                <div class="device-info">
                    <div class="device-ip">${d.ip_web}</div>
                    <div class="device-user">${d.username}</div>
                </div>

                <div class="device-actions">
                    <button class="device-btn"
                            onclick="deviceAction('${d.id}')">
                        Action
                    </button>

                    <button class="device-btn newest"
                            onclick="Get All Newest Data('${d.id}')">
                        Get newest data
                    </button>
                </div>
            `;

            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading devices</li>";
    }
}

/**
 * Nút  – tạm thời chưa có tác dụng
 */
function deviceAction(deviceId) {
    loadChannels(deviceId);
}

async function loadChannels(deviceId) {
    const ul = document.getElementById("channelList");
    ul.innerHTML = "<li>Loading channels...</li>";

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/channels`,
            {
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token")
                }
            }
        );

        if (!res.ok) throw new Error("Load channels failed");

        const channels = await res.json();
        ul.innerHTML = "";

        if (!channels.length) {
            ul.innerHTML = "<li>No channels</li>";
            return;
        }

        channels.forEach(ch => {
            const li = document.createElement("li");
            li.className = "channel-row";
            li.textContent = `${ch.name}`;

            li.onclick = () => selectChannel(ch);

            ul.appendChild(li);
        });

    } catch (err) {
        console.error(err);
        ul.innerHTML = "<li>Error loading channels</li>";
    }
}

/**
 * Nút mới – Get Newest Data
***/
async function getNewestData(deviceId) {
    if (!confirm("Get all newest record data for this device? If gonna take a while, please wait.")) return;

    try {
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/${deviceId}/get_channels_record_info`,
            {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token"),
                    "Content-Type": "application/json"
                }
            }
        );

        if (!res.ok) {
            const err = await res.text();
            throw new Error(err);
        }

        alert("Sync channel record info successfully ");

        // reload channel list
        loadChannels(deviceId);

    } catch (err) {
        console.error(err);
        alert("Sync failed ❌");
    }
}


// Select a channel and display its record days and time ranges
// This function is called when a channel is selected
// This function is called when a channel is selected
async function selectChannel(channel) {
    // Update the channel title in the UI
    document.getElementById("channelTitle").innerText = `Record Time – ${channel.name}`;

    console.log("Selected channel:", channel);

    try {
        // Fetch the record days and their time ranges for the selected channel
        const res = await fetch(
            `http://127.0.0.1:8000/api/devices/channels/${channel.id}/record_days_full`,
            {
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token")
                }
            }
        );

        if (!res.ok) throw new Error("Load record days failed");

        const recordDays = await res.json();  // Parse the response as JSON
        const recordDaysContainer = document.getElementById("recordDaysContainer");
        recordDaysContainer.innerHTML = "";  // Clear previous record days

        if (!recordDays.length) {
            recordDaysContainer.innerHTML = "<p>No record days found</p>";
            return;
        }

        // Filter out days where has_record is false
        const filteredRecordDays = recordDays.filter(recordDay => recordDay.has_record);

        if (!filteredRecordDays.length) {
            recordDaysContainer.innerHTML = "<p>No record days with records available</p>";
            return;
        }

        // Loop through each record day and display it
        filteredRecordDays.forEach(recordDay => {
            const recordDayElement = document.createElement("div");
            recordDayElement.className = "record-day";

            // Create the record date (without the "Has Record" line)
            const recordDateElement = document.createElement("h4");
            recordDateElement.innerText = `Date: ${recordDay.record_date}`;
            recordDayElement.appendChild(recordDateElement);

            // If there are time ranges, display them
            if (recordDay.time_ranges && recordDay.time_ranges.length > 0) {
                const timeRangesList = document.createElement("ul");

                // Loop through each time range and display it
                recordDay.time_ranges.forEach(timeRange => {
                    const timeRangeItem = document.createElement("li");
                    timeRangeItem.innerText = `From: ${timeRange.start_time} To: ${timeRange.end_time}`;
                    timeRangesList.appendChild(timeRangeItem);
                });

                recordDayElement.appendChild(timeRangesList);
            } else {
                const noTimeRanges = document.createElement("p");
                noTimeRanges.innerText = "No time ranges available";
                recordDayElement.appendChild(noTimeRanges);
            }

            // Append the record day element to the container
            recordDaysContainer.appendChild(recordDayElement);
        });

    } catch (err) {
        console.error(err);
        alert("Failed to load record days or time ranges");
    }
}
