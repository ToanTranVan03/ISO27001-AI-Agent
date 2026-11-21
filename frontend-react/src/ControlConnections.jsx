import {controlRunIds} from './navigation';

export default function ControlConnections({control,employeeId,onOpenDashboard,onOpenDossier,onOpenCompany,onOpenA8}){
 const context={controlId:control.control_id,employeeId:employeeId||''};
 const runs=controlRunIds(control);
 return <section className="space-y-3 rounded-xl border border-teal-800 bg-teal-950/20 p-4"><h3 className="text-sm font-semibold text-teal-200">Liên kết hồ sơ · {control.control_id}</h3>
  <div className="flex flex-wrap gap-2">{onOpenDashboard&&<button className="rounded border border-slate-600 p-2 text-xs" onClick={()=>onOpenDashboard(context)}>Tổng quan · {control.control_id}</button>}{onOpenDossier&&<button className="rounded border border-slate-600 p-2 text-xs" onClick={()=>onOpenDossier(context)}>Hồ sơ ISO · {control.control_id}</button>}{onOpenCompany&&<button className="rounded border border-slate-600 p-2 text-xs" onClick={()=>onOpenCompany(context)}>{employeeId?`Doanh nghiệp · ${employeeId}`:'Doanh nghiệp liên quan'}</button>}
   {onOpenA8&&runs.map(id=><button key={id} className="rounded border border-slate-600 p-2 text-xs" onClick={()=>onOpenA8({...context,runId:id})}>Mở lượt A.8 {id.slice(0,8)} · {control.control_id}</button>)}</div>
  <p className="text-[11px] text-slate-400">Cùng đợt và control. Lượt A.8 vẫn được kiểm tra quyền/chấm mù; chuyển màn hình không tự chạy Agent hoặc phê duyệt.</p>
 </section>;
}
