# Dàn ý thuyết trình — phiên bản theo bằng chứng hiện tại

## 1. Bài toán
AI Agent hỗ trợ đánh giá tuân thủ ATTT theo ISO/IEC 27001:2022; dữ liệu doanh nghiệp giả lập, chưa chứng nhận ISO.

## 2. Phạm vi
A.6.1–A.6.8 ở mô phỏng con người; collector lab và sự kiện văn phòng có phạm vi riêng. Xem PHAM_VI_DANH_GIA.md. Chưa đánh giá toàn bộ ISMS.

## 3. Bằng chứng
Nguồn, thời điểm, revision, hash và dấu vết đánh giá. Thiếu hoặc mâu thuẫn nguồn phải được thể hiện, không bịa dữ kiện.

## 4. Kiến trúc
React → FastAPI → PostgreSQL; Ollama lập kế hoạch với công cụ giới hạn. Bốn vai trò dùng chung bộ điều phối, chưa phải bốn LLM độc lập.

## 5. Phân định AI và luật
Luật/rubric đánh giá; workflow cố định; LLM lựa chọn công cụ. Kho tri thức hiện truy hồi từ khóa trên dữ liệu viết sẵn. Công thức điểm rủi ro là mô hình dự án.

## 6. Trình diễn
Chọn nhân viên → giao SOC → xem kết quả thực thi → mở hồ sơ sự cố → chuyển Hồ sơ ISO → xem căn cứ và chạy/tái đánh giá kiểm soát.

## 7. Hồ sơ và người duyệt
Kết luận kiểm soát tách trạng thái xử lý sự cố. Xem lịch sử, bằng chứng và audit trail; duyệt theo quyền hiện có. Không gọi COMPLETED là chứng nhận.

## 8. Benchmark thực tế
Ngày 06/11/2026: 8 ca chung, một lần lặp mỗi chế độ. Luật/workflow/LLM đều khớp 8/8; luật/workflow nhanh hơn. Xem KIEM_CHUNG_DANH_GIA.md và JSON gốc. Không suy độ chính xác tổng quát.

## 9. Lỗi và fallback
8 ca fault injection model: giữ lỗi AI, chạy phục hồi workflow có nhãn riêng. Không tính phục hồi là model thành công; không suy tỷ lệ lỗi vận hành.

## 10. Giới hạn và hướng tiếp
Chưa thẩm định chuyên gia, chưa khảo sát người thật, chưa có SoA được duyệt, chưa kiểm định dữ liệu doanh nghiệp thật. Ưu tiên chất lượng bằng chứng và kết luận trước hoạt ảnh.
