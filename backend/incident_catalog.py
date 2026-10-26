"""Synthetic incident scenarios for a fictional Vietnamese logistics company.

All targets and actions are local database fixtures. Nothing here reaches a real
device, identity provider, network, or production service.
"""

from __future__ import annotations

from backend.database import CONTROLS_PATH
import json


# tool_id -> the single state change the simulation tool is allowed to make.
TOOLS = {
    "open_case": ("case_status", "open", "Mở hồ sơ sự cố"),
    "hold_onboarding": ("onboarding_status", "on_hold", "Tạm dừng tiếp nhận nhân sự"),
    "restrict_sensitive_access": ("sensitive_access", "restricted", "Hạn chế quyền truy cập dữ liệu nhạy cảm"),
    "schedule_training": ("training_status", "assigned", "Giao khóa đào tạo bổ sung"),
    "preserve_logs": ("logs_preserved", True, "Niêm phong bản ghi sự kiện"),
    "disable_account": ("account_status", "disabled", "Vô hiệu hóa tài khoản mô phỏng"),
    "revoke_sessions": ("active_sessions", 0, "Thu hồi phiên đăng nhập"),
    "lock_device": ("device_status", "locked", "Khóa thiết bị đầu cuối"),
    "revoke_badge": ("badge_status", "revoked", "Thu hồi thẻ ra vào"),
    "isolate_asset": ("network_isolated", True, "Cô lập tài sản khỏi mạng lab"),
    "quarantine_file": ("file_status", "quarantined", "Cách ly tệp mô phỏng"),
    "block_external_transfer": ("external_transfer", "blocked", "Chặn truyền dữ liệu ra ngoài"),
    "restrict_area": ("area_access", "restricted", "Hạn chế khu vực vật lý"),
    "repair_monitoring": ("monitoring_status", "restored", "Khôi phục giám sát mô phỏng"),
    "activate_safety_plan": ("safety_plan", "active", "Kích hoạt phương án an toàn"),
    "secure_screen": ("screen_state", "locked", "Khóa màn hình mô phỏng"),
    "secure_equipment": ("physical_protection", "secured", "Đưa thiết bị về trạng thái bảo vệ"),
    "mark_asset_missing": ("asset_status", "missing", "Đánh dấu tài sản thất lạc"),
    "quarantine_media": ("media_status", "quarantined", "Cách ly vật mang tin"),
    "switch_utility": ("utility_mode", "backup", "Chuyển sang nguồn dự phòng"),
    "disable_network_port": ("network_port", "disabled", "Tắt cổng mạng mô phỏng"),
    "schedule_maintenance": ("maintenance_status", "scheduled", "Lên lịch bảo trì"),
    "sanitize_asset": ("sanitization_status", "required", "Đưa thiết bị vào quy trình xóa an toàn"),
    "enforce_encryption": ("encryption_status", "enabled", "Bật mã hóa mô phỏng"),
    "reduce_privilege": ("privilege_level", "standard", "Hạ quyền đặc quyền"),
    "restrict_data_access": ("data_access", "restricted", "Thu hẹp quyền truy cập dữ liệu"),
    "lock_repository": ("repository_access", "restricted", "Khóa quyền ghi kho mã nguồn"),
    "require_mfa": ("mfa_required", True, "Bắt buộc xác thực đa yếu tố"),
    "force_password_reset": ("password_reset_required", True, "Yêu cầu đặt lại mật khẩu"),
    "throttle_service": ("service_mode", "rate_limited", "Giới hạn tải dịch vụ mô phỏng"),
    "apply_patch": ("patch_status", "scheduled", "Đưa bản vá vào hàng đợi lab"),
    "restore_baseline": ("baseline_status", "restored", "Khôi phục cấu hình chuẩn"),
    "mask_data": ("data_masking", "enabled", "Che dữ liệu nhạy cảm"),
    "restore_backup": ("restore_status", "verified", "Khôi phục bản sao lưu giả lập"),
    "enable_failover": ("failover_status", "active", "Chuyển dịch vụ sang nút dự phòng"),
    "enable_audit_log": ("audit_log_status", "protected", "Bảo vệ nhật ký kiểm toán"),
    "enable_alerting": ("alerting_status", "enabled", "Bật cảnh báo giám sát"),
    "correct_clock": ("clock_status", "synchronized", "Đồng bộ đồng hồ mô phỏng"),
    "restrict_admin_tools": ("admin_tools", "restricted", "Hạn chế tiện ích quản trị"),
    "block_unapproved_software": ("software_status", "blocked", "Chặn phần mềm chưa được phê duyệt"),
    "block_network_traffic": ("network_policy", "blocked", "Chặn luồng mạng rủi ro"),
    "secure_network_service": ("network_service", "restricted", "Hạn chế dịch vụ mạng"),
    "segment_network": ("network_segment", "isolated", "Cô lập phân đoạn mạng"),
    "block_domain": ("web_filter", "blocked", "Chặn tên miền độc hại mô phỏng"),
    "rotate_key": ("key_status", "rotated", "Luân chuyển khóa mã hóa mô phỏng"),
    "pause_release": ("release_status", "paused", "Tạm dừng phát hành"),
    "enforce_security_requirements": ("security_gate", "enforced", "Bật cổng yêu cầu bảo mật"),
    "restore_secure_architecture": ("architecture_status", "contained", "Cô lập thành phần theo kiến trúc an toàn"),
    "block_unsafe_build": ("build_status", "blocked", "Chặn bản dựng không an toàn"),
    "run_security_scan": ("security_test_status", "queued", "Đưa kiểm thử bảo mật vào hàng đợi"),
    "suspend_vendor_access": ("vendor_access", "suspended", "Tạm dừng quyền truy cập nhà cung cấp"),
    "separate_environments": ("environment_access", "separated", "Khôi phục phân tách môi trường"),
    "rollback_change": ("change_status", "rolled_back", "Hoàn tác thay đổi mô phỏng"),
    "sanitize_test_data": ("test_data_status", "sanitized", "Thay dữ liệu kiểm thử bằng dữ liệu giả lập"),
    "pause_audit_job": ("audit_job_status", "paused", "Tạm dừng tác vụ kiểm toán ảnh hưởng hệ thống"),
}


# control_id: scenario title, event, department, affected entity id/name/type,
# permitted tool ids, mandatory containment tools. One deterministic case per
# selected control; the human-readable control metadata remains in the source catalog.
ROWS = {
    "A.6.1": ("Hồ sơ tuyển dụng bất thường", "Một hồ sơ tuyển dụng có thông tin tham chiếu không khớp nhưng tài khoản nhân viên đã được yêu cầu cấp quyền vào hệ thống nhân sự.", "Nhân sự", "EMP-014", "Hồ sơ nhân viên mới NV-014", "person", ["open_case", "hold_onboarding", "restrict_sensitive_access"], ["hold_onboarding", "restrict_sensitive_access"]),
    "A.6.2": ("Thiếu điều khoản bảo mật lao động", "Nhân viên hợp đồng bắt đầu xử lý bảng lương trước khi hoàn tất xác nhận điều khoản bảo mật trong hệ thống nhân sự.", "Nhân sự", "EMP-021", "Tài khoản nhân viên hợp đồng NV-021", "person", ["open_case", "restrict_sensitive_access"], ["restrict_sensitive_access"]),
    "A.6.3": ("Nhân viên làm theo email lừa đảo mô phỏng", "Trong diễn tập nội bộ, nhân viên nhập thông tin đăng nhập vào trang giả lập và tiếp tục mở phiên làm việc.", "Kế toán", "EMP-008", "Nhân viên kế toán NV-008", "person", ["open_case", "revoke_sessions", "require_mfa", "schedule_training"], ["revoke_sessions", "schedule_training"]),
    "A.6.4": ("Vi phạm quy tắc xử lý dữ liệu", "Nhân viên gửi tệp khách hàng sang kênh cá nhân sau khi đã được nhắc về quy tắc xử lý thông tin.", "Nhân sự", "EMP-006", "Nhân viên vận hành NV-006", "person", ["open_case", "preserve_logs", "restrict_sensitive_access"], ["preserve_logs", "restrict_sensitive_access"]),
    "A.6.5": ("Tài khoản còn hoạt động sau khi nghỉ việc", "Nhân viên đã nghỉ việc nhưng tài khoản ERP, phiên VPN và thẻ ra vào vẫn còn hiệu lực.", "Nhân sự", "EMP-003", "Tài khoản nhân viên NV-003", "person", ["open_case", "disable_account", "revoke_sessions", "revoke_badge", "lock_device"], ["disable_account", "revoke_sessions", "revoke_badge"]),
    "A.6.6": ("Thông tin mật bị chia sẻ sai đối tượng", "Một nhân viên gửi tệp giá vận chuyển nội bộ cho địa chỉ email bên ngoài chưa được phê duyệt.", "Kinh doanh", "EMP-011", "Tài khoản nhân viên kinh doanh NV-011", "person", ["open_case", "block_external_transfer", "revoke_sessions", "preserve_logs"], ["block_external_transfer", "preserve_logs"]),
    "A.6.7": ("Laptop làm việc từ xa bị thất lạc", "Nhân viên báo thất lạc laptop khi làm việc ngoài văn phòng; thiết bị còn phiên VPN và dữ liệu bộ nhớ đệm.", "Kinh doanh", "LAP-REMOTE-01", "Laptop làm việc từ xa LAP-REMOTE-01", "hardware", ["open_case", "mark_asset_missing", "lock_device", "revoke_sessions", "isolate_asset", "enforce_encryption"], ["lock_device", "revoke_sessions", "isolate_asset"]),
    "A.6.8": ("Sự kiện bảo mật chưa được báo cáo", "SOC phát hiện đăng nhập bất thường nhưng sự kiện chưa được chuyển vào hàng xử lý sự cố nội bộ.", "SOC", "SOC-QUEUE-01", "Hàng đợi tiếp nhận sự cố SOC", "software", ["open_case", "enable_alerting", "preserve_logs"], ["open_case", "preserve_logs"]),
    "A.7.1": ("Người lạ vượt vành đai phòng máy", "Cảm biến cửa ghi nhận cửa phụ phòng máy chủ bị mở ngoài khung giờ và không có phiếu công việc.", "An ninh cơ sở", "FAC-PERIMETER-01", "Vành đai phòng máy chủ", "hardware", ["open_case", "restrict_area", "enable_alerting", "preserve_logs"], ["restrict_area", "preserve_logs"]),
    "A.7.2": ("Thẻ khách được dùng lại", "Một thẻ khách tạm thời được quét vào khu vực kho dữ liệu sau giờ hết hạn.", "An ninh cơ sở", "BADGE-GUEST-04", "Thẻ khách GUEST-04", "hardware", ["open_case", "revoke_badge", "restrict_area", "preserve_logs"], ["revoke_badge", "restrict_area"]),
    "A.7.3": ("Tủ mạng văn phòng không khóa", "Nhân viên phát hiện tủ mạng ở khu vực làm việc chung mở khóa và có thiết bị lạ cắm vào.", "Hạ tầng", "CAB-NET-02", "Tủ mạng tầng 2", "hardware", ["open_case", "disable_network_port", "secure_equipment", "preserve_logs"], ["disable_network_port", "secure_equipment"]),
    "A.7.4": ("Camera giám sát mất tín hiệu", "Camera hành lang phòng máy mất tín hiệu trong lúc cảm biến cửa ghi nhận lượt ra vào.", "An ninh cơ sở", "CAM-DC-01", "Camera hành lang phòng máy", "hardware", ["open_case", "repair_monitoring", "restrict_area", "preserve_logs"], ["restrict_area", "preserve_logs"]),
    "A.7.5": ("Cảm biến nước báo rò rỉ", "Cảm biến dưới sàn phòng máy báo nước gần giá đỡ thiết bị; nhiệt độ phòng đang tăng.", "Cơ sở vật chất", "SENSOR-ENV-01", "Cảm biến môi trường phòng máy", "hardware", ["open_case", "activate_safety_plan", "enable_failover", "preserve_logs"], ["activate_safety_plan"]),
    "A.7.6": ("Nhà thầu đi lệch tuyến trong khu vực hạn chế", "Nhật ký thẻ cho thấy nhà thầu bảo trì vào phòng máy mà không có nhân viên giám sát đi kèm.", "An ninh cơ sở", "BADGE-VENDOR-02", "Thẻ nhà thầu VENDOR-02", "hardware", ["open_case", "revoke_badge", "restrict_area", "preserve_logs"], ["restrict_area", "preserve_logs"]),
    "A.7.7": ("Màn hình có dữ liệu khách hàng bị bỏ mở", "Máy trạm quầy tiếp nhận vẫn hiển thị hồ sơ khách hàng sau khi nhân viên rời vị trí.", "Vận hành", "WS-RECEPTION-01", "Máy trạm quầy tiếp nhận", "hardware", ["open_case", "secure_screen", "lock_device", "schedule_training"], ["secure_screen"]),
    "A.7.8": ("Máy chủ đặt sai vị trí thông gió", "Nhiệt độ thiết bị tăng do máy chủ phụ đặt sát vật cản và hệ thống báo quá nhiệt.", "Hạ tầng", "SRV-EDGE-02", "Máy chủ biên SRV-EDGE-02", "hardware", ["open_case", "isolate_asset", "schedule_maintenance", "enable_failover"], ["enable_failover"]),
    "A.7.9": ("Thiết bị mang ra ngoài chưa được trả", "Laptop công ty mang đi công tác quá hạn trả và không gửi tín hiệu quản lý thiết bị.", "Kinh doanh", "LAP-FIELD-03", "Laptop công tác LAP-FIELD-03", "hardware", ["open_case", "mark_asset_missing", "lock_device", "revoke_sessions", "isolate_asset"], ["lock_device", "revoke_sessions"]),
    "A.7.10": ("USB chứa dữ liệu bị thất lạc", "Nhân viên báo mất USB có bản xuất dữ liệu vận đơn sau khi rời văn phòng.", "Vận hành", "USB-OPS-07", "USB nghiệp vụ USB-OPS-07", "hardware", ["open_case", "mark_asset_missing", "quarantine_media", "block_external_transfer"], ["quarantine_media", "block_external_transfer"]),
    "A.7.11": ("Nguồn điện chính chập chờn", "UPS ghi nhận điện áp đầu vào không ổn định và máy chủ xử lý đơn hàng sắp chuyển sang pin dự phòng.", "Hạ tầng", "UPS-DC-01", "Bộ lưu điện UPS-DC-01", "hardware", ["open_case", "switch_utility", "enable_failover", "schedule_maintenance"], ["switch_utility"]),
    "A.7.12": ("Cáp mạng bị can thiệp", "Cảm biến tủ cáp ghi nhận patch cord tới máy chủ kế toán bị thay đổi ngoài cửa sổ bảo trì.", "Hạ tầng", "PATCH-ACC-01", "Cáp mạng máy chủ kế toán", "hardware", ["open_case", "disable_network_port", "isolate_asset", "preserve_logs"], ["disable_network_port", "preserve_logs"]),
    "A.7.13": ("Thiết bị mạng quá hạn bảo trì", "Switch lõi xuất hiện lỗi phần cứng lặp lại và bản ghi bảo trì gần nhất đã quá hạn.", "Hạ tầng", "SW-CORE-01", "Switch lõi SW-CORE-01", "hardware", ["open_case", "enable_failover", "schedule_maintenance", "preserve_logs"], ["enable_failover", "schedule_maintenance"]),
    "A.7.14": ("Ổ cứng cũ chuẩn bị tái sử dụng", "Ổ cứng máy chủ được chuyển sang kho tái sử dụng nhưng trạng thái xóa dữ liệu chưa xác nhận.", "Hạ tầng", "DISK-REUSE-03", "Ổ cứng lưu trữ DISK-REUSE-03", "hardware", ["open_case", "sanitize_asset", "restrict_sensitive_access"], ["sanitize_asset"]),
    "A.8.1": ("Laptop đầu cuối mất kết nối quản lý", "Laptop nhân viên không nhận chính sách mã hóa và vừa phát sinh cảnh báo truy cập dữ liệu ngoại tuyến.", "Hạ tầng CNTT", "LAP-FIN-02", "Laptop phòng tài chính LAP-FIN-02", "hardware", ["open_case", "lock_device", "isolate_asset", "enforce_encryption"], ["isolate_asset"]),
    "A.8.2": ("Tài khoản quản trị dùng ngoài giờ", "Tài khoản đặc quyền đăng nhập từ máy trạm người dùng và thử truy cập máy chủ cơ sở dữ liệu.", "Hạ tầng CNTT", "ADM-OPS-01", "Tài khoản quản trị ADM-OPS-01", "software", ["open_case", "reduce_privilege", "revoke_sessions", "require_mfa", "preserve_logs"], ["revoke_sessions", "reduce_privilege"]),
    "A.8.3": ("Nhân viên truy cập hồ sơ ngoài nhiệm vụ", "Tài khoản nhân viên kho mở hàng loạt hồ sơ lương không thuộc quyền công việc.", "Nhân sự", "APP-HR-PORTAL", "Ứng dụng hồ sơ nhân sự", "software", ["open_case", "restrict_data_access", "revoke_sessions", "preserve_logs"], ["restrict_data_access", "preserve_logs"]),
    "A.8.4": ("Token kho mã nguồn bị lộ", "Token nhà phát triển xuất hiện trong một bản ghi build; có lượt truy cập clone bất thường vào repository.", "Phát triển phần mềm", "REPO-ERP-01", "Kho mã nguồn ERP", "software", ["open_case", "lock_repository", "revoke_sessions", "preserve_logs"], ["lock_repository", "preserve_logs"]),
    "A.8.5": ("Đăng nhập bất thường không có MFA", "Tài khoản từ vị trí mới đăng nhập thành công mà không có bước xác thực đa yếu tố.", "Hạ tầng CNTT", "IDP-CORP-01", "Dịch vụ định danh doanh nghiệp", "software", ["open_case", "revoke_sessions", "require_mfa", "force_password_reset"], ["revoke_sessions", "require_mfa"]),
    "A.8.6": ("Dịch vụ ERP gần cạn tài nguyên", "Hàng đợi xử lý ERP tăng nhanh, CPU và bộ nhớ vượt ngưỡng trong giờ chốt vận đơn.", "Hạ tầng CNTT", "APP-ERP-PROD", "Ứng dụng ERP sản xuất", "software", ["open_case", "throttle_service", "enable_failover", "preserve_logs"], ["throttle_service"]),
    "A.8.7": ("Mã độc thử chạy trên máy trạm", "Tệp đính kèm trong thư giả lập tạo tiến trình đáng ngờ trên máy trạm kế toán.", "SOC", "LAP-FIN-02", "Laptop phòng tài chính LAP-FIN-02", "hardware", ["open_case", "isolate_asset", "quarantine_file", "preserve_logs"], ["isolate_asset", "quarantine_file"]),
    "A.8.8": ("Máy chủ còn lỗ hổng nghiêm trọng", "Bản quét nội bộ giả lập phát hiện thư viện trên máy chủ quản lý vận đơn đã quá hạn vá.", "Hạ tầng CNTT", "SRV-TRACK-01", "Máy chủ theo dõi vận đơn", "software", ["open_case", "isolate_asset", "apply_patch", "preserve_logs"], ["apply_patch"]),
    "A.8.9": ("Cấu hình máy chủ bị trôi chuẩn", "Một thay đổi ngoài quy trình đã bật dịch vụ quản trị từ mạng người dùng trên máy chủ ứng dụng.", "Hạ tầng CNTT", "SRV-APP-02", "Máy chủ ứng dụng SRV-APP-02", "software", ["open_case", "restore_baseline", "block_network_traffic", "preserve_logs"], ["restore_baseline", "block_network_traffic"]),
    "A.8.10": ("Dữ liệu hết hạn chưa được xóa", "Bản xuất dữ liệu khách hàng hết thời hạn lưu trữ vẫn còn trong thư mục chia sẻ nội bộ.", "Vận hành dữ liệu", "FILE-EXPORT-09", "Tệp xuất dữ liệu khách hàng", "software", ["open_case", "restrict_data_access", "sanitize_asset", "preserve_logs"], ["restrict_data_access"]),
    "A.8.11": ("Môi trường thử nghiệm hiển thị dữ liệu thật", "Trang thử nghiệm hiển thị số định danh và thông tin liên hệ của khách hàng thay vì dữ liệu đã che.", "Phát triển phần mềm", "APP-TEST-PORTAL", "Cổng thử nghiệm khách hàng", "software", ["open_case", "mask_data", "pause_release", "preserve_logs"], ["mask_data", "pause_release"]),
    "A.8.12": ("Lượng dữ liệu lớn gửi ra ngoài", "Máy trạm nhân viên chuẩn bị tải nhiều tệp vận đơn lên dịch vụ lưu trữ cá nhân.", "SOC", "LAP-OPS-05", "Laptop vận hành LAP-OPS-05", "hardware", ["open_case", "block_external_transfer", "isolate_asset", "preserve_logs"], ["block_external_transfer", "preserve_logs"]),
    "A.8.13": ("Bản sao lưu ERP lỗi kiểm tra toàn vẹn", "Tác vụ sao lưu gần nhất báo sai checksum và bản phục hồi gần nhất chưa được xác minh.", "Hạ tầng CNTT", "BACKUP-ERP-01", "Kho sao lưu ERP", "software", ["open_case", "restore_backup", "enable_alerting", "preserve_logs"], ["enable_alerting"]),
    "A.8.14": ("Nút dự phòng không nhận lưu lượng", "Nút xử lý dự phòng mất heartbeat trong lúc nút chính báo tải cao.", "Hạ tầng CNTT", "CLUSTER-ERP-01", "Cụm xử lý ERP", "software", ["open_case", "enable_failover", "schedule_maintenance", "preserve_logs"], ["enable_failover"]),
    "A.8.15": ("Nhật ký đăng nhập bị xóa", "Một máy chủ ngừng gửi log và có dấu hiệu tài khoản quản trị xóa bản ghi cục bộ.", "SOC", "LOG-AGENT-SRV-02", "Agent nhật ký máy chủ", "software", ["open_case", "enable_audit_log", "preserve_logs", "revoke_sessions"], ["enable_audit_log", "preserve_logs"]),
    "A.8.16": ("Nhiều lần dò quét dịch vụ", "Giám sát mạng ghi nhận nhiều lần dò cổng từ một máy trạm nội bộ tới các máy chủ.", "SOC", "SENSOR-NET-01", "Cảm biến giám sát mạng", "software", ["open_case", "enable_alerting", "isolate_asset", "preserve_logs"], ["enable_alerting", "preserve_logs"]),
    "A.8.17": ("Log giữa hai máy chủ lệch thời gian", "Thời gian ghi log của máy chủ ERP lệch nhiều phút so với máy chủ định danh, làm khó đối chiếu sự kiện.", "Hạ tầng CNTT", "NTP-CORP-01", "Dịch vụ đồng bộ giờ", "software", ["open_case", "correct_clock", "preserve_logs"], ["correct_clock"]),
    "A.8.18": ("Tiện ích quản trị được chạy trái phép", "Một công cụ quản trị hệ thống được chạy từ tài khoản người dùng thường trên máy trạm kế toán.", "SOC", "WS-FIN-02", "Máy trạm kế toán WS-FIN-02", "hardware", ["open_case", "restrict_admin_tools", "isolate_asset", "preserve_logs"], ["restrict_admin_tools", "preserve_logs"]),
    "A.8.19": ("Phần mềm chưa duyệt được cài lên máy chủ", "Gói tiện ích tải ngoài xuất hiện trên máy chủ ứng dụng mà không có yêu cầu thay đổi.", "Hạ tầng CNTT", "SRV-APP-02", "Máy chủ ứng dụng SRV-APP-02", "software", ["open_case", "block_unapproved_software", "isolate_asset", "preserve_logs"], ["block_unapproved_software", "preserve_logs"]),
    "A.8.20": ("Lưu lượng lạ tới mạng máy chủ", "Gateway ghi nhận kết nối từ VLAN khách tới máy chủ cơ sở dữ liệu nội bộ.", "Hạ tầng CNTT", "FW-EDGE-01", "Tường lửa biên FW-EDGE-01", "hardware", ["open_case", "block_network_traffic", "segment_network", "preserve_logs"], ["block_network_traffic", "preserve_logs"]),
    "A.8.21": ("Dịch vụ mạng quản trị lộ ra vùng người dùng", "Bảng điều khiển quản trị dịch vụ được truy cập từ dải mạng nhân viên thay vì mạng quản trị.", "Hạ tầng CNTT", "SVC-MGMT-01", "Dịch vụ quản trị mạng", "software", ["open_case", "secure_network_service", "restrict_admin_tools", "preserve_logs"], ["secure_network_service"]),
    "A.8.22": ("Máy chủ thử nghiệm nối cùng phân đoạn sản xuất", "Máy thử nghiệm phát hiện đường mạng trực tiếp tới cơ sở dữ liệu đang vận hành.", "Hạ tầng CNTT", "VLAN-TEST-01", "Phân đoạn mạng kiểm thử", "hardware", ["open_case", "segment_network", "block_network_traffic", "preserve_logs"], ["segment_network", "block_network_traffic"]),
    "A.8.23": ("Trình duyệt mở tên miền độc hại", "Máy trạm người dùng yêu cầu truy cập tên miền giả lập phát tán mã độc.", "SOC", "WEB-GATEWAY-01", "Gateway lọc web", "software", ["open_case", "block_domain", "isolate_asset", "preserve_logs"], ["block_domain"]),
    "A.8.24": ("Khóa mã hóa sắp hết hạn", "Hệ thống phát hiện khóa mã hóa dùng cho tệp vận đơn nhạy cảm sắp hết hạn và một bản xuất chưa được mã hóa.", "Hạ tầng CNTT", "KMS-CORP-01", "Dịch vụ quản lý khóa", "software", ["open_case", "rotate_key", "enforce_encryption", "restrict_data_access"], ["enforce_encryption"]),
    "A.8.25": ("Tính năng mới bỏ qua cổng kiểm tra bảo mật", "Một nhánh phát triển được đề nghị phát hành khi các bước rà soát bảo mật chưa hoàn tất.", "Phát triển phần mềm", "PIPELINE-ERP-01", "Pipeline phát hành ERP", "software", ["open_case", "pause_release", "run_security_scan"], ["pause_release"]),
    "A.8.26": ("Ứng dụng mới thiếu yêu cầu phân quyền", "Đặc tả chức năng cổng đối tác chưa xác định phân quyền và thời hạn phiên trước khi bắt đầu triển khai.", "Phát triển phần mềm", "APP-PARTNER-01", "Cổng đối tác doanh nghiệp", "software", ["open_case", "enforce_security_requirements", "pause_release"], ["enforce_security_requirements", "pause_release"]),
    "A.8.27": ("Dịch vụ nội bộ tin cậy toàn bộ mạng", "Một dịch vụ nội bộ chấp nhận yêu cầu từ mọi phân đoạn mà không kiểm tra danh tính dịch vụ.", "Kiến trúc CNTT", "SVC-ORDER-01", "Dịch vụ xử lý đơn hàng", "software", ["open_case", "restore_secure_architecture", "segment_network", "preserve_logs"], ["restore_secure_architecture"]),
    "A.8.28": ("Mã nguồn có chuỗi bí mật", "Quét mã nguồn phát hiện chuỗi khóa truy cập giả lập được commit vào nhánh tính năng.", "Phát triển phần mềm", "REPO-ORDER-01", "Kho mã nguồn đơn hàng", "software", ["open_case", "lock_repository", "rotate_key", "pause_release"], ["lock_repository", "pause_release"]),
    "A.8.29": ("Kiểm thử bảo mật phát hiện lỗi nghiêm trọng", "Bản build ứng viên phát hành còn lỗi phân quyền mức nghiêm trọng chưa được xử lý.", "QA bảo mật", "BUILD-PORTAL-09", "Bản build cổng khách hàng", "software", ["open_case", "run_security_scan", "pause_release", "block_unsafe_build"], ["pause_release", "block_unsafe_build"]),
    "A.8.30": ("Tài khoản nhà thầu còn quyền truy cập", "Tài khoản nhà cung cấp phát triển vẫn truy cập repository sau khi hợp đồng hỗ trợ kết thúc.", "Phát triển phần mềm", "VENDOR-DEV-01", "Tài khoản nhà cung cấp DEV-01", "software", ["open_case", "suspend_vendor_access", "revoke_sessions", "preserve_logs"], ["suspend_vendor_access", "revoke_sessions"]),
    "A.8.31": ("Thông tin xác thực sản xuất xuất hiện ở môi trường thử", "Cấu hình kiểm thử chứa thông tin kết nối giống môi trường sản xuất trong lúc chạy thử nghiệm.", "Hạ tầng CNTT", "ENV-TEST-01", "Môi trường kiểm thử", "software", ["open_case", "separate_environments", "rotate_key", "restrict_data_access"], ["separate_environments", "restrict_data_access"]),
    "A.8.32": ("Thay đổi tường lửa chưa được duyệt", "Một quy tắc firewall mới mở cổng quản trị được đẩy vào cấu hình mà chưa có người phê duyệt.", "Hạ tầng CNTT", "CHANGE-FW-018", "Yêu cầu thay đổi FW-018", "software", ["open_case", "rollback_change", "preserve_logs"], ["rollback_change"]),
    "A.8.33": ("Bộ dữ liệu kiểm thử chứa thông tin khách hàng", "Tệp dữ liệu đưa vào môi trường QA có số điện thoại và địa chỉ vận chuyển thật thay vì dữ liệu giả.", "QA dữ liệu", "DATASET-QA-04", "Bộ dữ liệu kiểm thử QA-04", "software", ["open_case", "sanitize_test_data", "restrict_data_access", "preserve_logs"], ["sanitize_test_data", "restrict_data_access"]),
    "A.8.34": ("Tác vụ kiểm toán gây tải lên hệ thống sản xuất", "Một truy vấn kiểm toán mô phỏng chạy quá rộng và làm tăng độ trễ của cơ sở dữ liệu sản xuất.", "Kiểm toán CNTT", "DB-PROD-01", "Cơ sở dữ liệu sản xuất ERP", "software", ["open_case", "pause_audit_job", "throttle_service", "preserve_logs"], ["pause_audit_job"]),
}


def load_scenarios() -> list[dict]:
    controls = {c["control_id"]: c for c in json.loads(CONTROLS_PATH.read_text(encoding="utf-8"))}
    if set(ROWS) != set(controls):
        missing = sorted(set(controls) - set(ROWS))
        extra = sorted(set(ROWS) - set(controls))
        raise RuntimeError(f"Incident catalog mismatch; missing={missing}, extra={extra}")
    result = []
    for control_id, row in ROWS.items():
        title, event, department, target_id, target_name, target_type, allowed, mandatory = row
        control = controls[control_id]
        for action_id in allowed + mandatory:
            if action_id not in TOOLS:
                raise RuntimeError(f"Unknown simulated tool {action_id} for {control_id}")
        result.append({
            "scenario_id": f"INC-{control_id.replace('.', '-')}-01",
            "control_id": control_id,
            "control_name": control["name"],
            "objective": control["objective"],
            "domain": "people" if control_id.startswith("A.6.") else ("hardware" if control_id.startswith("A.7.") else ("hardware" if control_id == "A.8.1" else "software")),
            "domain_label": {"people": "Con người", "hardware": "Phần cứng", "software": "Phần mềm"}["people" if control_id.startswith("A.6.") else ("hardware" if control_id.startswith("A.7.") else ("hardware" if control_id == "A.8.1" else "software"))],
            "title": title,
            "event": event,
            "department": department,
            "severity": "high" if control_id in {"A.6.5", "A.6.7", "A.7.5", "A.7.9", "A.7.10", "A.8.2", "A.8.4", "A.8.7", "A.8.12", "A.8.15", "A.8.20", "A.8.28", "A.8.33"} else "medium",
            "target": {"asset_id": target_id, "name": target_name, "type": target_type},
            # Human context is part of every enterprise case, even when the
            # affected object is a device or application. Annex A.6 cases name
            # the employee at the centre of the scenario; other cases identify
            # the synthetic departmental owner responsible for follow-up.
            "human_context": {
                "employee_id": (
                    target_id if target_type == "person" else
                    "EMP-017" if control_id == "A.6.7" else
                    "EMP-032" if control_id == "A.6.8" else
                    {"Nhân sự": "EMP-014", "Kinh doanh": "EMP-011", "Vận hành": "EMP-006",
                     "SOC": "EMP-032", "Hạ tầng": "EMP-025", "Hạ tầng CNTT": "EMP-025",
                     "An ninh cơ sở": "EMP-041", "Cơ sở vật chất": "EMP-044",
                     "Phát triển phần mềm": "EMP-038", "Vận hành dữ liệu": "EMP-019"}.get(department, "EMP-001")
                ),
                "department": department,
                "role": ("Nhân viên được xem xét" if target_type == "person" else
                         "Nhân viên báo cáo sự cố" if control_id == "A.6.7" else
                         "Điều phối viên SOC" if control_id == "A.6.8" else
                         {"Nhân sự": "Chuyên viên nhân sự", "Kinh doanh": "Nhân viên kinh doanh",
                          "Vận hành": "Nhân viên vận hành", "SOC": "Chuyên viên SOC",
                          "Hạ tầng": "Kỹ sư hạ tầng", "Hạ tầng CNTT": "Kỹ sư CNTT",
                          "An ninh cơ sở": "Nhân viên an ninh", "Cơ sở vật chất": "Kỹ thuật viên cơ sở",
                          "Phát triển phần mềm": "Kỹ sư phần mềm", "Vận hành dữ liệu": "Chuyên viên dữ liệu"}.get(department, "Nhân viên phụ trách")),
                "relationship": "affected_employee" if target_type == "person" or control_id == "A.6.7" else "responsible_employee",
                "is_synthetic": True,
            },
            "allowed_actions": allowed,
            "mandatory_actions": mandatory,
        })
    return result


SCENARIOS = load_scenarios()
SCENARIO_BY_ID = {item["scenario_id"]: item for item in SCENARIOS}
SCENARIO_BY_CONTROL = {item["control_id"]: item for item in SCENARIOS}
