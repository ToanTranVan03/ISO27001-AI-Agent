// Guidance derived from existing gates; never evidence, decisions or approvals.
export function buildCompletionGuide(scope) {
 const rows=scope.controls;
 const missing=rows.filter(c=>!c.explicit_source_count&&c.applicability?.applicable!==false);
 const unusable=rows.filter(c=>c.explicit_source_count&&!c.usable_source_count&&c.applicability?.applicable!==false);
 const tasks=scope.acceptance_worklist.tasks;
 const ids=stage=>[...new Set(tasks.filter(t=>t.stage===stage&&t.control_id).map(t=>t.control_id))];
 return {
  assessment_id:scope.assessment_id,rubric_sha256:scope.rubric_sha256,soa_fingerprint:scope.soa.fingerprint,
  meaning:'GUIDANCE_ONLY_NOT_EVIDENCE_OR_APPROVAL',
  steps:[
   {id:'rubric',title:'Chốt tiêu chí và người đánh giá',actor:'Người phụ trách / giảng viên',controls:[],
    pending:!scope.rubric_approval,summary:scope.rubric_approval?'Đã lưu xác nhận rubric; tư cách người chấm/phương pháp cần đối chiếu biên bản riêng.':'Chưa xác nhận rubric hiện hành.',
    action:'Rà tiêu chí, loại nguồn và giới hạn kiểm tra. Thống nhất người chấm/phương pháp với thầy; admin ghi căn cứ tại Tiêu chí toàn phạm vi 56.',
    completion:'Có xác nhận đúng phiên bản rubric và biên bản thống nhất phương pháp/người chấm; không tự suy ra từ tài khoản.'},
   {id:'sources',title:'Bổ sung nguồn còn thiếu / không dùng được',actor:'Chủ hồ sơ HR, hành chính và IT',controls:[...missing,...unusable].map(c=>c.control_id),
    pending:!!(missing.length+unusable.length),summary:`${missing.length} control thiếu nguồn; ${unusable.length} cần thay nguồn không dùng được.`,
    action:'Mở từng control, đọc tiêu chí và loại bằng chứng; nộp bản gốc có nội dung, ghi xuất xứ, kỳ quan sát và giới hạn. Rà mức bao phủ cả nguồn đã có.',
    completion:'Nguồn đọc được, đúng đối tượng/kỳ kiểm tra và được người phụ trách chấp nhận; số tệp hoặc hash không chứng minh đủ nội dung.'},
   {id:'evaluation',title:'Agent đánh giá nguồn hiện hành',actor:'Admin điều phối Agent',controls:ids('evaluation'),
    pending:!!ids('evaluation').length,summary:`${ids('evaluation').length} control có nguồn nhưng còn cần đánh giá theo danh sách công việc.`,
    action:'Sau khi thu nguồn, chọn Agent đánh giá hồ sơ đã thu hoặc chạy lô ở Hồ sơ ISO. Kiểm tra lỗi/viện dẫn; giữ lịch sử và không chạy preset để thay nguồn thiếu.',
    completion:'Có kết quả hiện hành hoặc lỗi được ghi nhận rõ; chạy xong không đồng nghĩa đạt control.'},
   {id:'research',title:'Chốt bộ kiểm định và tổ chức chấm',actor:'Người cung cấp bộ mới / Khoa, Tú nếu được chấp nhận',controls:[],pending:null,
    summary:'Cần xác minh bằng hồ sơ nghiên cứu riêng; bảng 56 không tự xác nhận tính độc lập.',
    action:'Chuẩn bị nguồn lab mới chưa dùng chỉnh code/prompt; chốt snapshot và đáp án thiết kế riêng trước dự đoán. Admin tạo lượt; Khoa/Tú tự đọc cùng run ID và khai đúng mức hỗ trợ/tiếp xúc.',
    completion:'Có hồ sơ tập mới và nhãn người chấm phù hợp. Giữ nhãn cũ có hỗ trợ; ghi bất đồng tại sổ riêng, không sửa nhãn khóa.'},
   {id:'review',title:'Thẩm định từng tiêu chí',actor:'Người đánh giá được phân công',controls:ids('review'),
    pending:!!ids('review').length,summary:`${ids('review').length} control còn cần thẩm định hiện hành.`,
    action:'Đọc nguồn gốc, chọn đạt/không đạt/chưa rõ từng tiêu chí và viện dẫn đúng nguồn; kết luận tổng khớp rubric. Đây là thẩm định hồ sơ, khác chấm mù A.8.',
    completion:'Có thẩm định gắn review token hiện hành; thiếu nguồn giữ chưa rõ, không chọn đạt để đóng tiến độ.'},
   {id:'decisions',title:'Ghi tính áp dụng và kế hoạch xử lý',actor:'Người phụ trách admin',controls:[...new Set([...ids('applicability'),...ids('treatment')])],
    pending:!!(ids('applicability').length+ids('treatment').length),summary:`${ids('applicability').length} quyết định chưa ghi; ${ids('treatment').length} kế hoạch cần bổ sung.`,
    action:'Với từng control, quyết định áp dụng/loại trừ có lý do. Nếu áp dụng, ghi xử lý/duy trì, người nhận thực tế, hạn và cách kiểm tra lại. Được lưu nháp nhưng chưa đủ điều kiện duyệt.',
    completion:'Quyết định có căn cứ và kế hoạch theo gate hiện hành; không tự gán người, hạn hoặc loại trừ chỉ vì chưa thu được nguồn.'},
   {id:'approval',title:'Rà và trình duyệt SoA',actor:'Người có trách nhiệm phê duyệt',controls:scope.soa.pending_controls,
    pending:!scope.acceptance.soa_approved,summary:scope.soa.approval,
    action:'Mở bảng điều kiện SoA, xử lý từng blocker và xác nhận rubric. Người có trách nhiệm đọc bản xuất, kiểm tra fingerprint rồi quyết định duyệt khi đủ điều kiện.',
    completion:'Phê duyệt hiện hành được lưu; không đồng nghĩa mọi control đạt hoặc doanh nghiệp được chứng nhận ISO.'}
  ]
 };
}
