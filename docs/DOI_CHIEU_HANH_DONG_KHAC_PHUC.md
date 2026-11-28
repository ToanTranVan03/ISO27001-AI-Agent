# Đối chiếu hành động khắc phục và phạm vi demo

| Điều cần thể hiện | Dữ liệu và hành động trong dự án | Phần cần thêm |
|---|---|---|
| Phát hiện vấn đề, có căn cứ | Scope 56 giữ nguồn, rubric và kết luận. MFA thu phép đo đầu vào từ lab, phát hiện ghi tiêu chí và snapshot. | Bổ sung các hồ sơ đang thiếu và xác nhận phạm vi. |
| Có hành động sau phát hiện | A.8.5 bật yêu cầu yếu tố thứ hai cho tài khoản tổng hợp. A.8.8 minh họa cập nhật ứng dụng mẫu từ 1.0.0 lên 1.1.0. A.6.5 giao nhân viên bàn giao thiết bị và người tiếp nhận đối chiếu biên nhận. | Cần nguồn thật, môi trường đích và connector được phép nếu thực hiện ngoài các ca demo. |
| Xác minh và báo cáo trước sau | Hai công cụ lab đo lại sau khi ghi thay đổi; giữ người duyệt, người chạy, thời điểm và dữ liệu đọc lại. Bàn giao có lịch sử yêu cầu bổ sung. Báo cáo PDF/Excel giữ biên nhận. | Thẩm định của người phụ trách và phê duyệt SoA cần thực hiện riêng. |
| Môi trường khác nhau | Probe A.8.8 đọc inventory dpkg trong lab Linux. Demo ứng dụng lưu hệ điều hành thực quan sát được và chạy bằng Python trên máy kiểm thử. | Mỗi hệ điều hành hoặc thiết bị cần nguồn inventory đúng nền tảng, chính sách phiên bản, thao tác cập nhật được cấp quyền và phép kiểm tra sau thay đổi. Tên một số thiết bị trong bản chép lời cần xác nhận. |
| Giao diện rõ người thực hiện và bước tiếp theo | Bốn màn hình chính nêu mục đích, người làm và bước kế tiếp. Khắc phục phân biệt trạng thái giao việc, phép đo của công cụ và thẩm định chuyên viên. | Một số thao tác của nhân viên vẫn được kiểm bằng API trong ca tích hợp. |

## Chạy demo cập nhật ứng dụng

Bật `ISO_MFA_DEMO_ENABLED=1` trên backend của đợt thử cô lập. Tạo phát hiện tham chiếu A.8.8, chọn phạm vi toàn control cho demo rồi đặt tên và mô tả ứng dụng thử iso-demo-inventory. Tạo kế hoạch, duyệt giao người phụ trách và bấm **Chạy cập nhật ứng dụng mẫu**. Xem biên nhận trên đầu việc, tải JSON hoặc xuất PDF/Excel.

Công cụ sinh hai gói Python mẫu trong thư mục tạm, kiểm hash, thay đúng tệp ứng dụng mẫu và khởi chạy ứng dụng đã cài để đọc phiên bản, trạng thái và hash. Thư mục tạm dọn sau lượt chạy. Kết quả chỉ phản ánh ứng dụng mẫu. Tiêu chí vá hệ điều hành và trạng thái tuân thủ A.8.8 có quy trình thẩm định riêng.

```powershell
npm --prefix frontend-react run build
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/mfa-software-lab-new.json
```

Chạy trực tiếp CLI: `.venv\Scripts\python.exe -m lab_a8.software_update_demo --output work/software-update-new.json`. CLI yêu cầu mã đề xuất để xác nhận chạy, tên người vận hành do người dùng khai.

[Biên nhận lượt tích hợp MFA và cập nhật ứng dụng](../work/mfa-software-lab-verified.json).

## Nguồn cập nhật ứng dụng trước và sau

Bấm **Thu phiên bản ứng dụng mẫu từ lab** trước khi lập phát hiện. Hệ thống chạy gói mẫu, lưu kết quả đọc phiên bản ban đầu và hash vào kho nguồn A.8.8. Sau khi duyệt và chạy cập nhật, bấm **Lưu biên nhận cập nhật vào nguồn A.8.8** trong thẻ đầu việc. Mỗi nguồn có mã và bản gốc, nạp lại biên nhận không tạo bản trùng. Chuyên viên vẫn rà nguồn và xác định phạm vi kết luận. Hồ sơ chỉ xác nhận ứng dụng mẫu trong lab.

Lệnh nghiệm thu ở trên kiểm cả hai nút, kiểm nguồn trước/sau xuất hiện đúng control và xác nhận kết luận thẩm định không tự đổi. [Biên nhận lượt kiểm](../work/software-evidence-2026-11-28.json).

## Khi giao việc và thẩm định

Mỗi đầu việc trong phạm vi 56 control hiển thị người phụ trách, cách thực hiện, bằng chứng cần nộp, cách kiểm tra lại và số nguồn đã gắn. Nếu đợt có công cụ lab phù hợp, thẻ ghi đích và thao tác được phép. Khi công việc chờ xác minh, người có quyền mở đúng tiêu chí và bằng chứng từ ngay trong thẻ. Sau khi thẩm định, quay lại đầu việc để lưu kết quả xác minh.

Đầu việc dùng kế hoạch do chuyên viên duyệt. Tự động hóa lab hiện có cho hai ca MFA và cập nhật ứng dụng thử. Mỗi thao tác ngoài lab cần công cụ và phép đo phù hợp với thiết bị hoặc hệ điều hành cụ thể.
