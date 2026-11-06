# HiveFive — AI Agent hỗ trợ đánh giá tuân thủ ISO/IEC 27001:2022

Hệ thống hỗ trợ thu thập bằng chứng, đánh giá một số kiểm soát, theo dõi khắc phục và lập hồ sơ chờ người phụ trách duyệt trong doanh nghiệp giả lập. Không phải chứng nhận ISO hoặc kết luận toàn doanh nghiệp tuân thủ.

## Phạm vi và kiến trúc

- Mô phỏng A.6.1–A.6.8; collector Enterprise Lab và văn phòng tương tác có phạm vi riêng: [ma trận phạm vi](docs/PHAM_VI_DANH_GIA.md).
- LLM Ollama lập kế hoạch với công cụ giới hạn. Bốn phòng là bốn vai trò dùng chung điều phối, chưa phải bốn LLM độc lập.
- Luật đánh giá, workflow và fallback phải được phân biệt. PostgreSQL lưu hồ sơ; React hiển thị thực thi.
- `iso_rag.py` hiện truy hồi từ khóa trên kho kiến thức viết sẵn, chưa phải vector RAG.
- Ngưỡng thời gian và công thức rủi ro lab là chính sách dự án, không phải yêu cầu bắt buộc của ISO.

## Doanh nghiệp dùng chung

Các màn hình web vận hành đọc cùng dữ liệu PostgreSQL theo đợt đánh giá: 50 nhân viên, 50 máy riêng và tài sản/tài khoản lab liên quan. Xem [kiến trúc và migration](docs/DOANH_NGHIEP_DUNG_CHUNG.md). CLI nghiên cứu và benchmark vẫn dùng fixture cô lập.

## Thực nghiệm và giới hạn

- Ca benchmark tổng hợp tự xây dựng, chưa thẩm định mù bởi chuyên gia.
- `run_user_study.py` sinh dữ liệu bằng random. Các số liệu SUS, giảm thời gian trong tài liệu cũ không phải khảo sát người thật.
- Kết quả cũ trong `docs/charts` và `docs/week3` phải đối chiếu nguồn, tập ca và thời điểm trước khi trích dẫn.
- Test phần mềm đạt không chứng minh chất lượng đánh giá ISO hoặc lợi ích riêng của LLM.
- [Quy trình đánh giá/khảo sát](docs/BAO-VE-VA-KHAO-SAT.md).

## Chạy và tài liệu

[Chạy local](CHAY_LOCAL.md): http://127.0.0.1:5173; API http://127.0.0.1:8000/docs.
Không đưa `.env`, mật khẩu hoặc token lên Git.

- [Phạm vi](docs/PHAM_VI_DANH_GIA.md)
- [Kiến trúc Agent](docs/KIEN_TRUC_AGENT_TU_VIDEO.md)
- [Trụ sở điều phối](docs/TRU_SO_DIEU_PHOI.md)
- [Kết quả kiểm chứng hiện tại](docs/KIEM_CHUNG_DANH_GIA.md)
- [Nhật ký tuần](ke_hoach_nhat_ky_tuan/README.md)
