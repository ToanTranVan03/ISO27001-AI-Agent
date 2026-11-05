export const ROUTINE_EVENTS = new Set([
  "approved_work_session", "employee_shift_started", "approved_break_started", "screen_locked_by_employee",
  "employee_left_locked", "employee_returned_to_locked_device", "workstation_reopened_after_review",
  "usb_removed_by_employee", "software_removed_by_employee", "employee_shift_ended",
]);

export function latestByEmployee(entries) {
  const result = {};
  for (const entry of entries) {
    if (!result[entry.employee_id] || Date.parse(entry.observed_at) > Date.parse(result[entry.employee_id].observed_at)) {
      result[entry.employee_id] = entry;
    }
  }
  return result;
}

export function commandPhase(entry) {
  if (!entry) return "idle";
  if (entry.incident_id) return entry.verified ? "resolved" : "review";
  return ROUTINE_EVENTS.has(entry.event_type) ? "routine" : "pending";
}

export function commandRecipient(text, selected) {
  return text.trim().match(/^@?(EMP-\d{3})\s+/i)?.[1].toUpperCase() || selected;
}

export function employeePosition(index, entry, state) {
  if (state?.location === "reception") return [348+(index%7)*77,640+Math.floor(index/7)*45];
  if (state?.location === "break" || (!state && (entry?.command === "/nghi" || entry?.command === "/roi-may"))) {
    return [680 + (index % 7) * 38, 480 + (Math.floor(index / 7) % 2) * 65];
  }
  return [111 + (index % 4) * 127, 174 + Math.floor(index / 4) * 118];
}

export function employeePhase(entry, workstation) {
  if (workstation?.pending_count > 0) return "pending";
  const state=workstation?.state;
  if(state && (state.media_status==="unregistered" || state.software_status==="unapproved" || (state.location!=="desk" && state.screen_state==="unlocked"))) return "review";
  return commandPhase(entry);
}
