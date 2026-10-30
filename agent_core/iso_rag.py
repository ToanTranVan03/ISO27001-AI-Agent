"""ISO/IEC 27002:2022 Knowledge Retrieval-Augmented Generation (RAG) Engine.

Provides authoritative standard text, implementation guidance, CIA impact analysis,
and actionable remediation recommendations across People (A.6), Software/Tech (A.8),
and Physical/Hardware (A.7) controls.
"""

from typing import Dict, List, Optional
import re

# Comprehensive ISO/IEC 27002:2022 Control Knowledge Base
ISO_27002_KB: Dict[str, dict] = {
    "A.6.1": {
        "code": "A.6.1",
        "title": "A.6.1 Sàng lọc lý lịch (Screening)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Đảm bảo tất cả ứng viên được thẩm tra phù hợp trước khi gia nhập tổ chức.",
        "text": "Các biện pháp kiểm tra lý lịch đối với mọi ứng viên tuyển dụng phải được thực hiện phù hợp với luật pháp, quy định liên quan và đạo đức nghề nghiệp, tương xứng với yêu cầu công việc, mức độ phân loại thông tin được tiếp cận và các rủi ro nhận diện.",
        "guidance": "Quy trình sàng lọc cần bao gồm: xác minh danh tính, bằng cấp học vấn, lịch sử công tác, và đối với các vị trí quản trị hệ thống/tài chính nhạy cảm cần xác minh tư pháp.",
        "evidence_required": ["Hồ sơ thẩm tra lý lịch (Background check)", "Bản xác minh tư pháp", "Biên bản phỏng vấn kỹ thuật"],
        "cia_impact": {"C": 3, "I": 3, "A": 1},
        "keywords": ["sàng lọc", "screening", "lý lịch", "background check", "tuyển dụng", "nhân sự mới"]
    },
    "A.6.2": {
        "code": "A.6.2",
        "title": "A.6.2 Điều khoản và điều kiện làm việc (Terms and conditions of employment)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Đảm bảo nhân sự hiểu rõ trách nhiệm an toàn thông tin trước khi bắt đầu công việc.",
        "text": "Các thỏa thuận hợp đồng lao động phải nêu rõ trách nhiệm an toàn thông tin của nhân viên và của tổ chức, bao gồm nghĩa vụ bảo mật thông tin (NDA) và tuân thủ các chính sách ATTT.",
        "guidance": "Hợp đồng hoặc phụ lục bảo mật phải được ký trước khi nhân sự được cấp bất kỳ quyền truy cập nào vào tài sản thông tin của tổ chức.",
        "evidence_required": ["Thỏa thuận không tiết lộ (NDA) có chữ ký", "Hợp đồng lao động có điều khoản ATTT", "Cam kết tuân thủ chính sách"],
        "cia_impact": {"C": 4, "I": 2, "A": 1},
        "keywords": ["hợp đồng", "nda", "bảo mật", "terms", "employment", "cam kết", "điều khoản"]
    },
    "A.6.3": {
        "code": "A.6.3",
        "title": "A.6.3 Đào tạo và nâng cao nhận thức an toàn thông tin (Information security awareness, education and training)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Đảm bảo nhân sự được đào tạo phù hợp và cập nhật định kỳ về các chính sách ATTT.",
        "text": "Nhân sự của tổ chức và các bên liên quan phải nhận được chương trình nâng cao nhận thức, đào tạo và giáo dục phù hợp, cũng như cập nhật thường xuyên các chính sách, quy trình ATTT của tổ chức.",
        "guidance": "Đào tạo phải diễn ra định kỳ (ít nhất hàng năm), có bài kiểm tra đánh giá (LMS/Quiz) và lưu trữ hồ sơ chứng minh kết quả đạt yêu cầu.",
        "evidence_required": ["Chứng chỉ hoàn thành khóa đào tạo LMS", "Biên bản điểm danh đào tạo định kỳ", "Kết quả bài kiểm tra sát hạch ATTT"],
        "cia_impact": {"C": 3, "I": 3, "A": 2},
        "keywords": ["đào tạo", "training", "nhận thức", "awareness", "lms", "sát hạch", "khóa học"]
    },
    "A.6.4": {
        "code": "A.6.4",
        "title": "A.6.4 Quy trình kỷ luật (Disciplinary process)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Thiết lập cơ chế xử lý rõ ràng đối với các hành vi vi phạm an toàn thông tin.",
        "text": "Một quy trình kỷ luật chính thức và được truyền thông rõ ràng phải được thiết lập để xử lý các nhân sự đã thực hiện hành vi vi phạm an toàn thông tin.",
        "guidance": "Quy trình kỷ luật phải được phổ biến cho toàn thể nhân viên ngay khi tuyển dụng và có chế tài tương ứng theo mức độ vi phạm.",
        "evidence_required": ["Nội quy lao động có điều khoản chế tài ATTT", "Biên bản xác nhận đã đọc quy trình kỷ luật", "Quyết định xử lý kỷ luật (nếu có)"],
        "cia_impact": {"C": 2, "I": 3, "A": 1},
        "keywords": ["kỷ luật", "disciplinary", "chế tài", "vi phạm", "xử phạt", "nội quy"]
    },
    "A.6.5": {
        "code": "A.6.5",
        "title": "A.6.5 Trách nhiệm sau khi chấm dứt hoặc thay đổi hợp đồng (Responsibilities after termination or change of employment)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Bảo vệ tài sản thông tin của tổ chức khi nhân sự thôi việc hoặc chuyển đổi vị trí công tác.",
        "text": "Các trách nhiệm và nghĩa vụ an toàn thông tin vẫn có hiệu lực sau khi chấm dứt hoặc thay đổi vị trí công việc phải được xác định, truyền đạt và thực thi.",
        "guidance": "Phải có quy trình Offboarding nghiêm ngặt: thu hồi toàn bộ tài khoản đăng nhập (SaaS, VPN, Email) trong vòng 24h và thu hồi toàn bộ thiết bị phần cứng (laptop, thẻ từ, khóa bảo mật) trước ngày làm việc cuối cùng.",
        "evidence_required": ["Biên bản bàn giao công việc & tài sản (Offboarding Checklist)", "Xác nhận thu hồi quyền từ quản trị hệ thống", "Xác nhận thu hồi thiết bị từ IT Support"],
        "cia_impact": {"C": 5, "I": 4, "A": 3},
        "keywords": ["nghỉ việc", "thôi việc", "offboarding", "bàn giao", "thu hồi", "thay đổi vị trí", "chấm dứt"]
    },
    "A.6.7": {
        "code": "A.6.7",
        "title": "A.6.7 Làm việc từ xa (Remote working)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Bảo vệ thông tin được truy cập, xử lý hoặc lưu trữ tại các địa điểm làm việc từ xa bên ngoài tổ chức.",
        "text": "Các biện pháp an toàn phải được thực hiện khi nhân viên làm việc từ xa để bảo vệ thông tin được truy cập, xử lý hoặc lưu trữ bên ngoài cơ sở của tổ chức.",
        "guidance": "Yêu cầu bắt buộc: (1) Thiết bị đầu cuối phải được mã hóa toàn bộ ổ đĩa (BitLocker/FileVault); (2) Kết nối mạng phải qua VPN có xác thực đa yếu tố (MFA); (3) Cấm sử dụng thiết bị cá nhân (BYOD) không được quản lý.",
        "evidence_required": ["Chính sách làm việc từ xa có phê duyệt", "Bằng chứng mã hóa đĩa cứng thiết bị", "Nhật ký kết nối VPN có xác thực MFA"],
        "cia_impact": {"C": 5, "I": 4, "A": 2},
        "keywords": ["làm việc từ xa", "remote", "wfh", "telework", "vpn", "mfa", "mã hóa thiết bị"]
    },
    "A.6.8": {
        "code": "A.6.8",
        "title": "A.6.8 Báo cáo sự cố an toàn thông tin (Information security event reporting)",
        "pillar": "people",
        "category": "6. People controls",
        "objective": "Đảm bảo các sự cố an toàn thông tin được báo cáo kịp thời qua các kênh thích hợp.",
        "text": "Tổ chức phải cung cấp cơ chế để nhân sự báo cáo kịp thời các sự cố hoặc điểm yếu an toàn thông tin quan sát được thông qua các kênh tiếp nhận chính thức.",
        "guidance": "Nhân sự phải được hướng dẫn cách nhận diện email lừa đảo (phishing), mã độc hoặc dấu hiệu bất thường và biết rõ kênh báo cáo (SOC email, hotline, ticketing).",
        "evidence_required": ["Kênh tiếp nhận sự cố ATTT (SOC ServiceDesk)", "Nhật ký tiếp nhận và xử lý sự cố", "Tài liệu hướng dẫn quy trình báo cáo"],
        "cia_impact": {"C": 3, "I": 4, "A": 4},
        "keywords": ["báo cáo sự cố", "incident", "reporting", "soc", "điểm yếu", "phishing", "thông báo"]
    },
    "A.7.7": {
        "code": "A.7.7",
        "title": "A.7.7 Chính sách bàn làm việc và màn hình sạch (Clear desk and clear screen)",
        "pillar": "hardware",
        "category": "7. Physical controls",
        "objective": "Ngăn chặn việc truy cập trái phép và nguy cơ rò rỉ thông tin trên giấy tờ hoặc màn hình hiển thị.",
        "text": "Quy tắc bàn làm việc sạch đối với tài liệu giấy và phương tiện lưu trữ rời rạc, cùng quy tắc màn hình sạch cho các phương tiện xử lý thông tin phải được xác định và thực thi thích hợp.",
        "guidance": "Tự động khóa màn hình sau tối đa 5 phút không hoạt động; tài liệu nhạy cảm phải được cất vào tủ khóa khi rời vị trí.",
        "evidence_required": ["Biên bản kiểm tra an ninh văn phòng định kỳ", "Cấu hình Group Policy tự động khóa màn hình", "Tủ có khóa lưu trữ hồ sơ"],
        "cia_impact": {"C": 4, "I": 2, "A": 1},
        "keywords": ["bàn sạch", "màn hình sạch", "clear desk", "clear screen", "khóa màn hình", "tủ khóa"]
    },
    "A.7.9": {
        "code": "A.7.9",
        "title": "A.7.9 Bảo vệ tài sản ngoài cơ sở (Security of off-premises assets)",
        "pillar": "hardware",
        "category": "7. Physical controls",
        "objective": "Bảo vệ tài sản của tổ chức khi được mang ra bên ngoài văn phòng.",
        "text": "Các tài sản bên ngoài cơ sở của tổ chức phải được bảo vệ, lưu ý đến các rủi ro khác nhau khi hoạt động bên ngoài ranh giới của tổ chức.",
        "guidance": "Mọi máy tính xách tay mang ra ngoài phải được đăng ký sổ theo dõi tài sản, có phần mềm EDR/Antivirus cập nhật và không được để lại nơi công cộng không có người trông coi.",
        "evidence_required": ["Sổ bàn giao và theo dõi thiết bị mang ra ngoài", "Chứng chỉ quản lý thiết bị MDM (Intune/Jamf)", "Nhật ký kiểm kê phần cứng định kỳ"],
        "cia_impact": {"C": 4, "I": 3, "A": 3},
        "keywords": ["tài sản ngoài", "off-premises", "laptop", "thiết bị lưu động", "mang ra ngoài", "bảo vệ phần cứng"]
    },
    "A.8.1": {
        "code": "A.8.1",
        "title": "A.8.1 Thiết bị đầu cuối của người dùng (User endpoint devices)",
        "pillar": "hardware",
        "category": "8. Technological controls",
        "objective": "Bảo vệ thông tin được lưu trữ và xử lý trên các thiết bị đầu cuối của người dùng.",
        "text": "Thông tin lưu trữ, xử lý hoặc truy cập thông qua các thiết bị đầu cuối của người dùng phải được bảo vệ trước các mối đe dọa an ninh mạng.",
        "guidance": "Cài đặt chuẩn hóa: Hệ điều hành có bản quyền cập nhật vá lỗi, bật tường lửa cá nhân, kích hoạt BitLocker/FileVault và cài phần mềm phòng chống mã độc tập trung.",
        "evidence_required": ["Báo cáo trạng thái mã hóa đĩa từ MDM", "Nhật ký cập nhật bản vá bảo mật (Patch Management)", "Cấu hình Antivirus/EDR"],
        "cia_impact": {"C": 4, "I": 4, "A": 3},
        "keywords": ["thiết bị đầu cuối", "endpoint", "laptop", "mã hóa", "bitlocker", "antivirus", "vá lỗi"]
    },
    "A.8.2": {
        "code": "A.8.2",
        "title": "A.8.2 Quyền truy cập đặc quyền (Privileged access rights)",
        "pillar": "software",
        "category": "8. Technological controls",
        "objective": "Kiểm soát và hạn chế việc cấp phát và sử dụng các quyền truy cập đặc quyền.",
        "text": "Việc phân bổ và sử dụng các quyền truy cập đặc quyền (Administrator, Root, Superuser) phải được hạn chế và kiểm soát chặt chẽ.",
        "guidance": "Áp dụng nguyên tắc quyền tối thiểu (Least Privilege), bắt buộc dùng MFA cho tài khoản đặc quyền, và định kỳ rà soát thu hồi quyền khi nhân sự chuyển vai trò.",
        "evidence_required": ["Danh sách tài khoản đặc quyền có phê duyệt", "Nhật ký sử dụng tài khoản Admin", "Biên bản rà soát quyền định kỳ hàng quý"],
        "cia_impact": {"C": 5, "I": 5, "A": 4},
        "keywords": ["quyền đặc quyền", "privileged", "admin", "root", "least privilege", "truy cập đặc quyền", "phần mềm"]
    },
    "A.8.5": {
        "code": "A.8.5",
        "title": "A.8.5 Xác thực an toàn (Secure authentication)",
        "pillar": "software",
        "category": "8. Technological controls",
        "objective": "Đảm bảo chỉ người dùng được xác thực hợp lệ mới có thể truy cập hệ thống và ứng dụng.",
        "text": "Các công nghệ và quy trình xác thực an toàn phải được thiết lập dựa trên các hạn chế về quyền truy cập và chính sách kiểm soát truy cập theo rủi ro của tổ chức.",
        "guidance": "Bắt buộc xác thực đa yếu tố (MFA) cho mọi kết nối từ bên ngoài (VPN, Email, Cloud Portal), chính sách mật khẩu mạnh và khóa tài khoản khi nhập sai nhiều lần.",
        "evidence_required": ["Cấu hình Identity Provider (Azure AD / Okta / Keycloak)", "Báo cáo kích hoạt MFA toàn doanh nghiệp", "Nhật ký xác thực đăng nhập"],
        "cia_impact": {"C": 5, "I": 4, "A": 2},
        "keywords": ["xác thực", "authentication", "mfa", "2fa", "mật khẩu", "vpn", "đăng nhập"]
    }
}


class IsoRagEngine:
    """Dynamic retrieval and compliance reasoning engine for ISO/IEC 27002:2022."""

    def __init__(self, kb: Optional[Dict[str, dict]] = None):
        self.kb = kb or ISO_27002_KB

    def get_control(self, clause_code: str) -> Optional[dict]:
        """Retrieve exact control details by standard clause code."""
        return self.kb.get(clause_code.strip().upper())

    def search(self, query: str, pillar_filter: Optional[str] = None, top_k: int = 3) -> List[dict]:
        """Perform semantic keyword search across ISO controls with relevance scoring."""
        query_tokens = [t.lower() for t in re.findall(r"\w+", query)]
        if not query_tokens:
            return []

        scored_results = []
        for code, ctrl in self.kb.items():
            if pillar_filter and ctrl.get("pillar") != pillar_filter:
                continue

            score = 0
            ctrl_text = f"{ctrl['title']} {ctrl['objective']} {ctrl['text']} {ctrl['guidance']} {' '.join(ctrl.get('keywords', []))}".lower()

            for token in query_tokens:
                # Direct code match
                if token.upper() == code:
                    score += 15
                # Keyword list match
                for kw in ctrl.get("keywords", []):
                    if token in kw:
                        score += 5
                # Body match
                if token in ctrl_text:
                    score += 2

            if score > 0:
                scored_results.append({
                    "code": code,
                    "title": ctrl["title"],
                    "pillar": ctrl["pillar"],
                    "category": ctrl["category"],
                    "score": score,
                    "objective": ctrl["objective"],
                    "text": ctrl["text"],
                    "guidance": ctrl["guidance"],
                    "evidence_required": ctrl.get("evidence_required", []),
                    "cia_impact": ctrl.get("cia_impact", {})
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def generate_remediation_guidance(self, finding_type: str, person_name: str, context: dict) -> dict:
        """Generate structured ISO-aligned remediation advice for cross-entity triad findings."""
        if "OFFBOARDING" in finding_type:
            clause = self.get_control("A.6.5")
            secondary = self.get_control("A.8.2") if "SOFTWARE" in finding_type else self.get_control("A.7.9")
            return {
                "primary_control": "A.6.5",
                "primary_title": clause["title"],
                "secondary_control": secondary["title"] if secondary else None,
                "regulatory_rationale": (
                    f"Theo ISO/IEC 27002:2022 điều khoản A.6.5 và {secondary['category'] if secondary else ''}, "
                    f"khi nhân sự '{person_name}' chấm dứt hợp đồng, toàn bộ quyền truy cập và tài sản phải được thu hồi triệt để. "
                    f"Vi phạm này tạo nguy cơ lộ lọt dữ liệu có chủ đích hoặc thất thoát thiết bị chứa dữ liệu mật."
                ),
                "actionable_steps": [
                    f"IT Admin lập tức khóa và xóa tài khoản thuộc hệ thống {context.get('unrevoked_accounts', 'SaaS/VPN/Email')}.",
                    f"Thu hồi ngay thiết bị {context.get('unreturned_devices', 'Laptop/Thẻ từ')} và lập Biên bản bàn giao có chữ ký.",
                    "Lưu giữ nhật ký thu hồi vào hồ sơ kiểm toán (Audit Trail) để đối soát tại kỳ đánh giá chứng chỉ."
                ],
                "required_evidence": clause.get("evidence_required", [])
            }

        elif "REMOTE" in finding_type:
            clause = self.get_control("A.6.7")
            tech_clause = self.get_control("A.8.1")
            return {
                "primary_control": "A.6.7",
                "primary_title": clause["title"],
                "secondary_control": tech_clause["title"],
                "regulatory_rationale": (
                    f"Theo ISO/IEC 27002:2022 điều khoản A.6.7 (Làm việc từ xa) và A.8.1 (Thiết bị đầu cuối), "
                    f"nhân viên '{person_name}' làm việc ngoài cơ sở mà không bật mã hóa ổ đĩa hoặc thiếu MFA VPN "
                    f"là vi phạm nghiêm trọng mức độ CIA C:5 / I:4."
                ),
                "actionable_steps": [
                    "Kích hoạt bắt buộc mã hóa BitLocker/FileVault qua chính sách MDM đối với thiết bị của nhân viên.",
                    "Bật chính sách Conditional Access bắt buộc MFA khi kết nối VPN từ dải IP ngoài văn phòng.",
                    "Tạm ngắt quyền kết nối từ xa cho đến khi thiết bị được kiểm định an toàn."
                ],
                "required_evidence": clause.get("evidence_required", [])
            }

        else:
            # Fallback general response
            results = self.search(finding_type, top_k=1)
            ctrl = results[0] if results else self.get_control("A.6.3")
            return {
                "primary_control": ctrl.get("code", "A.6.3"),
                "primary_title": ctrl["title"],
                "regulatory_rationale": f"Cần tuân thủ hướng dẫn ISO/IEC 27002:2022 mục {ctrl['title']}: {ctrl['objective']}",
                "actionable_steps": [ctrl["guidance"]],
                "required_evidence": ctrl.get("evidence_required", [])
            }


# Singleton instance for quick import
iso_rag = IsoRagEngine()
