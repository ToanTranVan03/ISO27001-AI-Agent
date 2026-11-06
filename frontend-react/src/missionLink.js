export function employeeTarget(person,machine,eventId) {
  if(!person?.employee_id||!machine?.asset_id)return null;
  return {employee_id:person.employee_id,employee_name:person.display_name,asset_id:machine.asset_id,...(eventId?{event_id:eventId}:{})};
}

export function missionLiveFocus(mission,monitor) {
  const activity=mission?.current_activity;
  if(mission?.status==="running"&&activity?.active){
    return {...activity,source:"mission",text:activity.employee_id?`Agent SOC ${activity.state==="processing"?"đang xử lý":"đang kiểm tra"} ${activity.employee_id} · ${activity.asset_id}`:"Agent SOC đang quét dữ liệu toàn doanh nghiệp"};
  }
  if(monitor?.state==="processing"&&monitor.current_finding?.employee_id){
    const finding=monitor.current_finding;
    return {...finding,active:true,source:"monitor",state:"processing",text:`Giám sát tự động đang xử lý ${finding.employee_id} · ${finding.asset_id}`};
  }
  return null;
}

export function linkedRecord(report,findings=[]) {
  const finding=findings.find(item=>item.event_id===report.event_id)||{};
  return {...finding,...report,employee_id:report.employee_id||finding.employee_id,asset_id:report.asset_id||finding.asset_id,
    event_id:report.event_id||finding.event_id,incident_id:report.incident_id};
}

export function refreshLinkedRecord(record,entries=[],missions=[]) {
  if(!record)return null;
  const matches=item=>item.employee_id===record.employee_id&&item.asset_id===record.asset_id&&(!record.event_id||item.event_id===record.event_id);
  const receipt=entries.find(matches);
  const reports=missions.filter(Boolean).flatMap(mission=>{
    const security=mission.tasks?.find(task=>task.id==="security")?.output;
    return [...(security?.reports||[]),...(security?.previously_processed||[])];
  });
  const result=reports.find(matches);
  return {...record,...(receipt||{}),...(result||{})};
}
