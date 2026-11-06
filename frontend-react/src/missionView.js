export const ROLES=[
  {id:"coordination",name:"Điều phối",agent:"Agent điều phối",color:"#53b9cf",job:"Lập kế hoạch · chia việc",scope:"all",preset:"Kiểm tra dấu hiệu vi phạm trong doanh nghiệp và lập hồ sơ bàn giao"},
  {id:"inventory",name:"Tài sản & nhân sự",agent:"Agent tài sản",color:"#d9a256",job:"Đọc danh mục · kiểm tra máy",scope:"hardware",preset:"Đối chiếu danh mục và trạng thái máy nhân viên, kiểm tra dấu hiệu còn mở"},
  {id:"security",name:"SOC · ứng phó",agent:"Agent SOC",color:"#9c87db",job:"Quét · xử lý · xác minh",scope:"hardware",preset:"Kiểm tra USB lạ và trạng thái máy nhân viên, xử lý và xác minh dấu hiệu"},
  {id:"report",name:"Kiểm soát nội bộ",agent:"Agent kiểm soát",color:"#59b895",job:"Đối chiếu đầu ra · lập hồ sơ",scope:"all",preset:"Rà soát sự cố còn mở và kết quả xác minh, chuẩn bị hồ sơ để người phụ trách duyệt"},
];
export const TOOL_LABELS={coordination:"Lập kế hoạch và chia việc",inventory:"Thu thập danh mục",workstations:"Kiểm tra trạng thái máy",security:"Quét, xử lý và xác minh",report:"Lập hồ sơ bàn giao"};
export const STATUS_LABELS={idle:"Sẵn sàng",waiting:"Chờ bàn giao",running:"Đang làm việc",completed:"Đã bàn giao",blocked:"Bị chặn",failed:"Gặp lỗi",queued:"Đã nhận yêu cầu",awaiting_review:"Chờ bạn duyệt",approved:"Đã duyệt hồ sơ",revision_requested:"Cần bổ sung",interrupted:"Bị gián đoạn"};
export const roleForTool=tool=>tool==="workstations"?"inventory":ROLES.some(role=>role.id===tool)?tool:"coordination";

export function subtasksOf(mission) {
  if(!mission)return [];
  if(mission.subtasks?.length)return mission.subtasks;
  return (mission.tasks||[]).map((task,index)=>({...task,id:`${mission.mission_id}:${task.id}`,tool:task.id,role:task.id,output_ref:task.output?`tasks.${index}.output`:null}));
}

export function outputOf(mission,task) {
  const ref=task?.output_ref;
  const phase=ref?.match(/^tasks\.([0-3])\.output$/);
  if(phase)return mission?.tasks?.[Number(phase[1])]?.output;
  const diagnostic=ref?.match(/^diagnostics\.(\d+)$/);
  if(diagnostic)return mission?.diagnostics?.[Number(diagnostic[1])];
  return undefined;
}

export function roleStatus(mission,role) {
  if(!mission)return "idle";
  const jobs=subtasksOf(mission).filter(task=>task.role===role);
  if(jobs.some(task=>task.status==="running"))return "running";
  if(role==="report"&&["awaiting_review","approved","revision_requested"].includes(mission.status))return mission.status;
  if(jobs.length&&jobs.every(task=>task.status==="completed"))return "completed";
  if(jobs.some(task=>task.status==="failed"))return "failed";
  if(jobs.some(task=>task.status==="blocked")||["blocked","failed","interrupted"].includes(mission.status))return "blocked";
  return "waiting";
}

export function messagesOf(mission) {
  if(mission?.agent_messages?.length)return mission.agent_messages;
  return (mission?.trace||[]).map((event,index)=>({...event,id:`legacy:${index}`,role:roleForTool(event.tool),source:"legacy_trace",kind:event.kind}));
}

export function activeRole(mission) {
  return subtasksOf(mission).find(task=>task.status==="running")?.role||null;
}

export function roleFeedback(mission,role) {
  const messages=messagesOf(mission).filter(message=>message.role===role);
  if(messages.length)return messages.at(-1).text;
  const task=subtasksOf(mission).find(task=>task.role===role&&task.summary);
  if(task)return task.summary;
  const state=roleStatus(mission,role);
  return state==="idle"?"Chọn vai trò để xem hoặc giao yêu cầu mới.":state==="blocked"?"Đang chờ xử lý bước bị chặn; chưa có kết quả mới.":state==="completed"?"Đã lưu đầu ra của vai trò này.":"Đang chờ công việc từ điều phối.";
}

export function sourceForRole(mission,role) {
  if(role==="coordination"){
    const plan=mission?.tasks?.find(task=>task.id==="coordination")?.output;
    return plan?(plan.model||"Quy trình điều phối"):"Chưa có kết quả lập kế hoạch";
  }
  if(role==="security"){
    const data=mission?.tasks?.find(task=>task.id==="security")?.output;
    const records=[...(data?.reports||[]),...(data?.previously_processed||[])];
    const sources=[...new Set(records.map(item=>item.model).filter(Boolean))];
    return sources.length?`${!data?.reports?.length&&data?.previously_processed?.length?"Hồ sơ đã xử lý · ":""}${sources.map(source=>source==="policy-fallback"?"Quy tắc dự phòng":source).join(", ")}`:"Chưa có kết quả ứng phó";
  }
  return "Công cụ nghiệp vụ";
}
