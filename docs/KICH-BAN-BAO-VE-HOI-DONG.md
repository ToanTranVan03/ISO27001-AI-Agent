# Kịch bản bảo vệ theo trạng thái triển khai

## Trình diễn 7 phút

1. (1 phút) Nêu bài toán, phạm vi giả lập và giới hạn: hỗ trợ đánh giá, không cấp chứng nhận ISO.
2. (1 phút) Giải thích nguồn bằng chứng, tiêu chí lab và ba trạng thái kết luận.
3. (2 phút) Chọn nhân viên, phát sinh sự kiện, giao SOC kiểm tra; cho thấy đúng người/máy, hành động và kết quả xác minh thực.
4. (1 phút) Mở Hồ sơ ISO: xem bằng chứng, rationale, audit trail, lịch sử; chỉ ra xử lý sự cố không tự làm kiểm soát tuân thủ.
5. (1 phút) Trình bày benchmark thật và tách nguồn luật/LLM/fault injection.
6. (1 phút) Nêu giới hạn và kế hoạch kiểm định độc lập.

## Câu hỏi phản biện

**Đây có phải bốn Agent độc lập?** Bốn vai trò dùng chung bộ điều phối có giới hạn. Không khẳng định bốn mô hình tự thảo luận.

**LLM có tốt hơn luật?** Chưa chứng minh. Trong 8 ca chung hiện tại cùng evaluator, ba chế độ cùng nhãn; LLM chậm hơn. Vai trò LLM hiện ở chọn công cụ và lập kế hoạch.

**Công thức rủi ro có do ISO quy định?** Không. Đó là rubric của đồ án và trọng số do dự án lựa chọn, cần thẩm định.

**RAG có dùng vector?** Chưa. Module hiện truy hồi từ khóa trên kho diễn giải viết sẵn.

**Có khảo sát UX thật chưa?** Chưa có dữ liệu người tham gia được xác minh. Script random chỉ minh họa, không trích SUS hoặc p-value thành thành tích.

**Đã đáp ứng toàn ISO?** Chưa. Phạm vi là một số kiểm soát và tiêu chí mô phỏng. Cần SoA, nguồn chuẩn có phiên bản, thẩm định và kiểm định thực tế.

Nguồn minh chứng: PHAM_VI_DANH_GIA.md, KIEM_CHUNG_DANH_GIA.md, BAO-VE-VA-KHAO-SAT.md.
