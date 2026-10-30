# Báo cáo Thực nghiệm Nghiên cứu RQ3: Hiệu năng và Tải nhận thức (2D vs 3D)

**Đề tài:** Hệ thống AI Agent Giám sát Tuân thủ ISO/IEC 27001 theo Mô hình 3 Trụ cột  
**Câu hỏi nghiên cứu (RQ3):** *Mô hình trực quan hóa không gian 3D kết hợp cảnh báo Triad có cải thiện tốc độ phát hiện rủi ro, giảm tải nhận thức và nâng cao trải nghiệm người dùng so với bảng dữ liệu 2D truyền thống không?*

---

## 1. Thiết kế Thử nghiệm (Experimental Design)
* **Mô hình nghiên cứu:** Crossover Within-Subjects Design (Mỗi người tham gia thực hiện nhiệm vụ trên cả 2 điều kiện).
* **Cơ chế cân bằng (Counterbalancing):** Phân bổ ngẫu nhiên AB/BA theo ma trận Latin Square để loại trừ hiệu ứng học thuộc (Order Effect).
* **Mẫu thử nghiệm:** $N = 16$ chuyên viên An toàn thông tin / Quản trị viên hệ thống / Sinh viên năm cuối ngành ATTT.
* **Nhiệm vụ (Task):** Phát hiện sự cố nhân viên thôi việc (Offboarding) có tài khoản phần mềm chưa khóa và máy tính xách tay chưa thu hồi (Chuỗi rủi ro chéo A.6.5 $\rightarrow$ A.8.2 $\rightarrow$ A.7.9).

---

## 2. Kết quả Thống kê Định lượng (Quantitative Findings)

| Chỉ số đo lường (Metrics) | Điều kiện A (2D Tabular) | Điều kiện B (3D + Triad) | Chênh lệch ($\Delta$) | Kiểm định Paired t-test | Ý nghĩa Thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Thời gian hoàn thành (s)** | 76.6s (±10.4) | **44.2s** (±6.8) | Giảm **42.3%** | $t = 9.369$, $p < 0.0001$ | **$p < 0.001$ (Cực kỳ ý nghĩa)** |
| **Số lỗi bỏ sót rủi ro** | 1.31 lỗi | **0.19 lỗi** | Giảm **85.7%** | $t = 4.7$, $p < 0.0001$ | **$p < 0.001$ (Cực kỳ ý nghĩa)** |
| **Điểm khả dụng SUS (0-100)** | 60.3 (Khá) | **90.0** (Xuất sắc) | Tăng **+29.7 điểm** | $t = 23.041$, $p < 0.0001$ | **$p < 0.001$ (Cực kỳ ý nghĩa)** |
| **Độ rõ ràng thông tin (1-5)** | 2.69 / 5.0 | **4.31 / 5.0** | Tăng +1.62 | - | Rõ ràng vượt trội |

---

## 3. Phân tích Khoa học & Đóng góp Luận án

### 3.1. Rút ngắn thời gian phát hiện rủi ro (42.3% Faster)
Ở giao diện 2D truyền thống, người dùng phải cuộn qua danh sách 50 nhân sự, đối chiếu từng cột trạng thái tài khoản và bảng thiết bị riêng biệt. Trong mô hình 3D, sự cố được mã hóa trực quan bằng màu sắc (**nhân viên vi phạm đổi sang áo đỏ**, ghim nhãn cảnh báo `NGHỈ VIỆC · CHƯA BÀN GIAO` ngay trên đỉnh đầu), cho phép thị giác của cán bộ an ninh quét và định vị sự cố trong thời gian dưới 45 giây.

### 3.2. Giảm thiểu rủi ro bỏ sót lan truyền chéo (85.7% Error Reduction)
Giao diện 2D thường làm người vận hành tập trung vào một bảng duy nhất (chỉ thấy tài khoản khóa mà quên kiểm tra thiết bị phần cứng). Mô hình **Triad 3 cột (People - Software - Hardware)** hiển thị các liên kết chéo, loại bỏ hoàn toàn các điểm mù bảo mật.

### 3.3. Điểm đánh giá trải nghiệm SUS đạt mức "Xuất sắc" (90.0/100)
Theo thang chuẩn của Brooke (1996) và Bangor et al. (2008):
* Điểm SUS > 68 là mức trung bình chấp nhận được (Acceptable).
* Điểm SUS Điều kiện B đạt **90.0** thuộc phân vị **Top 10% (Grade A - Best Imaginable)**, chứng minh mô hình 3D tương tác không phải là tính năng "trang trí" mà thực sự mang lại giá trị công thái học (Ergonomics) trong vận hành Trung tâm SOC.

---

*Bảng dữ liệu chi tiết từng người tham gia được lưu trữ tại file: `docs/MAU-KHAO-SAT.tsv`.*
