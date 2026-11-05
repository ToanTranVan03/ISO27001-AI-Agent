import { employeeStatus } from "./officeLive";

export default function OfficeRoster({ employees, workspace, selectedEmployee, onSelect }) {
  const machines=Object.fromEntries(workspace.map(item=>[item.employee_id,item]));
  return <section className="mb-3 rounded-2xl border border-emerald-200/20 bg-[#203c38] p-4 text-emerald-50" aria-label="Nhân vật trong văn phòng">
    <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm font-black">VĂN PHÒNG CHUNG · {employees.length} nhân vật</h2><span className="text-xs">{workspace.filter(x=>x.state.shift==="on").length} trong ca · {workspace.length} máy riêng</span></div>
    <p className="mt-1 text-xs leading-5 text-emerald-100/70">Mỗi bình luận điều khiển một người. Chọn nhân vật → gõ “đi làm”, “nghỉ”, “cắm USB lạ”… → gửi. Những người còn lại tiếp tục hoạt động riêng.</p>
    <div className="mt-3 flex max-h-36 flex-wrap gap-2 overflow-y-auto">{employees.map(person=><button key={person.employee_id} onClick={()=>onSelect(person.employee_id)} aria-pressed={selectedEmployee===person.employee_id} title={`${person.display_name} · ${employeeStatus(machines[person.employee_id])}`} className={`rounded-lg border px-3 py-2 text-left text-[10px] ${selectedEmployee===person.employee_id?"border-emerald-100 bg-emerald-100 text-emerald-950":"border-white/15 hover:bg-white/10"}`}><b>{person.employee_id}</b><span className="mt-1 block opacity-75">{employeeStatus(machines[person.employee_id])}</span></button>)}</div>
  </section>;
}
