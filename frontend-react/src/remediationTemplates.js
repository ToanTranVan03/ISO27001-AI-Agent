// Advisory starting points for the project rubric. A specialist must review each draft.
const rows = `6.1|Nhân sự|Rà hồ sơ thẩm tra trước tuyển dụng theo vị trí|Danh sách mẫu và biên bản thẩm tra đã che dữ liệu cá nhân|Đối chiếu ngày thẩm tra với ngày tuyển và yêu cầu của vị trí
6.2|Nhân sự|Bổ sung điều khoản ATTT vào hồ sơ lao động|Mẫu điều khoản và hồ sơ ký đúng phiên bản|Đối chiếu phiên bản, thời điểm ký và phạm vi nhân viên
6.3|Nhân sự và ATTT|Giao đào tạo và kiểm tra lại nhận thức cho nhóm còn thiếu|Danh sách tham gia và kết quả kiểm tra theo kỳ|Đối chiếu người trong phạm vi với hồ sơ hoàn thành và kết quả
6.4|Nhân sự|Rà quy trình xử lý vi phạm và luồng phê duyệt|Quy trình được duyệt và hồ sơ tình huống đã ẩn danh|Đối chiếu trách nhiệm, thông báo và quyền giải trình trong mẫu
6.5|Nhân sự và CNTT|Thu hồi thiết bị và kiểm tra cắt quyền khi nghỉ việc|Checklist nghỉ việc, biên nhận theo mã thiết bị và nhật ký cắt quyền|Đối chiếu từng thiết bị và tài khoản với ngày nghỉ
6.6|Nhân sự và Pháp chế|Rà người còn thiếu thỏa thuận bảo mật đúng phiên bản|Danh mục phiên bản và bản ghi ký được phép xem|Đối chiếu người nhận, phiên bản và ngày xác nhận
6.7|CNTT|Rà điều kiện truy cập từ xa và bảo vệ máy làm việc|Quy định từ xa và nguồn cấu hình VPN, MFA, mã hóa|Đối chiếu mẫu truy cập và các ngoại lệ được duyệt
6.8|ATTT|Diễn tập báo cáo sự cố qua kênh nội bộ|Phiếu diễn tập, dấu thời gian và xác nhận tiếp nhận|Kiểm tra kênh báo, nội dung và thời gian phản hồi
7.1|Vận hành cơ sở|Rà ranh giới khu vực cần bảo vệ và khắc phục điểm hở|Sơ đồ khu vực và biên bản kiểm tra sau sửa|Đối chiếu từng ranh giới và điểm ra vào với sơ đồ
7.2|An ninh cơ sở|Rà và cập nhật quyền ra vào khu vực hạn chế|Danh sách quyền và nhật ký ra vào đã lọc|Kiểm quyền còn hiệu lực và đối chiếu mẫu truy cập
7.3|Vận hành cơ sở|Bổ sung biện pháp khóa và quản lý phòng nhạy cảm|Danh mục phòng, biện pháp bảo vệ và biên bản kiểm tra|Kiểm trực tiếp phòng và người được phép mở
7.4|An ninh cơ sở|Rà độ phủ và lưu giữ dữ liệu giám sát vật lý|Sơ đồ phủ, chính sách lưu và bản ghi thử|Kiểm điểm giám sát và quyền truy xuất bản ghi
7.5|Vận hành cơ sở|Xử lý điểm thiếu phòng ngừa cháy, nước và môi trường|Danh mục rủi ro, biên bản bảo trì và thử cảnh báo|Đối chiếu từng điểm với biện pháp và lần thử
7.6|An ninh cơ sở|Áp dụng quy trình làm việc và giám sát khu an toàn|Quy trình, danh sách người vào và nhật ký giám sát|Đối chiếu một lượt làm việc với điều kiện được phép
7.7|Nhân sự và CNTT|Rà bàn làm việc sạch và cấu hình khóa màn hình|Checklist kiểm tra và cấu hình timeout thực tế|Đo khóa màn hình và rà mẫu khu vực làm việc
7.8|Vận hành cơ sở|Điều chỉnh vị trí và bảo vệ thiết bị dễ bị tác động|Danh mục thiết bị, vị trí và biên bản kiểm tra|Đối chiếu mã tài sản, vị trí và biện pháp bảo vệ
7.9|Quản lý tài sản|Rà quyền mang thiết bị ra ngoài và hồ sơ bàn giao|Phiếu giao nhận theo mã tài sản và nguồn mã hóa|Đối chiếu người giữ, thời hạn và trạng thái thiết bị
7.10|Quản lý tài sản|Kiểm kê và quản lý vòng đời vật mang tin|Danh mục, nhật ký lưu chuyển và biên bản xử lý|Truy vết một vật mang tin từ cấp phát tới thu hồi
7.11|Vận hành cơ sở|Rà UPS và khả năng duy trì dịch vụ thiết yếu|Biên bản bảo trì và phép thử nguồn dự phòng|Kiểm điều kiện chuyển nguồn và thời gian duy trì
7.12|Hạ tầng|Rà tuyến cáp và điểm đấu nối cần bảo vệ|Sơ đồ cáp và biên bản kiểm tra tuyến|Đối chiếu tuyến thực tế với khu vực và điểm khóa
7.13|Quản lý tài sản|Lập lịch bảo trì và kiểm soát quyền nhà bảo trì|Phiếu bảo trì, phạm vi quyền và biên bản nghiệm thu|Kiểm đúng thiết bị, người thực hiện và quyền đã thu hồi
7.14|Quản lý tài sản|Rà quy trình làm sạch và thanh lý thiết bị|Chuỗi bàn giao và bản ghi xác minh đã làm sạch|Đối chiếu số sê-ri và bằng chứng xóa trước khi tái sử dụng
8.1|CNTT máy trạm|Rà baseline bảo vệ thiết bị đầu cuối|Inventory và bản xuất cấu hình bảo vệ máy trạm|Đối chiếu cấu hình từng máy mẫu với baseline được duyệt
8.2|Quản trị danh tính|Rà và thu hẹp quyền đặc quyền dư thừa|Danh sách quyền trước sau và phiếu phê duyệt|Đối chiếu từng tài khoản với nhiệm vụ và ngoại lệ
8.3|Chủ hệ thống|Rà ma trận quyền truy cập dữ liệu|Ma trận quyền và bản xuất cấu hình truy cập|Đối chiếu quyền thực tế với phân loại dữ liệu và người được phép
8.4|Nhóm phát triển|Rà quyền truy cập kho mã nguồn và nhánh bảo vệ|Bản xuất quyền kho mã và cấu hình nhánh|Đối chiếu nhóm quyền và kiểm tra quy trình duyệt thay đổi
8.5|Quản trị danh tính|Rà chính sách xác thực và yêu cầu MFA đúng đối tượng|Cấu hình xác thực và kết quả thử trước sau|Đối chiếu phạm vi chính sách và thử xác thực được phép
8.6|Vận hành CNTT|Rà ngưỡng tài nguyên và kế hoạch tăng dung lượng|Số liệu tải, ngưỡng cảnh báo và kế hoạch công suất|Đối chiếu tải ở kỳ cao điểm và thử ngưỡng cảnh báo
8.7|ATTT máy trạm|Rà cấu hình bảo vệ mã độc và quy trình xử lý cảnh báo|Trạng thái bảo vệ và nhật ký xử lý của lab|Dùng mẫu kiểm tra vô hại trong lab và đối chiếu sự kiện
8.8|Vận hành CNTT|Kiểm kê phiên bản và lập kế hoạch cập nhật được duyệt|Inventory trước sau, phiếu thay đổi và kết quả kiểm tra|Đối chiếu phiên bản đang chạy với mục tiêu và kiểm tình trạng
8.9|Vận hành hệ thống|Đối chiếu cấu hình thực với baseline được duyệt|Cấu hình trước sau, phiên bản baseline và bản so sánh|Rà khác biệt còn lại và các ngoại lệ được duyệt
8.10|Chủ dữ liệu|Rà lịch xóa theo chính sách lưu giữ|Phiếu xử lý, phạm vi dữ liệu và biên nhận phép thử|Kiểm mẫu dữ liệu thử không còn đọc được sau xử lý
8.11|Chủ dữ liệu|Che trường nhạy cảm trong bản sao phục vụ nghiệp vụ|Quy tắc che và mẫu dữ liệu tổng hợp trước sau|Đối chiếu các trường phải che và quyền đọc bản gốc
8.12|ATTT|Rà quy tắc ngăn thất thoát và luồng cảnh báo|Cấu hình DLP và nhật ký phép thử mẫu vô hại|Kiểm luồng được phép và luồng bị chặn trong lab
8.13|Vận hành hệ thống|Rà sao lưu và diễn tập khôi phục bản sao thử|Nhật ký sao lưu, hash và biên bản khôi phục|Khôi phục thử và đối chiếu tính toàn vẹn với mục tiêu
8.14|Hạ tầng|Kiểm tra dự phòng và diễn tập chuyển đổi có phê duyệt|Sơ đồ dự phòng và biên bản diễn tập|Đối chiếu thời gian chuyển đổi và khả năng phục hồi
8.15|Vận hành hệ thống|Bổ sung ghi nhật ký và bảo vệ nguồn log|Cấu hình ghi log và sự kiện thử có dấu thời gian|Đối chiếu sự kiện phát sinh với bản ghi và quyền đọc
8.16|ATTT|Rà luật giám sát và trách nhiệm tiếp nhận cảnh báo|Luật giám sát, cảnh báo thử và biên nhận xử lý|Kiểm khả năng phát hiện và thời gian tiếp nhận
8.17|Hạ tầng|Rà nguồn thời gian và cấu hình đồng bộ|Danh sách nguồn giờ và số đo sai lệch|Đối chiếu nguồn giờ và ngưỡng sai lệch được duyệt
8.18|Quản trị hệ thống|Rà tiện ích đặc quyền và hạn chế người được sử dụng|Danh mục tiện ích, quyền và nhật ký dùng thử|Đối chiếu quyền với vai trò và bản ghi theo dõi
8.19|CNTT máy trạm|Rà danh mục phần mềm được phép và quy trình cài|Inventory, danh mục cho phép và phiếu cấp quyền|Đối chiếu gói đã cài với danh mục và ngoại lệ
8.20|Hạ tầng mạng|Rà cấu hình bảo vệ mạng và luồng đi được phép|Sơ đồ mạng, cấu hình và biên nhận kiểm tra lab|Đối chiếu các luồng đã khai với quy tắc hiện hành
8.21|Hạ tầng mạng|Rà yêu cầu bảo mật của các dịch vụ mạng|Hồ sơ dịch vụ, yêu cầu cấu hình và kết quả đối chiếu|Kiểm dịch vụ mẫu đáp ứng thông số và trách nhiệm
8.22|Hạ tầng mạng|Rà tách vùng và luồng liên vùng|Sơ đồ phân vùng, quy tắc và phép thử lab|Đối chiếu luồng liên vùng được phép và bị chặn
8.23|ATTT|Rà chính sách lọc web và danh sách ngoại lệ|Chính sách lọc và log phép thử với dữ liệu mẫu|Kiểm đúng nhóm chính sách và ngoại lệ được duyệt
8.24|ATTT|Rà cấu hình mã hóa và quản lý vòng đời khóa|Cấu hình, danh mục khóa đã che bí mật và biên bản kiểm|Đối chiếu thuật toán, quyền và kỳ xoay khóa theo chính sách
8.25|Nhóm phát triển|Bổ sung bước kiểm tra ATTT vào vòng đời phát triển|Quy trình và hồ sơ rà soát một bản phát hành|Đối chiếu các cổng duyệt với bằng chứng ở từng giai đoạn
8.26|Chủ ứng dụng|Chốt yêu cầu bảo mật và tiêu chí nghiệm thu ứng dụng|Đặc tả yêu cầu và ma trận truy vết test|Đối chiếu từng yêu cầu với kết quả nghiệm thu
8.27|Kiến trúc CNTT|Rà thiết kế, ranh giới tin cậy và quyết định kiến trúc|Sơ đồ, biên bản rà thiết kế và danh sách ngoại lệ|Đối chiếu thiết kế triển khai với nguyên tắc đã duyệt
8.28|Nhóm phát triển|Sửa lỗi mã nguồn theo quy trình review bảo mật|Phiếu sửa mã, kết quả review và kiểm thử hồi quy|Đối chiếu thay đổi với tiêu chí coding và kết quả kiểm
8.29|Kiểm thử và ATTT|Hoàn thiện kiểm thử bảo mật trước nghiệm thu|Kế hoạch kiểm thử, kết quả và hồ sơ xử lý lỗi|Đối chiếu ca kiểm với yêu cầu và trạng thái kiểm lại
8.30|Quản lý nhà cung cấp|Rà yêu cầu bảo mật với bên phát triển thuê ngoài|Điều khoản, biên bản bàn giao và đánh giá nhà cung cấp|Đối chiếu nghĩa vụ với bằng chứng thực hiện
8.31|Vận hành và phát triển|Rà tách môi trường phát triển, kiểm thử và vận hành|Sơ đồ, danh mục quyền và cấu hình triển khai|Đối chiếu tài khoản và luồng triển khai giữa các môi trường
8.32|Quản lý thay đổi|Chuẩn hóa hồ sơ, duyệt và kiểm lại sau thay đổi|Phiếu thay đổi, kết quả kiểm và kế hoạch hoàn nguyên|Đối chiếu thời điểm, người duyệt và kết quả sau triển khai
8.33|Kiểm thử và chủ dữ liệu|Rà nguồn dữ liệu thử và loại dữ liệu nhạy cảm|Danh mục bộ thử, quy tắc xử lý và mẫu tổng hợp|Kiểm nguồn được phép và trường nhạy cảm đã xử lý
8.34|Kiểm toán và vận hành|Chốt phạm vi kiểm tra, quyền và thời gian đã duyệt|Kế hoạch kiểm toán, nhật ký và biên bản thu hồi quyền|Đối chiếu thao tác thực tế với phạm vi và kiểm quyền sau thử`;

export const remediationTemplates = Object.fromEntries(rows.split('\n').map(row=>{
 const [id, department, title, evidence, verification] = row.split('|');
 return ['A.'+id,{department,title,evidence,verification}];
}));

export function remediationDraft(controlId){
 const template=remediationTemplates[controlId];
 if(!template)return null;
 const {department,title,evidence,verification}=template;
 return {
  title,department,
  steps: title+'. Xác định tài sản, người và phạm vi từ phát hiện, sau đó thực hiện theo kế hoạch đã duyệt.',
  resources:'Nguồn và quyền thực hiện được người phụ trách xác nhận.',
  acceptance:verification+'.',
  required_evidence:evidence+'.',
  recheck_method:verification+'.',
  tasks:'Xác nhận phạm vi và phương án với người phụ trách\n'+title+'\nNộp bằng chứng sau thực hiện để chuyên viên kiểm tra',
 };
}
