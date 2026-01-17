

# =========================
# JWT CLAIMS
# =========================
# Trước làm băng ASP.NET Identity về sau chuyển sang python nên như thế 
#  from: app/core/security.py and app/api/deps.py
JWT_CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
JWT_CLAIM_NAME_ID = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
JWT_CLAIM_ROLE = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
JWT_CLAIM_SUPERADMIN_ID = "superAdminId"

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# =========================
# HIKVISION ISAPI
# =========================
# XML namespace for Hikvision ISAPI responses, Payload nó yêu cầu, để làm gì thì chịu :V
# from: app/features/deps.py
HIK_XML_NAMESPACE = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

# =========================
# NETWORK & CONNECTION
# =========================
# để check ip connect lúc add
#  from: app/features/deps.py
DEFAULT_IP_PORT = 80
DEFAULT_CONNECTION_TIMEOUT = 3
DEFAULT_AUTH_TIMEOUT = 5

# =========================
# HTTP ERROR MESSAGES
# =========================

ERROR_MSG_DEVICE_NOT_FOUND = "Device not found"
ERROR_MSG_CHANNEL_NOT_FOUND = "Channel not found"
ERROR_MSG_USER_NOT_FOUND = "User not found"
ERROR_MSG_MISSING_AUTH = "Missing Authorization"
ERROR_MSG_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_MSG_USERNAME_EXISTS = "Username exists"
ERROR_MSG_OLD_PASSWORD_INCORRECT = "Old password incorrect"
ERROR_MSG_TOKEN_EXPIRED = "Token expired"
ERROR_MSG_INVALID_TOKEN = "Invalid token"
ERROR_MSG_DEVICE_EXISTS = "Device already exists"
ERROR_MSG_INVALID_DATE_FORMAT = "Invalid date format. Use YYYY-MM"
ERROR_MSG_ALARM_NOT_FOUND = "Alarm not found"
ERROR_MSG_LOW_PRIVILEGE = "Không đủ quyền để thay đổi permission trên thiết bị"
ERROR_MSG_INVALID_OPERATION = "Thao tác không hợp lệ"
ERROR_MSG_CANNOT_REACH_DEVICE = "Cannot reach device IP"
ERROR_MSG_UNSUPPORTED_BRAND = "Unsupported brand"
ERROR_MSG_AUTH_FAILED = "Authentication failed, Xem Lại username , password"
