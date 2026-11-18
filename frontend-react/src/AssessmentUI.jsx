import {ShieldCheck,ArrowRight} from 'lucide-react';

import {conclusionLabels} from './assessmentLabels';
export function StatusBadge({status,label}){
 const tone={Compliant:'success','Partially Compliant':'warning','Non-Compliant':'danger','Insufficient Evidence':'info',running:'active',RUNNING:'active',stale:'warning',failed:'danger'}[status]||'neutral';
 return <span className={`status-badge status-${tone}`}><span className="status-dot"/>{label||conclusionLabels[status]||status||'Chưa đánh giá'}</span>;
}
export function PageHeader({step,title,description,children}){
 return <header className="page-heading"><div><p className="page-eyebrow"><ShieldCheck size={14}/>ISO 27001 · {step}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{children&&<div className="page-heading-actions">{children}</div>}</header>;
}
export function WorkflowGuide({current}){
 return <div className="workflow-guide" aria-label="Các bước đánh giá">{['Doanh nghiệp','Bằng chứng & kiểm tra','Thẩm định','Báo cáo SoA'].map((label,i)=><span key={label} className={i===current?'workflow-current':''}><b>0{i+1}</b>{label}{i<3&&<ArrowRight size={12}/>}</span>)}</div>;
}
