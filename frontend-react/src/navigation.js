const views=new Set(['scope56','a8','company','dossier']);
const uuid=/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i;
export function normalizeNavigation(input={}){
 const value=key=>typeof input[key]==='string'?input[key]:'';
 const cid=value('controlId'),parts=/^A\.([678])\.(\d{1,2})$/.exec(cid);
 const validControl=parts&&!parts[2].startsWith('0')&&Number(parts[2])>=1&&Number(parts[2])<=({'6':8,'7':14,'8':34}[parts[1]]);
 return {view:views.has(input.view)?input.view:'scope56',controlId:validControl?cid:'',
  employeeId:/^EMP-\d{3}$/.test(value('employeeId'))?value('employeeId'):'',
  ...(uuid.test(value('findingId'))?{findingId:value('findingId').toLowerCase()}:{}),
  runId:uuid.test(value('runId'))?value('runId').toLowerCase():'',
  assessmentId:uuid.test(value('assessmentId'))?value('assessmentId').toLowerCase():''};
}
export function readNavigation(hash=''){
 const params=new URLSearchParams(hash.replace(/^#/,''));
 return normalizeNavigation({view:params.get('view'),controlId:params.get('control'),employeeId:params.get('employee'),runId:params.get('run'),assessmentId:params.get('assessment'),findingId:params.get('finding')});
}
export function navigationHash(input){
 const n=normalizeNavigation(input),p=new URLSearchParams({view:n.view});
 for(const [key,field] of [['control','controlId'],['employee','employeeId'],['run','runId'],['assessment','assessmentId'],['finding','findingId']])if(n[field])p.set(key,n[field]);
 return '#'+p.toString();
}
export function mergeNavigation(current,patch){
 const update=typeof patch==='string'?{view:patch}:patch||{};
 const reset=update.assessmentId&&update.assessmentId!==current.assessmentId||update.controlId!==undefined&&update.controlId!==current.controlId;
 return normalizeNavigation({...current,...(reset?{findingId:''}:{}),...Object.fromEntries(Object.entries(update).filter(([,v])=>v!==undefined))});
}
export function sourceRunIds(control){
 return [...new Set((control?.evidence||[]).map(e=>{
  const match=/^a8-capture:\/\/([^/]+)\/(A\.[678]\.\d+)$/.exec(e.source||'');
  return match&&uuid.test(match[1])&&match[2]===control.control_id?match[1].toLowerCase():null;
 }).filter(Boolean))];
}
export function controlReferencesEmployee(control,id){
 return !!id&&(control.evidence||[]).some(e=>Array.isArray(e.entity_refs?.employees)&&e.entity_refs.employees.includes(id));
}
export function controlRunIds(control){
 return [...new Set([...sourceRunIds(control),...(control?.experiment_results||[]).map(r=>normalizeNavigation({runId:r.run_id}).runId).filter(Boolean)])];
}
