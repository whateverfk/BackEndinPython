# Tham chiếu nhanh API - Hệ thống Quản lý NVR Hikvision

## Xác thực
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| POST | `/api/auth/register` | Đăng ký người dùng mới |
| POST | `/api/auth/login` | Đăng nhập và lấy mã thông báo JWT |
| POST | `/api/auth/change-password` | Thay đổi mật khẩu (yêu cầu xác thực) |

## Thiết bị
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/devices` | Liệt kê tất cả thiết bị |
| GET | `/api/devices/active` | Liệt kê chỉ thiết bị hoạt động |
| GET | `/api/devices/{id}` | Lấy một thiết bị duy nhất |
| POST | `/api/devices` | Tạo thiết bị mới |
| PUT | `/api/devices/{id}` | Cập nhật thiết bị |
| DELETE | `/api/devices/{id}` | Xóa thiết bị |
| POST | `/api/devices/test-connection` | Kiểm tra kết nối thiết bị |
| GET | `/api/devices/{id}/channels` | Lấy các kênh của thiết bị |
| GET | `/api/devices/channels/{channel_id}/record_days_full` | Lấy tất cả ngày ghi |
| GET | `/api/devices/{id}/channels/month_data/{date}` | Lấy dữ liệu tháng cho tất cả kênh |
| POST | `/api/devices/{id}/get_channels_record_info` | Cập nhật bản ghi kênh |
| POST | `/api/devices/{id}/channelsdata/sync` | Đồng bộ tất cả dữ liệu kênh |

## Cấu hình kênh
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/device/{device_id}/channel/{channel_id}/infor` | Lấy cấu hình kênh |
| PUT | `/api/device/{device_id}/channel/{channel_id}/infor` | Cập nhật cấu hình kênh |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/sync` | Đồng bộ kênh từ thiết bị |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/capabilities` | Lấy chỉ các số giới hạn của cam phát trực tiếp |
| GET | `/api/device/{device_id}/channel/{channel_id}/infor/recording-mode` | Lấy lịch ghi hình |
| POST | `/api/device/{device_id}/channel/{channel_id}/infor/recording-mode/sync` | Đồng bộ chế độ ghi |
| POST | `/api/device/{device_id}/channels/recording-mode/sync` | Đồng bộ ghi cho tất cả kênh |

## Thông tin hệ thống thiết bị
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/device/{id}/infor` | Lấy thông tin hệ thống |
| POST | `/api/device/{id}/infor/sync` | Đồng bộ thông tin hệ thống từ thiết bị |
| GET | `/api/device/{id}/infor/storage` | Lấy thông tin lưu trữ |
| POST | `/api/device/{id}/infor/storage` | Đồng bộ thông tin lưu trữ |
| GET | `/api/device/{id}/infor/onvif-users` | Lấy người dùng ONVIF |
| POST | `/api/device/{id}/infor/onvif-users` | Đồng bộ người dùng ONVIF |

## Người dùng thiết bị (ISAPI)
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/device/{id}/user` | Lấy người dùng thiết bị |
| POST | `/api/device/{id}/user/sync` | Đồng bộ người dùng từ thiết bị |

## Quyền người dùng
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/device/{id}/user/{device_user_id}/permissions` | Lấy quyền người dùng |
| POST | `/api/device/{id}/user/{device_user_id}/permissions/sync` | Đồng bộ quyền |
| PUT | `/api/device/{id}/user/{device_user_id}/permissions` | Cập nhật quyền |
| POST | `/api/device/{id}/user/syncall` | Đồng bộ tất cả người dùng & quyền |

## Cảnh báo
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/user/alarm` | Liệt kê cảnh báo (phân trang con trỏ) |
| DELETE | `/api/user/alarm/{alarm_id}` | Xóa một cảnh báo |
| DELETE | `/api/user/alarm` | Xóa tất cả cảnh báo |

## Đồng bộ hóa giờ
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| POST | `/api/sync/now` | Kích hoạt đồng bộ ngay lập tức |
| GET | `/api/sync/setting` | Lấy cài đặt đồng bộ |
| POST | `/api/sync/setting` | Cập nhật cài đặt đồng bộ |

## Logs
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/logs` | Lấy nhật ký đồng bộ giờ (200 gần đây) |
| POST | `/api/logs/device/{device_id}` | Lấy nhật ký ISAPI thiết bị |

## Cấu hình record status ( time line tháng ngày)
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/config` | Lấy cài đặt |
| POST | `/api/config` | Cập nhật cài đặt |

## Phát trực tiếp
| Phương thức | Điểm cuối | Mô tả |
|-----------|-----------|-------|
| GET | `/api/device/{device_id}/channel/{channel_id}/live` | Bắt đầu luồng HLS |
| POST | `/api/device/{device_id}/channel/{channel_id}/stop` | Dừng luồng |
| POST | `/api/device/{device_id}/channel/{channel_id}/heartbeat` | đảm báo tắt ffmpeg decode nếu tắt tab, browser đột ngột khiến /stop ko gửi đc  |

---

**Tổng cộng**: 50+ điểm cuối

**Xác thực**: Tất cả các điểm cuối ngoại trừ `/api/auth/register` và `/api/auth/login` đều yêu cầu mã thông báo Bearer

## Xử lý lỗi

### Phản hồi lỗi chuẩn
```json
{
  "detail": "Thông báo lỗi"
}
```

### Mã trạng thái HTTP thông dụng

| Mã | Ý nghĩa | Ví dụ |
|----|---------|-------|
| 200 | Thành công | Yêu cầu GET thành công |
| 201 | Đã tạo | Thiết bị được tạo |
| 204 | Không có nội dung | DELETE/PUT thành công |
| 400 | Yêu cầu không hợp lệ | Xác thực thất bại |
| 401 | Chưa được xác thực | Mã thông báo bị thiếu/không hợp lệ |
| 403 | Bị cấm | Quyền không đủ |
| 404 | Không tìm thấy | Tài nguyên không tìm thấy |
| 409 | Xung đột | Tài nguyên trùng lặp |
| 500 | Lỗi máy chủ | Lỗi nội bộ |
| 502 | Bad Gateway | Thiết bị không thể liên lạc |

### Thông báo lỗi

**Xác thực**:
- `ERROR_MSG_MISSING_AUTH`: "Authorization header missing"
- `ERROR_MSG_INVALID_TOKEN`: "Invalid token"
- `ERROR_MSG_TOKEN_EXPIRED`: "Token expired"
- `ERROR_MSG_INVALID_CREDENTIALS`: "Invalid username or password"
- `ERROR_MSG_USERNAME_EXISTS`: "Username already exists"

**Thiết bị**:
- `ERROR_MSG_DEVICE_NOT_FOUND`: "Device not found"
- `ERROR_MSG_DEVICE_EXISTS`: "Device already exists"
- `ERROR_MSG_CANNOT_REACH_DEVICE`: "Cannot reach device"
- `ERROR_MSG_AUTH_FAILED`: "Authentication failed"
- `ERROR_MSG_UNSUPPORTED_BRAND`: "Unsupported brand"

**Quyền**:
- `ERROR_MSG_LOW_PRIVILEGE`: "Insufficient privilege to modify permissions"
- `ERROR_MSG_INVALID_OPERATION`: "Invalid operation"

## Quan hệ cơ sở dữ liệu

```
User (SuperAdmin)
 └─→ sở hữu nhiều Devices
      ├─→ có DeviceSystemInfo (1-to-1)
      ├─→ có nhiều Channels
      │    ├─→ có ChannelExtension (1-to-1)
      │    ├─→ có ChannelStreamConfig (1-to-1)
      │    ├─→ có ChannelRecordingMode (1-to-1)
      │    ├─→ có nhiều ChannelRecordingModeTimeline
      │    └─→ có nhiều ChannelRecordDay
      │         └─→ có nhiều ChannelRecordTimeRange
      └─→ có nhiều DeviceUser
           ├─→ có nhiều UserGlobalPermission (scope: local/remote)
           └─→ có nhiều UserChannelPermission
```

## Ghi chú

1. **Mã hóa mật khẩu**: Mật khẩu thiết bị được mã hóa bằng AES trước khi lưu trữ
2. **Hết hạn JWT**: Mã thông báo hết hạn sau số phút được định cấu hình (có thể tuỳ chỉnh)
3. **Hoạt động không đồng bộ**: Các tác vụ nền xử lý khởi tạo thiết bị và đồng bộ
4. **Tích hợp ISAPI**: Tích hợp trực tiếp với ISAPI Hikvision để quản lý thiết bị
5. **Phát trực tiếp HLS**: Các luồng trực tiếp sử dụng FFmpeg để chuyển đổi RTSP thành HLS
