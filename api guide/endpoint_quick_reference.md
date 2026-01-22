# API Endpoint Quick Reference

## Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| POST | `/api/auth/change-password` | Change password (auth required) |

## Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices |
| GET | `/api/devices/active` | List active devices only |
| GET | `/api/devices/{id}` | Get single device |
| POST | `/api/devices` | Create new device |
| PUT | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |
| POST | `/api/devices/test-connection` | Test device connectivity |
| GET | `/api/devices/{id}/channels` | Get device channels |
| GET | `/api/devices/channels/{channel_id}/record_days_full` | Get all record days |
| GET | `/api/devices/{id}/channels/month_data/{date}` | Get month data for all channels |
| POST | `/api/devices/{id}/get_channels_record_info` | Update channel records |
| POST | `/api/devices/{id}/channelsdata/sync` | Sync all channel data |

## Channel Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/device/{device_id}/channel/{channel_id}/infor` | Get channel config |
| PUT | `/api/device/{device_id}/channel/{channel_id}/infor` | Update channel config |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/sync` | Sync channel from device |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/capabilities` | Get streaming capabilities |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/recording-mode` | Get recording schedule |
| POST | `/api/device/{device_id}/channel/{channel_id}/infor/recording-mode/sync` | Sync recording mode |
| POST | `/api/device/{device_id}/channels/recording-mode/sync` | Sync all channels recording |

## Device System Information
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/device/{id}/infor` | Get system info |
| POST | `/api/device/{id}/infor/sync` | Sync system info from device |
| GET | `/api/device/{id}/infor/storage` | Get storage info |
| POST | `/api/device/{id}/infor/storage` | Sync storage info |
| GET | `/api/device/{id}/infor/onvif-users` | Get ONVIF users |
| POST | `/api/device/{id}/infor/onvif-users` | Sync ONVIF users |

## Device Users (ISAPI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/device/{id}/user` | Get device users |
| POST | `/api/device/{id}/user/sync` | Sync users from device |

## User Permissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/device/{id}/user/{device_user_id}/permissions` | Get user permissions |
| POST | `/api/device/{id}/user/{device_user_id}/permissions/sync` | Sync permissions |
| PUT | `/api/device/{id}/user/{device_user_id}/permissions` | Update permissions |
| POST | `/api/device/{id}/user/syncall` | Sync all users & permissions |

## Alarms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user/alarm` | List alarms (cursor pagination) |
| DELETE | `/api/user/alarm/{alarm_id}` | Delete single alarm |
| DELETE | `/api/user/alarm` | Delete all alarms |

## Sync
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sync/now` | Trigger sync immediately |
| GET | `/api/sync/setting` | Get sync settings |
| POST | `/api/sync/setting` | Update sync settings |

## Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/logs` | Get sync logs (last 200) |
| POST | `/api/logs/device/{device_id}` | Get device ISAPI logs |

## Monitor Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Get monitor settings |
| POST | `/api/config` | Update monitor settings |

## Live Streaming
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/device/{device_id}/channel/{channel_id}/live` | Start HLS stream |
| POST | `/api/device/{device_id}/channel/{channel_id}/stop` | Stop stream |
| POST | `/api/device/{device_id}/channel/{channel_id}/heartbeat` | Keep stream alive |

---

**Total Endpoints**: 50+

**Authentication**: All endpoints except `/api/auth/register` and `/api/auth/login` require Bearer token
