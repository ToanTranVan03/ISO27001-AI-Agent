"""Pure state transitions for the shared, fictional employee workstation."""
DEFAULT_STATE = {
    "shift": "off", "location": "reception", "screen_state": "locked",
    "usb_connected": False, "media_status": "clear", "software_status": "approved",
    "device_status": "available", "network_isolated": False, "revision": 0,
}
RISK_EVENTS = {"unattended_screen_unlocked", "unapproved_usb_inserted", "unapproved_software_installed"}


def preparation_steps(command, current, pending=0):
    """Validate an explicitly requested approach-to-workstation sequence first.

    No unlock/isolation bypass: each actual step still passes transition().
    Unknown commands must already have been rejected by the command parser.
    """
    state={**DEFAULT_STATE,**current}
    steps=[]
    if command in {'/usb-la','/cai-app-la','/roi-may'}:
        if state['network_isolated'] or state['device_status']=='locked' or state.get('returned') or pending:
            raise ValueError('Máy đang bị bảo vệ hoặc có sự kiện chưa xử lý; không tự mở khóa để thực hiện lệnh.')
        if state['shift']=='off':steps.append('/di-lam')
        elif state['location']!='desk' or state['screen_state']!='unlocked':steps.append('/lam-viec')
    for step in steps:
        state,_=transition(step,state,pending)
    transition(command,state,pending)
    return steps


def transition(command, current, pending=0):
    state = {**DEFAULT_STATE, **current}
    if state.get('returned') is True and command in {'/di-lam','/vao-ca','/lam-viec','/usb-la','/cai-app-la','/mo-khoa'}:
        raise ValueError('Thiết bị đã được thu hồi; cần phân công lại trước khi sử dụng.')
    after = dict(state)
    if command == "/di-lam":
        if state["shift"] == "on":
            raise ValueError("Nhân viên đã tham gia ca. Dùng /lam-viec để quay lại bàn.")
        blocked = state["device_status"] == "locked" or state["network_isolated"] or pending or state["media_status"] == "unregistered" or state["software_status"] == "unapproved"
        after.update(shift="on", location="desk", screen_state="locked" if blocked else "unlocked")
        event = "employee_returned_to_locked_device" if blocked else "approved_work_session"
    elif command == "/vao-ca":
        if state["shift"] == "on":
            raise ValueError("Nhân viên đã vào ca. Dùng /lam-viec để quay lại bàn.")
        after.update(shift="on", location="desk", screen_state="locked")
        event = "employee_shift_started"
    else:
        if state["shift"] != "on":
            raise ValueError("Nhân viên chưa vào ca. Hãy gửi /vao-ca trước.")
        if command == "/lam-viec":
            # Returning to the desk is permitted, but does not bypass containment.
            after["location"] = "desk"
            blocked = state["device_status"] == "locked" or state["network_isolated"]
            after["screen_state"] = "locked" if blocked else "unlocked"
            event = "employee_returned_to_locked_device" if blocked else "approved_work_session"
        elif command in {"/nghi", "/roi-may", "/khoa-may", "/usb-la", "/rut-usb", "/cai-app-la", "/go-app", "/mo-khoa"}:
            if state["location"] != "desk":
                raise ValueError("Nhân viên đang ở ngoài bàn. Dùng /lam-viec để quay lại trước.")
            if command == "/nghi":
                after.update(location="break", screen_state="locked")
                event = "approved_break_started"
            elif command == "/roi-may":
                after["location"] = "break"
                event = "unattended_screen_unlocked" if state["screen_state"] == "unlocked" else "employee_left_locked"
            elif command == "/khoa-may":
                if state["screen_state"] == "locked":
                    raise ValueError("Màn hình đã khóa; không tạo thêm hành động trùng.")
                after["screen_state"] = "locked"
                event = "screen_locked_by_employee"
            elif command == "/mo-khoa":
                if pending or state["media_status"] == "unregistered" or state["software_status"] == "unapproved":
                    raise ValueError("Chưa thể mở lại máy khi còn dấu hiệu hoặc sự kiện chưa được Agent xử lý.")
                if state["screen_state"] != "locked" and not state["network_isolated"]:
                    raise ValueError("Máy đã sẵn sàng sử dụng.")
                after.update(screen_state="unlocked", device_status="available", network_isolated=False)
                event = "workstation_reopened_after_review"
            elif command == "/rut-usb":
                if not state["usb_connected"]:
                    raise ValueError("Không có USB đang kết nối.")
                after.update(usb_connected=False, media_status="removed")
                event = "usb_removed_by_employee"
            elif command == "/go-app":
                if state["software_status"] not in {"unapproved", "blocked"}:
                    raise ValueError("Không có ứng dụng lạ cần gỡ.")
                after["software_status"] = "removed"
                event = "software_removed_by_employee"
            else:
                if state["screen_state"] != "unlocked" or state["device_status"] == "locked" or state["network_isolated"]:
                    raise ValueError("Máy đang khóa hoặc bị cô lập. Quay lại bàn và chờ Agent xử lý trước khi mở máy.")
                if command == "/usb-la":
                    if state["usb_connected"]:
                        raise ValueError("USB vẫn đang cắm. Rút USB trước khi tạo lần kết nối mới.")
                    after.update(usb_connected=True, media_status="unregistered")
                    event = "unapproved_usb_inserted"
                else:
                    if state["software_status"] in {"unapproved", "blocked"}:
                        raise ValueError("Ứng dụng này vẫn còn trên máy. Gỡ ứng dụng trước khi cài lại.")
                    after["software_status"] = "unapproved"
                    event = "unapproved_software_installed"
        elif command == "/tan-ca":
            if state["screen_state"] != "locked" or state["usb_connected"] or state["software_status"] == "unapproved" or pending:
                raise ValueError("Trước khi tan ca: khóa máy, rút USB, xử lý ứng dụng lạ và chờ Agent hoàn tất sự kiện còn mở.")
            after.update(shift="off", location="reception")
            event = "employee_shift_ended"
        else:
            raise ValueError("Lệnh chưa được hỗ trợ.")
    after["revision"] = state["revision"] + 1
    return after, event


def lock_key(assessment_id, employee_id):
    return f"office:{assessment_id}:{employee_id}"
