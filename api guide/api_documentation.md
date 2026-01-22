# API Documentation - Hikvision NVR Management System

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
   - [Authentication](#auth-endpoints)
   - [Devices](#devices)
   - [Channels](#channel-configuration)
   - [Device System Info](#device-system-information)
   - [Device Users](#device-users-isapi-users)
   - [User Permissions](#device-users--permissions)
   - [Alarms](#alarms)
   - [Sync](#sync)
   - [Logs](#logs)
   - [Monitor Config](#monitor-configuration)
   - [Live Streaming](#live-streaming)
5. [Error Handling](#error-handling)
6. [Quick Reference](#endpoint-quick-reference)

## Overview

**Base URL**: `http://your-server:8000`  
**Version**: v1.0  
**Primary Technology**: FastAPI + PostgreSQL + SQLAlchemy (Async)

This API manages Hikvision NVR devices, channels, recordings, user permissions, alarms, and live streaming.

### API Endpoint Summary

**Total Endpoints**: 50+

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Authentication** | 3 | Register, login, password management |
| **Devices** | 11 | CRUD, test connection, channels, records, sync |
| **Channels** | 7 | Config, recording schedules, sync, capabilities |
| **Device System Info** | 6 | System info, storage, ONVIF users |
| **Device Users** | 2 | ISAPI user management |
| **User Permissions** | 4 | Global & channel permissions |
| **Alarms** | 3 | List, filter, delete |
| **Sync** | 3 | Manual trigger, settings |
| **Logs** | 2 | Sync logs, device ISAPI logs |
| **Monitor Config** | 2 | Display settings |
| **Live Streaming** | 3 | HLS start/stop, heartbeat |



## Authentication

### JWT Token Structure

All protected endpoints require JWT Bearer token authentication.

**Header Format**:
```
Authorization: Bearer <token>
```

**JWT Payload**:
```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "role": "SuperAdmin",
  "superadmin_id": "uuid-string",
  "exp": 1705939200
}
```

### Auth Endpoints

#### Register User
```http
POST /api/auth/register
```

**Request Body**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Validation**: username ≥3 chars, password ≥6 chars

**Response (200)**:
```json
{
  "token": "eyJhbGc..."
}
```

#### Login
```http
POST /api/auth/login
```

**Request Body**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response (200)**:
```json
{
  "token": "eyJhbGc..."
}
```

#### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

## Data Models

### User
- **id**: String(36) PK
- **username**: String(50) Unique
- **password_hash**: String(255)
- **role**: String(20) - Default: "SuperAdmin"
- **is_active**: Boolean - Default: True
- **Relationships**: devices, sync_logs, sync_settings, monitor_settings, alarm_messages

### Device
- **id**: Integer PK
- **ip_nvr**: String(50) - NVR IP address
- **ip_web**: String(50) - Web interface IP
- **username**: String(50)
- **password**: String(100) - Encrypted
- **brand**: String(50) - e.g., "hikvision"
- **is_checked**: Boolean - Active status
- **owner_superadmin_id**: String(36) FK → users.id
- **Relationships**: channels, users (DeviceUser), system_info

### Channel
- **id**: Integer PK
- **device_id**: Integer FK → devices.id
- **channel_no**: Integer - Channel number on device
- **name**: String(100)
- **connected_type**: String(20)
- **oldest_record_date**: Date
- **latest_record_date**: Date
- **is_active**: Boolean
- **Relationships**: record_days, extension, stream_config, recording, recording_timeline

### DeviceUser
Device-level users (from ISAPI)
- **id**: Integer PK
- **device_id**: Integer FK → devices.id
- **user_id**: Integer - User ID from device
- **user_name**: String(50)
- **role**: String(20) - admin/operator
- **is_active**: Boolean

### User Permissions

**UserGlobalPermission**: Device-level permissions
- scope: "local" or "remote"
- Fields: upgrade, parameter_config, restart_or_shutdown, log_or_state_check, manage_channel, playback, record, backup, ptz_control, preview, voice_talk, etc.

**UserChannelPermission**: Channel-level permissions
- scope: "local" or "remote"
- permission: String(30)
- enabled: Boolean

### AlarmMessage
- **id**: Integer PK
- **user_id**: String(36) FK → users.id
- **device_id**: Integer FK → devices.id
- **channel_id_in_device**: String(32)
- **event**: String(64) - Event type
- **message**: Text
- **created_at**: DateTime

## API Endpoints

### Devices

#### List All Devices
```http
GET /api/devices
Authorization: Bearer <token>
```

**Response (200)**:
```json
[
  {
    "id": 1,
    "ip_nvr": "192.168.1.64",
    "ip_web": "192.168.1.64",
    "username": "admin",
    "brand": "hikvision",
    "is_checked": true
  }
]
```

#### Get Active Devices
```http
GET /api/devices/active
Authorization: Bearer <token>
```

#### Test Device Connection
```http
POST /api/devices/test-connection
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "ip_web": "192.168.1.64",
  "username": "admin",
  "password": "admin123",
  "brand": "hikvision"
}
```

**Response (200)**:
```json
{
  "ip_reachable": true,
  "auth_ok": true,
  "message": "OK"
}
```

#### Create Device
```http
POST /api/devices
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "ip_nvr": "192.168.1.64",
  "ip_web": "192.168.1.64",
  "username": "admin",
  "password": "admin123",
  "brand": "hikvision",
  "is_checked": true
}
```

**Response (201)**:
```json
{
  "id": 1,
  "ip_nvr": "192.168.1.64",
  "ip_web": "192.168.1.64",
  "username": "admin",
  "brand": "hikvision",
  "is_checked": true
}
```

#### Update Device
```http
PUT /api/devices/{id}
Authorization: Bearer <token>
```

**Request Body** (partial update):
```json
{
  "ip_web": "192.168.1.65",
  "is_checked": false
}
```

**Response**: 204 No Content

#### Delete Device
```http
DELETE /api/devices/{id}
Authorization: Bearer <token>
```

**Response**: 204 No Content

#### Get Device Channels
```http
GET /api/devices/{id}/channels
Authorization: Bearer <token>
```

**Response (200)**:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "channel_no": 1,
    "name": "Camera 1",
    "is_active": true
  }
]
```

#### Get Channel Record Days
```http
GET /api/devices/channels/{channel_id}/record_days_full
Authorization: Bearer <token>
```

**Response (200)**:
```json
[
  {
    "id": 1,
    "channel_id": 1,
    "record_date": "2025-01-15",
    "has_record": true
  }
]
```

#### Get Month Data for All Channels
```http
GET /api/devices/{id}/channels/month_data/{date_str}
Authorization: Bearer <token>
```

**Path Parameters**:
- `date_str`: Format "YYYY-MM" (e.g., "2025-01")

**Response (200)**:
```json
{
  "oldest_record_month": "2024-12",
  "channels": [
    {
      "channel": {
        "id": 1,
        "channel_no": 1,
        "name": "Camera 1",
        "oldest_record_date": "2024-12-01",
        "latest_record_date": "2025-01-22"
      },
      "record_days": [
        {
          "record_date": "2025-01-15",
          "has_record": true,
          "time_ranges": [
            {"start_time": "08:00:00", "end_time": "18:00:00"}
          ]
        }
      ]
    }
  ]
}
```

### Channel Configuration

#### Get Channel Info
```http
GET /api/device/{device_id}/channel/{channel_id}/infor
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "id": 1,
  "channel_name": "Camera 1",
  "connected_type": "analog",
  "motion_detect": true,
  "resolution_width": 1920,
  "resolution_height": 1080,
  "video_codec": "H.264",
  "max_frame_rate": 2500,
  "fixed_quality": 6,
  "vbr_average_cap": 2048,
  "vbr_upper_cap": 3072,
  "h265_plus": false
}
```

#### Update Channel Config
```http
PUT /api/device/{device_id}/channel/{channel_id}/infor
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "channel_name": "Front Door",
  "motion_detect": true,
  "resolution_width": 1920,
  "resolution_height": 1080,
  "video_codec": "H.265",
  "max_frame_rate": 2500,
  "fixed_quality": 6,
  "vbr_average_cap": 2048,
  "vbr_upper_cap": 3072,
  "h265_plus": true
}
```

**Response (200)**:
```json
{"status": "ok"}
```

#### Sync Channel from Device
```http
GET /api/device/{device_id}/channel/{channel_id}/infor/sync
Authorization: Bearer <token>
```

Fetches latest configuration from the physical device and updates database.

#### Get Recording Mode Schedule
```http
GET /api/device/{device_id}/channel/{channel_id}/infor/recording-mode
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "device_id": 1,
  "channel_id": 1,
  "channel_no": 1,
  "channel_name": "Camera 1",
  "schedule_enable": true,
  "default_mode": "continuous",
  "timeline": [
    {
      "id": 1,
      "day_of_week": 0,
      "day_end_of_week": 0,
      "start_time": "08:00:00",
      "end_time": "18:00:00",
      "mode": "motion"
    }
  ]
}
```

**Recording Modes**: `continuous`, `motion`, `off`

### Device Users & Permissions

#### Get Device User Permissions
```http
GET /api/device/{id}/user/{device_user_id}/permissions
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "device_user_id": 1,
  "user_name": "operator1",
  "global_permissions": {
    "local": {
      "upgrade": false,
      "parameter_config": true,
      "playback": true,
      "ptz_control": false
    },
    "remote": {
      "upgrade": false,
      "playback": true
    }
  },
  "channel_permissions": {
    "1": {
      "local": {"preview": true, "playback": true},
      "remote": {"preview": false}
    }
  }
}
```

#### Update Device User Permissions
```http
PUT /api/device/{id}/user/{device_user_id}/permissions
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "global_permissions": {
    "local": {
      "playback": true,
      "ptz_control": true
    }
  },
  "channel_permissions": {
    "1": {
      "local": {"preview": true}
    }
  }
}
```

**Response (200)**:
```json
{
  "success": true,
  "code": "OK",
  "message": "Permission updated successfully"
}
```

#### Sync All Device Users & Permissions
```http
POST /api/device/{id}/user/syncall
Authorization: Bearer <token>
```

Fetches all users from device ISAPI and syncs their permissions.

**Response (200)**:
```json
{
  "success": true,
  "device_id": 1,
  "total": 5,
  "synced": 5,
  "failed": 0,
  "errors": []
}
```

### Alarms

#### List Alarms (Cursor Pagination)
```http
GET /api/user/alarm
Authorization: Bearer <token>
```

**Query Parameters**:
- `cursor_time`: DateTime (ISO format)
- `cursor_id`: Integer
- `device_id`: Integer (filter)
- `event`: String (filter)
- `channel_id_in_device`: String (filter)

**Response (200)**:
```json
{
  "items": [
    {
      "id": 123,
      "device_id": 1,
      "device_ip_web": "192.168.1.64",
      "event": "motion_detection",
      "channel_id_in_device": "1",
      "channel_name": "Camera 1",
      "message": "Motion detected",
      "created_at": "2025-01-22T10:30:00Z"
    }
  ],
  "next_cursor_time": "2025-01-22T09:00:00Z",
  "next_cursor_id": 100,
  "has_more": true
}
```

#### Delete Alarm
```http
DELETE /api/user/alarm/{alarm_id}
Authorization: Bearer <token>
```

**Response (200)**:
```json
{"detail": "Alarm deleted successfully"}
```

#### Delete All Alarms
```http
DELETE /api/user/alarm
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "detail": "All alarms deleted",
  "deleted_count": 45
}
```

### Sync

#### Trigger Sync Now
```http
POST /api/sync/now
Authorization: Bearer <token>
```

Triggers immediate sync of all active devices.

**Response (200)**:
```json
{"message": "Sync started"}
```

#### Get Sync Settings
```http
GET /api/sync/setting
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "is_enabled": true,
  "interval_minutes": 60
}
```

#### Update Sync Settings
```http
POST /api/sync/setting
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "is_enabled": true,
  "interval_minutes": 30
}
```

**Response (200)**:
```json
{"message": "Saved"}
```

### Live Streaming

#### Start Live Stream
```http
GET /api/device/{device_id}/channel/{channel_id}/live
Authorization: Bearer <token>
```

Starts HLS stream via FFmpeg.

**Response (200)**:
```json
{
  "status": "ok",
  "hls_url": "/hls/{device_id}/{channel_id}/index.m3u8"
}
```

#### Stop Live Stream
```http
POST /api/device/{device_id}/channel/{channel_id}/stop
Authorization: Bearer <token>
```

**Response (200)**:
```json
{"status": "ok"}
```

#### Heartbeat
```http
POST /api/device/{device_id}/channel/{channel_id}/heartbeat
Authorization: Bearer <token>
```

Keeps stream alive. Client should call every 30s.

**Response (200)**:
```json
{"status": "ok"}
```

### Device System Information

#### Get Device System Info
```http
GET /api/device/{id}/infor
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "device_id": 1,
  "model": "DS-7608NI-I2/8P",
  "serial_number": "DS-7608NI-I2/8P0820170101CCRR123456789",
  "firmware_version": "V4.0.1 build 210101",
  "mac_address": "44:19:B6:XX:XX:XX"
}
```

**Error (404)**: System info not found, sync first

#### Sync Device System Info
```http
POST /api/device/{id}/infor/sync
Authorization: Bearer <token>
```

Fetches system information from device via ISAPI.

**Response (200)**:
```json
{
  "status": "ok",
  "source": "device",
  "data": {
    "model": "DS-7608NI-I2/8P",
    "serial_number": "DS-7608NI-I2/8P0820170101CCRR123456789",
    "firmware_version": "V4.0.1 build 210101",
    "mac_address": "44:19:B6:XX:XX:XX"
  }
}
```

#### Get Device Storage
```http
GET /api/device/{id}/infor/storage
Authorization: Bearer <token>
```

**Response (200)**:
```json
[
  {
    "hdd_id": 0,
    "hdd_name": "HDD 0",
    "status": "ok",
    "hdd_type": "sata",
    "capacity": 2000000,
    "free_space": 1500000,
    "property": "RW"
  }
]
```

#### Sync Device Storage
```http
POST /api/device/{id}/infor/storage
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "status": "success",
  "count": 2
}
```

#### Get ONVIF Users
```http
GET /api/device/{id}/infor/onvif-users
Authorization: Bearer <token>
```

Gets ONVIF integration users configured on the device.

**Response (200)**:
```json
[
  {
    "user_id": 1,
    "username": "onvif_user",
    "level": "user"
  }
]
```

#### Sync ONVIF Users
```http
POST /api/device/{id}/infor/onvif-users
Authorization: Bearer <token>
```

**Response (200)**:
```json
{
  "status": "success",
  "count": 3
}
```

### Device Users (ISAPI Users)

#### Get Device Users
```http
GET /api/device/{id}/user
Authorization: Bearer <token>
```

Returns list of users configured on the device (from ISAPI).

**Response (200)**:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "user_id": 1,
    "user_name": "admin",
    "role": "administrator",
    "is_active": true
  },
  {
    "id": 2,
    "device_id": 1,
    "user_id": 2,
    "user_name": "operator",
    "role": "operator",
    "is_active": true
  }
]
```

#### Sync Device Users
```http
POST /api/device/{id}/user/sync
Authorization: Bearer <token>
```

Fetches user list from device ISAPI and updates database.

**Response (200)**:
```json
{
  "status": "success",
  "count": 5
}
```

### Logs

#### Get Sync Logs
```http
GET /api/logs
Authorization: Bearer <token>
```

Returns recent sync logs (limit 200, auto-deletes logs older than 7 days).

**Response (200)**:
```json
[
  {
    "id": 1,
    "device_id": 1,
    "sync_time": "2025-01-22T10:30:00Z",
    "status": "success",
    "message": "Synced 8 channels",
    "owner_superadmin_id": "uuid-string"
  }
]
```

#### Get Device Logs (ISAPI)
```http
POST /api/logs/device/{device_id}
Authorization: Bearer <token>
```

Fetches logs directly from device via ISAPI.

**Request Body**:
```json
{
  "from_": "2025-01-22T00:00:00",
  "to": "2025-01-22T23:59:59",
  "maxResults": 100,
  "majorType": "all"
}
```

**Request Fields**:
- `from_`: Start datetime (ISO format)
- `to`: End datetime (ISO format)
- `maxResults`: Integer (1-2000, defaults to 2000)
- `majorType`: String - Log type filter (e.g., "all", "alarm", "operation")

**Response (200)**:
```json
[
  {
    "eventTime": "2025-01-22T10:15:30",
    "majorType": "alarm",
    "subType": "motionDetection",
    "channelID": 1,
    "description": "Motion detected on Camera 1"
  }
]
```

### Monitor Configuration

#### Get Monitor Settings
```http
GET /api/config
Authorization: Bearer <token>
```

Get monitor/timeline display settings for the user.

**Response (200)**:
```json
{
  "id": 1,
  "start_day": 1,
  "end_day": 31,
  "order": false,
  "owner_superadmin_id": "uuid-string"
}
```

**Fields**:
- `start_day`: Integer (1-31) - Start day of month for monitoring
- `end_day`: Integer (1-31) - End day of month for monitoring
- `order`: Boolean - Display order preference

#### Update Monitor Settings
```http
POST /api/config
Authorization: Bearer <token>
```

**Request Body**:
```json
{
  "start_day": 1,
  "end_day": 28,
  "order": true
}
```

**Validation**: `start_day` must be ≤ `end_day`

**Response (200)**:
```json
{
  "id": 1,
  "start_day": 1,
  "end_day": 28,
  "order": true,
  "owner_superadmin_id": "uuid-string"
}
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET request successful |
| 201 | Created | Device created |
| 204 | No Content | DELETE/PUT successful |
| 400 | Bad Request | Validation failed |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource |
| 500 | Server Error | Internal error |
| 502 | Bad Gateway | Device communication failed |

### Error Messages

**Authentication**:
- `ERROR_MSG_MISSING_AUTH`: "Authorization header missing"
- `ERROR_MSG_INVALID_TOKEN`: "Invalid token"
- `ERROR_MSG_TOKEN_EXPIRED`: "Token expired"
- `ERROR_MSG_INVALID_CREDENTIALS`: "Invalid username or password"
- `ERROR_MSG_USERNAME_EXISTS`: "Username already exists"

**Devices**:
- `ERROR_MSG_DEVICE_NOT_FOUND`: "Device not found"
- `ERROR_MSG_DEVICE_EXISTS`: "Device already exists"
- `ERROR_MSG_CANNOT_REACH_DEVICE`: "Cannot reach device"
- `ERROR_MSG_AUTH_FAILED`: "Authentication failed"
- `ERROR_MSG_UNSUPPORTED_BRAND`: "Unsupported brand"

**Permissions**:
- `ERROR_MSG_LOW_PRIVILEGE`: "Insufficient privilege to modify permissions"
- `ERROR_MSG_INVALID_OPERATION`: "Invalid operation"

## Database Relationships

```
User (SuperAdmin)
 └─→ owns multiple Devices
      ├─→ has DeviceSystemInfo (1-to-1)
      ├─→ has multiple Channels
      │    ├─→ has ChannelExtension (1-to-1)
      │    ├─→ has ChannelStreamConfig (1-to-1)
      │    ├─→ has ChannelRecordingMode (1-to-1)
      │    ├─→ has multiple ChannelRecordingModeTimeline
      │    └─→ has multiple ChannelRecordDay
      │         └─→ has multiple ChannelRecordTimeRange
      └─→ has multiple DeviceUser
           ├─→ has multiple UserGlobalPermission (scope: local/remote)
           └─→ has multiple UserChannelPermission
```

## Notes

1. **Password Encryption**: Device passwords are encrypted using AES before storage
2. **JWT Expiration**: Tokens expire after defined minutes (configurable)
3. **Async Operations**: Background tasks handle device initialization and sync
4. **ISAPI Integration**: Direct integration with Hikvision ISAPI for device management
5. **HLS Streaming**: Live streams use FFmpeg to convert RTSP to HLS
