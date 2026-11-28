import {useEffect,useState} from 'react';

const screens=[['company','Doanh nghiệp'],['scope56','Tổng quan 56 control'],['a8','Thực nghiệm A.8'],['dossier','Hồ sơ ISO']];

export function CaptureFindings({assessmentId,request,runId,reportHash,controlId,onOpen}){
 const [matches,setMatches]=useState(null);
 const key=[assessmentId,runId,reportHash,controlId].join(':');
 useEffect(()=>{
  let active=true;
  request(`/api/assessments/${assessmentId}/remediation`).then(board=>{
   if(active)setMatches({key,rows:board.records.filter(({kind,document})=>kind==='finding'&&
    document.control_id===controlId&&document.a8_capture?.run_id===runId&&document.a8_capture.report_sha256===reportHash)});
  }).catch(()=>{if(active)setMatches({key,rows:[]});});
  return()=>{active=false;};
 },[assessmentId,request,runId,reportHash,controlId,key]);
 if(matches?.key!==key||!matches.rows.length)return null;
 return <section aria-label="Phát hiện từ bản thu A.8" className="space-y-2">
  {matches.rows.map(({record_id,document})=><button key={record_id} className="block rounded border border-teal-700 p-2 text-left" onClick={()=>onOpen({controlId,runId,findingId:record_id})}>
   {document.description} · {record_id}
  </button>)}
 </section>;
}

export default function FindingContext({assessment,navigation,request,navigate}){
 const [loaded,setLoaded]=useState(null);
 const {findingId,controlId,view}=navigation;
 const aid=assessment.assessment_id;
 const key=aid+':'+findingId;
 useEffect(()=>{
  if(!findingId)return;
  let active=true;
  request(`/api/assessments/${aid}/remediation`).then(board=>{
   if(active)setLoaded({key,row:board.records.find(r=>r.kind==='finding'&&r.record_id===findingId)});
  }).catch(()=>{if(active)setLoaded({key,row:null});});
  return()=>{active=false;};
 },[aid,findingId,key,request,view]);
 if(!findingId)return null;
 if(loaded?.key!==key)return <p role="status" className="mx-auto mt-36 max-w-7xl px-5 text-sm text-slate-300">Đang kiểm tra liên kết phát hiện…</p>;
 const row=loaded.row;
 if(!row||row.document.control_id!==controlId)return <p role="status" className="mx-auto mt-36 max-w-7xl px-5 text-sm text-amber-200">Phát hiện không có trong hồ sơ được phép xem của đợt và control này.</p>;
 const target=row.document.software_target;
 const capture=row.document.a8_capture;
 return <aside aria-label="Phát hiện đang theo dõi" className="mx-auto mt-36 max-w-7xl space-y-2 border-l-2 border-teal-500 px-5 text-sm text-slate-200 lg:mt-28">
  <p><strong>Mã phát hiện:</strong> <span className="break-all">{row.record_id}</span></p>
  <p>{controlId} · {row.document.description}</p>
  {target&&<p>Đích: {target.system} · {target.application} · Nguồn đầu: {target.baseline_evidence_id}</p>}
  {capture&&<p className="break-all">Bản thu liên kết: {capture.evidence_id} · Đối tượng quan sát: {capture.asset_id} · Lượt: {capture.run_id}</p>}
  {view==='a8'&&!capture&&<p>Phát hiện này chưa gắn với bản thu của lượt Thực nghiệm A.8.</p>}
  {view==='a8'&&capture&&navigation.runId!==capture.run_id&&<button className="rounded border border-slate-600 px-2 py-1" onClick={()=>navigate({view:'a8',controlId,findingId,runId:capture.run_id})}>Mở lượt chứa bản thu</button>}
  <nav aria-label="Đi theo phát hiện" className="flex flex-wrap gap-2">
   {screens.filter(([id])=>id!==view).map(([id,label])=><button key={id} className="rounded border border-slate-600 px-2 py-1" onClick={()=>navigate({view:id,controlId,findingId,...(id==='a8'?{runId:capture?.run_id||''}:{})})}>{label} · phát hiện</button>)}
  </nav>
 </aside>;
}
