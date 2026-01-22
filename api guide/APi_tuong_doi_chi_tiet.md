# Tài liệu API - Hệ thống Quản lý NVR Hikvision

## Mục lục
1. [Tổng quan](#tổng-quan)
2. [Xác thực](#xác-thực)
3. [Mô hình dữ liệu](#mô-hình-dữ-liệu)
4. [Các điểm cuối API](#các-điểm-cuối-api)
   - [Xác thực](#các-điểm-cuối-xác-thực)
   - [Thiết bị](#thiết-bị)
   - [Kênh](#cấu-hình-kênh)
   - [Thông tin hệ thống](#thông-tin-hệ-thống-thiết-bị)
   - [Người dùng thiết bị](#người-dùng-thiết-bị-isapi)
   - [Quyền người dùng](#quyền-người-dùng)
   - [Cảnh báo](#cảnh-báo)
   - [Đồng bộ hóa](#đồng-bộ-hóa)
   - [Nhật ký](#nhật-ký)
   - [Cấu hình màn hình](#cấu-hình-màn-hình)
   - [Phát trực tiếp](#phát-trực-tiếp)
5. [Xử lý lỗi](#xử-lý-lỗi)
6. [Tham chiếu nhanh](#tham-chiếu-nhanh-các-điểm-cuối)

## Tổng quan

**URL cơ sở**: `http://your-server:8000`  
**Phiên bản**: v1.0  
**Công nghệ chính**: FastAPI + PostgreSQL + SQLAlchemy (Async)

API này quản lý các thiết bị NVR Hikvision, kênh, ghi hình, quyền người dùng, cảnh báo và phát trực tiếp.

### Tóm tắt điểm cuối API

**Tổng cộng**: 50+ điểm cuối

| Danh mục | Số điểm cuối | Mô tả |
|----------|--------------|-------|
| **Xác thực** | 3 | Đăng ký, đăng nhập, quản lý mật khẩu |
| **Thiết bị** | 11 | CRUD, kiểm tra kết nối, kênh, bản ghi, đồng bộ |
| **Kênh** | 7 | Cấu hình, lịch ghi, đồng bộ, khả năng |
| **Thông tin hệ thống** | 6 | Thông tin hệ thống, lưu trữ, người dùng ONVIF |
| **Người dùng thiết bị** | 2 | Quản lý người dùng ISAPI |
| **Quyền người dùng** | 4 | Quyền toàn cục & kênh |
| **Cảnh báo** | 3 | Danh sách, lọc, xóa |
| **Đồng bộ** | 3 | Kích hoạt thủ công, cài đặt |
| **Nhật ký** | 2 | Nhật ký đồng bộ, nhật ký ISAPI thiết bị |
| **Cấu hình màn hình** | 2 | Cài đặt hiển thị |
| **Phát trực tiếp** | 3 | Bắt đầu/dừng HLS, nhịp tim |

## Xác thực

### Cấu trúc mã thông báo JWT

Tất cả các điểm cuối được bảo vệ yêu cầu xác thực mã thông báo Bearer JWT.

**Định dạng tiêu đề**:
```
Authorization: Bearer <token>
```

**Payload JWT**:
```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "role": "SuperAdmin",
  "superadmin_id": "uuid-string",
  "exp": 1705939200
}
```

### Các điểm cuối xác thực

#### Đăng ký người dùng
```http
POST /api/auth/register
```

**Thân yêu cầu**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Xác thực**: username ≥ 3 ký tự, mật khẩu ≥ 6 ký tự

**Phản hồi (200)**:
```json
{
  "token": "eyJhbGc..."
}
```

#### Đăng nhập
```http
POST /api/auth/login
```

**Thân yêu cầu**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Phản hồi (200)**:
```json
{
  "token": "eyJhbGc..."
}
```

#### Thay đổi mật khẩu
```http
POST /api/auth/change-password
Authorization: Bearer <token>
```

**Thân yêu cầu**:
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

## Mô hình dữ liệu

### User (Người dùng)
- **id**: String(36) PK
- **username**: String(50) Duy nhất
- **password_hash**: String(255)
- **role**: String(20) - Mặc định: "SuperAdmin"
- **is_active**: Boolean - Mặc định: True
- **Quan hệ**: thiết bị, nhật ký đồng bộ, cài đặt đồng bộ, cài đặt màn hình, thông báo cảnh báo

### Device (Thiết bị)
- **id**: Integer PK
- **ip_nvr**: String(50) - Địa chỉ IP NVR
- **ip_web**: String(50) - Địa chỉ IP giao diện web
- **username**: String(50)
- **password**: String(100) - Mã hóa
- **brand**: String(50) - vd: "hikvision"
- **is_checked**: Boolean - Trạng thái hoạt động
- **owner_superadmin_id**: String(36) FK → users.id
- **Quan hệ**: kênh, người dùng (DeviceUser), thông tin hệ thống

### Channel (Kênh)
- **id**: Integer PK
- **device_id**: Integer FK → devices.id
- **channel_no**: Integer - Số kênh trên thiết bị
- **name**: String(100)
- **connected_type**: String(20)
- **oldest_record_date**: Date
- **latest_record_date**: Date
- **is_active**: Boolean
- **Quan hệ**: ngày ghi, extension, cấu hình luồng, ghi hình, dòng thời gian ghi

### DeviceUser (Người dùng thiết bị)
Người dùng cấp thiết bị (từ ISAPI)
- **id**: Integer PK
- **device_id**: Integer FK → devices.id
- **user_id**: Integer - ID người dùng từ thiết bị
- **user_name**: String(50)
- **role**: String(20) - admin/operator
- **is_active**: Boolean

### Quyền người dùng

**UserGlobalPermission**: Quyền cấp thiết bị
- scope: "local" hoặc "remote"
- Fields: nâng cấp, cấu hình tham số, khởi động lại hoặc tắt, kiểm tra nhật ký hoặc trạng thái, quản lý kênh, phát lại, ghi, sao lưu, điều khiển PTZ, xem trước, nói chuyện thoại, v.v.

**UserChannelPermission**: Quyền cấp kênh
- scope: "local" hoặc "remote"
- permission: String(30)
- enabled: Boolean

### AlarmMessage (Thông báo cảnh báo)
- **id**: Integer PK
- **user_id**: String(36) FK → users.id
- **device_id**: Integer FK → devices.id
- **channel_id_in_device**: String(32)
- **event**: String(64) - Loại sự kiện
- **message**: Text
- **created_at**: DateTime

## Các điểm cuối API

### Thiết bị

#### Liệt kê tất cả thiết bị
```http
GET /api/devices
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Lấy thiết bị hoạt động
```http
GET /api/devices/active
Authorization: Bearer <token>
```

#### Kiểm tra kết nối thiết bị
```http
POST /api/devices/test-connection
Authorization: Bearer <token>
```

**Thân yêu cầu**:
```json
{
  "ip_web": "192.168.1.64",
  "username": "admin",
  "password": "admin123",
  "brand": "hikvision"
}
```

**Phản hồi (200)**:
```json
{
  "ip_reachable": true,
  "auth_ok": true,
  "message": "OK"
}
```

#### Tạo thiết bị
```http
POST /api/devices
Authorization: Bearer <token>
```

**Thân yêu cầu**:
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

**Phản hồi (201)**:
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

#### Cập nhật thiết bị
```http
PUT /api/devices/{id}
Authorization: Bearer <token>
```

**Thân yêu cầu** (cập nhật riêng phần):
```json
{
  "ip_web": "192.168.1.65",
  "is_checked": false
}
```

**Phản hồi**: 204 No Content

#### Xóa thiết bị
```http
DELETE /api/devices/{id}
Authorization: Bearer <token>
```

**Phản hồi**: 204 No Content

#### Lấy các kênh của thiết bị
```http
GET /api/devices/{id}/channels
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Lấy ngày ghi của kênh
```http
GET /api/devices/channels/{channel_id}/record_days_full
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Lấy dữ liệu tháng cho tất cả kênh
```http
GET /api/devices/{id}/channels/month_data/{date_str}
Authorization: Bearer <token>
```

**Tham số đường dẫn**:
- `date_str`: Định dạng "YYYY-MM" (vd: "2025-01")

**Phản hồi (200)**:
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

### Cấu hình kênh

#### Lấy thông tin kênh
```http
GET /api/device/{device_id}/channel/{channel_id}/infor
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Cập nhật cấu hình kênh
```http
PUT /api/device/{device_id}/channel/{channel_id}/infor
Authorization: Bearer <token>
```

**Thân yêu cầu**:
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

**Phản hồi (200)**:
```json
{"status": "ok"}
```

#### Đồng bộ hóa kênh từ thiết bị
```http
GET /api/device/{device_id}/channel/{channel_id}/infor/sync
Authorization: Bearer <token>
```

Tìm nạp cấu hình mới nhất từ thiết bị vật lý và cập nhật cơ sở dữ liệu.

#### Lấy lịch chế độ ghi hình
```http
GET /api/device/{device_id}/channel/{channel_id}/infor/recording-mode
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

**Chế độ ghi hình**: `continuous`, `motion`, `off`

### Quyền người dùng & Thiết bị

#### Lấy quyền người dùng thiết bị
```http
GET /api/device/{id}/user/{device_user_id}/permissions
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Cập nhật quyền người dùng thiết bị
```http
PUT /api/device/{id}/user/{device_user_id}/permissions
Authorization: Bearer <token>
```

**Thân yêu cầu**:
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

**Phản hồi (200)**:
```json
{
  "success": true,
  "code": "OK",
  "message": "Permission updated successfully"
}
```

#### Đồng bộ hóa tất cả người dùng thiết bị & Quyền
```http
POST /api/device/{id}/user/syncall
Authorization: Bearer <token>
```

Tìm nạp tất cả người dùng từ ISAPI thiết bị và đồng bộ hóa quyền của họ.

**Phản hồi (200)**:
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

### Cảnh báo

#### Liệt kê cảnh báo (Phân trang con trỏ)
```http
GET /api/user/alarm
Authorization: Bearer <token>
```

**Tham số truy vấn**:
- `cursor_time`: DateTime (định dạng ISO)
- `cursor_id`: Integer
- `device_id`: Integer (bộ lọc)
- `event`: String (bộ lọc)
- `channel_id_in_device`: String (bộ lọc)

**Phản hồi (200)**:
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

#### Xóa cảnh báo
```http
DELETE /api/user/alarm/{alarm_id}
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{"detail": "Alarm deleted successfully"}
```

#### Xóa tất cả cảnh báo
```http
DELETE /api/user/alarm
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{
  "detail": "All alarms deleted",
  "deleted_count": 45
}
```

### Đồng bộ hóa

#### Kích hoạt đồng bộ ngay
```http
POST /api/sync/now
Authorization: Bearer <token>
```

Kích hoạt đồng bộ hóa ngay lập tức tất cả các thiết bị hoạt động.

**Phản hồi (200)**:
```json
{"message": "Sync started"}
```

#### Lấy cài đặt đồng bộ
```http
GET /api/sync/setting
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{
  "is_enabled": true,
  "interval_minutes": 60
}
```

#### Cập nhật cài đặt đồng bộ
```http
POST /api/sync/setting
Authorization: Bearer <token>
```

**Thân yêu cầu**:
```json
{
  "is_enabled": true,
  "interval_minutes": 30
}
```

**Phản hồi (200)**:
```json
{"message": "Saved"}
```

### Phát trực tiếp

#### Bắt đầu phát trực tiếp
```http
GET /api/device/{device_id}/channel/{channel_id}/live
Authorization: Bearer <token>
```

Bắt đầu luồng HLS qua FFmpeg.

**Phản hồi (200)**:
```json
{
  "status": "ok",
  "hls_url": "/hls/{device_id}/{channel_id}/index.m3u8"
}
```

#### Dừng phát trực tiếp
```http
POST /api/device/{device_id}/channel/{channel_id}/stop
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{"status": "ok"}
```

#### Nhịp tim
```http
POST /api/device/{device_id}/channel/{channel_id}/heartbeat
Authorization: Bearer <token>
```

Giữ luồng hoạt động. Client nên gọi mỗi 30 giây.

**Phản hồi (200)**:
```json
{"status": "ok"}
```

### Thông tin hệ thống thiết bị

#### Lấy thông tin hệ thống thiết bị
```http
GET /api/device/{id}/infor
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{
  "device_id": 1,
  "model": "DS-7608NI-I2/8P",
  "serial_number": "DS-7608NI-I2/8P0820170101CCRR123456789",
  "firmware_version": "V4.0.1 build 210101",
  "mac_address": "44:19:B6:XX:XX:XX"
}
```

**Lỗi (404)**: Thông tin hệ thống không tìm thấy, đồng bộ trước

#### Đồng bộ thông tin hệ thống thiết bị
```http
POST /api/device/{id}/infor/sync
Authorization: Bearer <token>
```

Tìm nạp thông tin hệ thống từ thiết bị qua ISAPI.

**Phản hồi (200)**:
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

#### Lấy dung lượng lưu trữ thiết bị
```http
GET /api/device/{id}/infor/storage
Authorization: Bearer <token>
```

**Phản hồi (200)**:
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

#### Đồng bộ dung lượng lưu trữ thiết bị
```http
POST /api/device/{id}/infor/storage
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{
  "status": "success",
  "count": 2
}
```

#### Lấy người dùng ONVIF
```http
GET /api/device/{id}/infor/onvif-users
Authorization: Bearer <token>
```

Lấy người dùng tích hợp ONVIF được cấu hình trên thiết bị.

**Phản hồi (200)**:
```json
[
  {
    "user_id": 1,
    "username": "onvif_user",
    "level": "user"
  }
]
```

#### Đồng bộ người dùng ONVIF
```http
POST /api/device/{id}/infor/onvif-users
Authorization: Bearer <token>
```

**Phản hồi (200)**:
```json
{
  "status": "success",
  "count": 3
}
```

### Người dùng thiết bị (ISAPI Users)

#### Lấy người dùng thiết bị
```http
GET /api/device/{id}/user
Authorization: Bearer <token>
```

Trả về danh sách người dùng được cấu hình trên thiết bị (từ ISAPI).

**Phản hồi (200)**:
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

#### Đồng bộ người dùng thiết bị
```http
POST /api/device/{id}/user/sync
Authorization: Bearer <token>
```

Tìm nạp danh sách người dùng từ ISAPI thiết bị và cập nhật cơ sở dữ liệu.

**Phản hồi (200)**:
```json
{
  "status": "success",
  "count": 5
}
```

### Nhật ký

#### Lấy nhật ký đồng bộ
```http
GET /api/logs
Authorization: Bearer <token>
```

Trả về nhật ký đồng bộ gần đây (giới hạn 200, tự động xóa nhật ký cũ hơn 7 ngày).

**Phản hồi (200)**:
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

#### Lấy nhật ký thiết bị (ISAPI)
```http
POST /api/logs/device/{device_id}
Authorization: Bearer <token>
```

Tìm nạp nhật ký trực tiếp từ thiết bị qua ISAPI.

**Thân yêu cầu**:
```json
{
  "from_": "2025-01-22T00:00:00",
  "to": "2025-01-22T23:59:59",
  "maxResults": 100,
  "majorType": "all"
}
```

**Các trường yêu cầu**:
- `from_`: Ngày giờ bắt đầu (định dạng ISO)
- `to`: Ngày giờ kết thúc (định dạng ISO)
- `maxResults`: Integer (1-2000, mặc định 2000)
- `majorType`: String - Bộ lọc loại nhật ký (vd: "all", "alarm", "operation")

**Phản hồi (200)**:
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

### Cấu hình màn hình

#### Lấy cài đặt màn hình
```http
GET /api/config
Authorization: Bearer <token>
```

Lấy cài đặt hiển thị màn hình/dòng thời gian cho người dùng.

**Phản hồi (200)**:
```json
{
  "id": 1,
  "start_day": 1,
  "end_day": 31,
  "order": false,
  "owner_superadmin_id": "uuid-string"
}
```

**Các trường**:
- `start_day`: Integer (1-31) - Ngày bắt đầu theo tháng để giám sát
- `end_day`: Integer (1-31) - Ngày kết thúc theo tháng để giám sát
- `order`: Boolean - Tuỳ chỉnh thứ tự hiển thị

#### Cập nhật cài đặt màn hình
```http
POST /api/config
Authorization: Bearer <token>
```

**Thân yêu cầu**:
```json
{
  "start_day": 1,
  "end_day": 28,
  "order": true
}
```

**Xác thực**: `start_day` phải ≤ `end_day`

**Phản hồi (200)**:
```json
{
  "id": 1,
  "start_day": 1,
  "end_day": 28,
  "order": true,
  "owner_superadmin