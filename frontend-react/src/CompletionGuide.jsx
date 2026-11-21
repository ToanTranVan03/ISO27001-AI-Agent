import {buildCompletionGuide} from './completionGuide';

export default function CompletionGuide({scope,onSelect,exportFile}){
 const guide=buildCompletionGuide(scope);
 function markdown(){return ['# Hướng dẫn hoàn tất đợt đánh giá','',`Đợt: ${guide.assessment_id}`,`Rubric: ${guide.rubric_sha256}`,`SoA: ${guide.soa_fingerprint}`,
  '', 'Checklist hướng dẫn, không phải bằng chứng, phân công đã chấp nhận hoặc phê duyệt.',
  ...guide.steps.flatMap((s,i)=>['',`## ${i+1}. ${s.title}`,`Vai trò thực hiện: ${s.actor}`,s.summary,s.action,`Điều kiện kiểm tra: ${s.completion}`,`Control cần mở: ${s.controls.join(', ')||'Rà hồ sơ toàn đợt / nghiên cứu riêng'}`])].join('\n');}
 return <details className="rounded-2xl border border-teal-700 bg-teal-950/20 p-5"><summary className="cursor-pointer font-semibold">Cần làm gì để hoàn tất? · Hướng dẫn theo hồ sơ hiện tại</summary>
  <p className="my-3 text-sm text-slate-300">Thực hiện theo thứ tự dưới đây. Nguồn có thể là cấu hình/log của doanh nghiệp lab đúng phạm vi đã thống nhất; không bắt buộc nguồn production. Công cụ không xác nhận chuyên môn hoặc chấm thay thành viên.</p>
  <div className="flex flex-wrap gap-2"><button className="rounded border border-slate-600 p-2 text-sm" onClick={()=>exportFile(guide,'huong-dan-hoan-tat.json')}>Xuất hướng dẫn JSON</button><button className="rounded border border-slate-600 p-2 text-sm" onClick={()=>exportFile(markdown(),'huong-dan-hoan-tat.md','text/markdown;charset=utf-8')}>Xuất hướng dẫn Markdown</button></div>
  <ol className="mt-4 grid gap-4 lg:grid-cols-2">{guide.steps.map((s,i)=><li key={s.id} className="space-y-2 rounded-xl border border-slate-700 bg-slate-900 p-4"><h3 className="font-semibold text-teal-200">{i+1}. {s.title}</h3><p className="text-xs text-slate-400">{s.actor}</p><p className="text-sm">{s.summary}</p><p className="text-sm text-slate-300">{s.action}</p><details><summary className="text-xs text-teal-200">Khi nào đủ điều kiện?</summary><p className="mt-2 text-xs leading-6">{s.completion}</p></details><div className="flex max-h-28 flex-wrap gap-2 overflow-auto">{s.controls.map(id=><button key={id} onClick={()=>onSelect(id)} className="rounded bg-slate-800 px-2 py-1 text-xs text-teal-200">{id}</button>)}</div></li>)}</ol>
 </details>;
}
