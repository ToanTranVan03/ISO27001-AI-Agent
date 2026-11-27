import {ShieldCheck} from 'lucide-react';

import {conclusionLabels} from './assessmentLabels';
export function StatusBadge({status,label}){
 const tone={Compliant:'success','Partially Compliant':'warning','Non-Compliant':'danger','Insufficient Evidence':'info',running:'active',RUNNING:'active',stale:'warning',failed:'danger'}[status]||'neutral';
 return <span className={`status-badge status-${tone}`}><span className="status-dot"/>{label||conclusionLabels[status]||status||'Chưa đánh giá'}</span>;
}
export function PageHeader({step,title,description,children}){
 return <header className="page-heading"><div><p className="page-eyebrow"><ShieldCheck size={14}/>ISO 27001 · {step}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{children&&<div className="page-heading-actions">{children}</div>}</header>;
}
const workflow = {
 company: {
  check: 'Xác định đối tượng trong phạm vi: nhân viên, tài khoản, thiết bị và hệ thống.',
  owner: 'Doanh nghiệp khai báo danh mục và cung cấp hồ sơ gốc.',
  next: 'Qua Tổng quan 56 control để mở tiêu chí và thu bằng chứng cho đối tượng cần đánh giá.',
 },
 scope: {
  check: 'Mở một control để xem tiêu chí, kết luận hiện tại và nguồn còn thiếu.',
  owner: 'Agent đọc nguồn đã lưu. Chuyên viên thẩm định và duyệt công việc khắc phục.',
  next: 'Dùng Tư vấn & khắc phục để giao việc, hoặc mở hồ sơ control để nộp nguồn và thẩm định.',
 },
 study: {
  check: 'Chọn nguồn và lượt thử để đánh giá 18 control kỹ thuật A.8.',
  owner: 'Agent kết luận trên bằng chứng lab. Người chấm đọc nguồn và nộp nhãn độc lập.',
  next: 'Đối chiếu theo từng control. Dùng Hồ sơ ISO để xem tiến độ và quyết định của đợt chính.',
 },
 dossier: {
  check: 'Theo dõi điều đã đánh giá, bằng chứng còn thiếu và hồ sơ chờ xác nhận.',
  owner: 'Người phụ trách kiểm tra căn cứ và thẩm định trước khi trình duyệt SoA.',
  next: 'Mở control còn thiếu để bổ sung bằng chứng hoặc kiểm tra lại, rồi xuất hồ sơ theo trạng thái hiện tại.',
 },
};

export function WorkflowGuide({screen}){
 const info=workflow[screen];
 return <dl className="workflow-guide" aria-label="Hướng dẫn màn hình">
  {[['Đang làm gì',info.check],['Ai thực hiện',info.owner],['Bước tiếp theo',info.next]].map(([label,value])=><div key={label}>
   <dt>{label}</dt><dd>{value}</dd>
  </div>)}
 </dl>;
}
