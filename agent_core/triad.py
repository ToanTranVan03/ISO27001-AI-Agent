"""Security Triad Engine: People (Con người - Focal Point), Software (Phần mềm), Hardware (Phần cứng).

Implements multi-entity compliance monitoring and cross-entity risk propagation
mapped to ISO/IEC 27001:2022 and ISO/IEC 27002:2022 guidance.
"""

from datetime import date
from typing import Dict, List, Any, Optional
from agent_core.evidence_context import assessment_date, valid_retention

# ==============================================================================
# 1. KNOWLEDGE BASE: ISO/IEC 27002:2022 STANDARD CITATIONS & MAPPING
# ==============================================================================
ISO_27002_CITATIONS = {
    'A.6.1': {
        'pillar': 'people',
        'title': 'Thẩm tra lý lịch nhân sự (Screening)',
        'clause': 'ISO/IEC 27002:2022 Clause 6.1',
        'objective': 'Đảm bảo ứng viên và nhân sự đáp ứng tính tin cậy và liêm chính trước khi tiếp cận tài sản thông tin.',
        'cia_impact': {'C': 3, 'I': 3, 'A': 1},
        'guidance': 'Tiến hành xác minh lý lịch nhân sự tỷ lệ thuận với cấp độ phân loại dữ liệu và vị trí công việc tiếp cận.'
    },
    'A.6.2': {
        'pillar': 'people',
        'title': 'Điều khoản và điều kiện lao động',
        'clause': 'ISO/IEC 27002:2022 Clause 6.2',
        'objective': 'Ràng buộc pháp lý nghĩa vụ an toàn thông tin trong hợp đồng lao động giữa nhân sự và tổ chức.',
        'cia_impact': {'C': 4, 'I': 2, 'A': 1},
        'guidance': 'Hợp đồng phải quy định rõ trách nhiệm bảo mật trước, trong và sau thời hạn làm việc tại doanh nghiệp.'
    },
    'A.6.3': {
        'pillar': 'people',
        'title': 'Nhận thức, giáo dục và đào tạo ATTT',
        'clause': 'ISO/IEC 27002:2022 Clause 6.3',
        'objective': 'Đảm bảo nhân sự nhận thức được rủi ro ATTT, các mối đe dọa và thực hiện đúng chính sách tổ chức.',
        'cia_impact': {'C': 4, 'I': 4, 'A': 3},
        'guidance': 'Đào tạo định kỳ tối thiểu hàng năm, kiểm tra đánh giá nhận thức và theo dõi nhân sự chưa đạt để tái đào tạo.'
    },
    'A.6.4': {
        'pillar': 'people',
        'title': 'Quy trình kỷ luật và xử lý vi phạm',
        'clause': 'ISO/IEC 27002:2022 Clause 6.4',
        'objective': 'Thiết lập quy trình minh bạch nhằm xử lý các hành vi vi phạm chính sách an toàn thông tin.',
        'cia_impact': {'C': 3, 'I': 3, 'A': 2},
        'guidance': 'Phổ biến quy trình kỷ luật đến toàn thể nhân viên; lưu trữ xác nhận đã tiếp nhận thông tin.'
    },
    'A.6.5': {
        'pillar': 'cross_pillar',
        'sub_pillars': ['people', 'software', 'hardware'],
        'title': 'Trách nhiệm khi thôi việc hoặc thay đổi công tác',
        'clause': 'ISO/IEC 27002:2022 Clause 6.5',
        'objective': 'Bảo vệ tài sản thông tin khi nhân sự chấm dứt hợp đồng hoặc chuyển đổi vị trí công việc.',
        'cia_impact': {'C': 5, 'I': 4, 'A': 3},
        'guidance': 'Ngay khi nghỉ việc: thu hồi toàn bộ quyền truy cập phần mềm/IAM và nhận lại toàn bộ tài sản phần cứng (laptop, thẻ).'
    },
    'A.6.6': {
        'pillar': 'people',
        'title': 'Thỏa thuận bảo mật thông tin (NDA)',
        'clause': 'ISO/IEC 27002:2022 Clause 6.6',
        'objective': 'Ràng buộc trách nhiệm giữ bí mật thông tin nhạy cảm của tổ chức và khách hàng.',
        'cia_impact': {'C': 5, 'I': 2, 'A': 1},
        'guidance': 'Ký kết NDA trước khi cấp bất kỳ tài khoản truy cập hệ thống thông tin nội bộ nào.'
    },
    'A.6.7': {
        'pillar': 'cross_pillar',
        'sub_pillars': ['people', 'hardware', 'software'],
        'title': 'Làm việc từ xa (Remote Working)',
        'clause': 'ISO/IEC 27002:2022 Clause 6.7',
        'objective': 'Bảo vệ thông tin được truy cập, xử lý hoặc lưu trữ tại các địa điểm làm việc từ xa ngoài trụ sở.',
        'cia_impact': {'C': 5, 'I': 4, 'A': 3},
        'guidance': 'Thiết bị phần cứng phải mã hóa ổ đĩa toàn phần; kết nối phần mềm qua VPN phải bắt buộc xác thực đa yếu tố (MFA).'
    },
    'A.6.8': {
        'pillar': 'people',
        'title': 'Báo cáo sự kiện an toàn thông tin',
        'clause': 'ISO/IEC 27002:2022 Clause 6.8',
        'objective': 'Đảm bảo các sự kiện và điểm yếu ATTT được thông báo kịp thời cho đội ngũ ứng phó sự cố.',
        'cia_impact': {'C': 4, 'I': 4, 'A': 4},
        'guidance': 'Thiết lập kênh báo cáo dễ tiếp cận; hướng dẫn nhân viên cách nhận biết email lừa đảo và sự cố bất thường.'
    },
    # Liên kết Phần mềm (Software Controls A.8)
    'A.8.2': {
        'pillar': 'software',
        'title': 'Quyền truy cập đặc quyền (Privileged access rights)',
        'clause': 'ISO/IEC 27002:2022 Clause 8.2',
        'objective': 'Hạn chế và kiểm soát chặt chẽ việc phân bổ quyền quản trị đặc quyền.',
        'cia_impact': {'C': 5, 'I': 5, 'A': 5},
        'guidance': 'Chỉ cấp quyền quản trị theo nguyên tắc đặc quyền tối thiểu (Least Privilege) và rà soát định kỳ.'
    },
    'A.8.3': {
        'pillar': 'software',
        'title': 'Hạn chế truy cập thông tin (Information access restriction)',
        'clause': 'ISO/IEC 27002:2022 Clause 8.3',
        'objective': 'Hạn chế quyền truy cập vào thông tin và hệ thống theo nguyên tắc cần biết (Need-to-know).',
        'cia_impact': {'C': 5, 'I': 4, 'A': 3},
        'guidance': 'Rà soát và thu hồi quyền truy cập không còn phù hợp khi nhân sự luân chuyển vai trò.'
    },
    'A.8.5': {
        'pillar': 'software',
        'title': 'Xác thực an toàn (Secure authentication)',
        'clause': 'ISO/IEC 27002:2022 Clause 8.5',
        'objective': 'Đảm bảo định danh và xác thực an toàn người dùng trước khi cấp quyền truy cập mạng.',
        'cia_impact': {'C': 5, 'I': 4, 'A': 3},
        'guidance': 'Bắt buộc áp dụng MFA cho toàn bộ truy cập từ xa và các tài khoản quản trị đặc quyền.'
    },
    # Liên kết Phần cứng (Hardware Controls A.7 & A.8.1)
    'A.8.1': {
        'pillar': 'hardware',
        'title': 'Thiết bị đầu cuối của người dùng (User endpoint devices)',
        'clause': 'ISO/IEC 27002:2022 Clause 8.1',
        'objective': 'Bảo vệ thiết bị đầu cuối chống lại nguy cơ bị truy cập trái phép hoặc đánh cắp dữ liệu.',
        'cia_impact': {'C': 5, 'I': 4, 'A': 3},
        'guidance': 'Áp dụng mã hóa ổ đĩa (BitLocker), cấu hình khóa màn hình tự động và bảo vệ vật lý thiết bị.'
    },
    'A.7.7': {
        'pillar': 'hardware',
        'title': 'Bàn làm việc sạch và màn hình sạch (Clear desk and clear screen)',
        'clause': 'ISO/IEC 27002:2022 Clause 7.7',
        'objective': 'Giảm nguy cơ tiếp cận trái phép tài liệu và thiết bị tại không gian làm việc.',
        'cia_impact': {'C': 4, 'I': 2, 'A': 1},
        'guidance': 'Khóa màn hình máy tính khi rời vị trí; không để tài liệu nhạy cảm trên bàn làm việc trong văn phòng.'
    },
    'A.7.9': {
        'pillar': 'hardware',
        'title': 'Bảo vệ tài sản ngoài cơ sở (Security of assets off-premises)',
        'clause': 'ISO/IEC 27002:2022 Clause 7.9',
        'objective': 'Bảo vệ an toàn cho thiết bị và tài sản của tổ chức khi được mang ra ngoài trụ sở.',
        'cia_impact': {'C': 4, 'I': 3, 'A': 4},
        'guidance': 'Lập danh mục theo dõi thiết bị được cấp phát và thu hồi nguyên trạng khi chấm dứt hợp đồng.'
    }
}

# ==============================================================================
# 2. TRIAD RISK SCORER: LIKELIHOOD x IMPACT (CIA TRIPLE)
# ==============================================================================
ROLE_SENSITIVITY = {
    'IT': 1.4,       # Tiếp cận hạ tầng kỹ thuật
    'Finance': 1.3,  # Dữ liệu tài chính, tiền lương
    'Ops': 1.1,      # Vận hành nội bộ
    'Sales': 1.0     # Thông tin khách hàng, kinh doanh
}

def calculate_triad_risk(control_id: str, department: str, severity: str = 'violation') -> Dict[str, Any]:
    """Calculates quantitative risk score using Likelihood x Impact (CIA)."""
    citation = ISO_27002_CITATIONS.get(control_id, {})
    cia = citation.get('cia_impact', {'C': 3, 'I': 3, 'A': 2})
    dept_weight = ROLE_SENSITIVITY.get(department, 1.0)
    
    # Impact score: Average of CIA adjusted by role/department sensitivity
    base_impact = (cia['C'] * 0.5 + cia['I'] * 0.3 + cia['A'] * 0.2)
    impact = round(min(5.0, base_impact * dept_weight), 1)
    
    # Likelihood based on violation type
    likelihood = 4.5 if severity == 'violation' else 3.0 if severity == 'missing' else 1.0
    
    risk_score = round(likelihood * impact, 1)  # Range 1.0 to 25.0
    
    if risk_score >= 18.0:
        risk_level = 'Rất cao (Critical)'
    elif risk_score >= 12.0:
        risk_level = 'Cao (High)'
    elif risk_score >= 6.0:
        risk_level = 'Trung bình (Medium)'
    else:
        risk_level = 'Thấp (Low)'
        
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'likelihood': likelihood,
        'impact': impact,
        'cia': cia
    }

# ==============================================================================
# 3. CROSS-ENTITY RISK PROPAGATION & TRIAD ANALYSIS
# ==============================================================================
def analyze_triad(enterprise: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes the enterprise across the 3 pillars: People, Software, Hardware.
    
    Identifies cross-entity risk chains where a change in People impacts
    Software permissions or Hardware assets.
    """
    people = enterprise.get('people', [])
    accounts = enterprise.get('accounts', [])
    devices = enterprise.get('devices', [])
    today = assessment_date(enterprise)
    
    people_issues = []
    software_issues = []
    hardware_issues = []
    cross_entity_risks = []
    
    people_by_id = {p['id']: p for p in people}
    accounts_by_person = {}
    for a in accounts:
        accounts_by_person.setdefault(a['person_id'], []).append(a)
    devices_by_person = {}
    for d in devices:
        devices_by_person.setdefault(d['person_id'], []).append(d)
        
    for person in people:
        pid = person['id']
        dept = person.get('department', 'Sales')
        p_accounts = accounts_by_person.get(pid, [])
        p_devices = devices_by_person.get(pid, [])
        
        # -------------------------------------------------------------
        # TRỤ CỘT 1: CON NGƯỜI (A.6 People Controls)
        # -------------------------------------------------------------
        # Đào tạo ATTT
        if person.get('training_complete') is False or person.get('training_passed') is False:
            people_issues.append({
                'person_id': pid, 'pillar': 'people', 'control_id': 'A.6.3',
                'issue': 'Chưa hoàn thành hoặc chưa đạt bài kiểm tra nhận thức ATTT',
                'risk': calculate_triad_risk('A.6.3', dept, 'violation')
            })
        elif person.get('training_passed') is None or person.get('training_complete') is None:
            people_issues.append({
                'person_id': pid, 'pillar': 'people', 'control_id': 'A.6.3',
                'issue': 'Thiếu bằng chứng xác thực hoàn tất đào tạo ATTT',
                'risk': calculate_triad_risk('A.6.3', dept, 'missing')
            })
            
        # Thỏa thuận bảo mật NDA
        if person.get('nda_signed') is False or person.get('terms_signed') is False:
            people_issues.append({
                'person_id': pid, 'pillar': 'people', 'control_id': 'A.6.6',
                'issue': 'Chưa ký thỏa thuận bảo mật NDA hoặc điều khoản lao động',
                'risk': calculate_triad_risk('A.6.6', dept, 'violation')
            })
            # Cross-entity: Premature software accounts
            active_accs = [a['id'] for a in p_accounts if a.get('active')]
            if active_accs:
                cross_entity_risks.append({
                    'person_id': pid,
                    'type': 'ONBOARDING_PREMATURE_SOFTWARE',
                    'title': 'Cấp quyền phần mềm trước khi hoàn tất cam kết bảo mật',
                    'source_pillar': 'people',
                    'target_pillar': 'software',
                    'controls': ['A.6.6', 'A.8.2'],
                    'detail': f'Nhân sự chưa ký NDA nhưng đã kích hoạt {len(active_accs)} tài khoản: {", ".join(active_accs)}.',
                    'risk': calculate_triad_risk('A.6.6', dept, 'violation')
                })

        # -------------------------------------------------------------
        # TRỤ CỘT 2: PHẦN MỀM (A.8 Technological Controls & IAM)
        # -------------------------------------------------------------
        # Rà soát quyền khi đổi vai trò
        if person.get('access_review_required') and person.get('status') == 'active':
            unreviewed = [a['id'] for a in p_accounts if not a.get('role_reviewed')]
            if unreviewed:
                software_issues.append({
                    'person_id': pid, 'pillar': 'software', 'control_id': 'A.8.3',
                    'issue': f'Đổi vai trò nhưng chưa rà soát quyền cho {len(unreviewed)} tài khoản',
                    'risk': calculate_triad_risk('A.8.3', dept, 'violation')
                })
                cross_entity_risks.append({
                    'person_id': pid,
                    'type': 'ROLE_CHANGE_UNREVIEWED_SOFTWARE',
                    'title': 'Chuyển vai trò chưa rà soát quyền phần mềm cũ',
                    'source_pillar': 'people',
                    'target_pillar': 'software',
                    'controls': ['A.6.5', 'A.8.3'],
                    'detail': f'Nhân sự chuyển sang vai trò {person.get("role")} nhưng quyền tài khoản cũ ({", ".join(unreviewed)}) chưa được thu hồi hoặc chuẩn hóa theo Least Privilege.',
                    'risk': calculate_triad_risk('A.8.3', dept, 'violation')
                })
                
        # -------------------------------------------------------------
        # TRỤ CỘT 3: PHẦN CỨNG (A.7 Physical & A.8.1 Endpoints)
        # -------------------------------------------------------------
        # Làm việc từ xa: Kết nối Phần cứng + Phần mềm
        if person.get('remote') and person.get('status') != 'terminated':
            unencrypted_laptops = [d['id'] for d in p_devices if not d.get('encrypted')]
            if unencrypted_laptops:
                hardware_issues.append({
                    'person_id': pid, 'pillar': 'hardware', 'control_id': 'A.8.1',
                    'issue': f'Laptop làm việc từ xa chưa mã hóa: {", ".join(unencrypted_laptops)}',
                    'risk': calculate_triad_risk('A.8.1', dept, 'violation')
                })
            
            insecure_vpn = [a['id'] for a in p_accounts if a.get('system') == 'VPN' and a.get('active') and not a.get('mfa')]
            if insecure_vpn:
                software_issues.append({
                    'person_id': pid, 'pillar': 'software', 'control_id': 'A.8.5',
                    'issue': f'Tài khoản VPN chưa bật xác thực đa yếu tố MFA: {", ".join(insecure_vpn)}',
                    'risk': calculate_triad_risk('A.8.5', dept, 'violation')
                })
                
            if unencrypted_laptops or insecure_vpn:
                cross_entity_risks.append({
                    'person_id': pid,
                    'type': 'REMOTE_WORK_VULNERABILITY',
                    'title': 'Lỗ hổng làm việc từ xa lan truyền Phần cứng & Phần mềm',
                    'source_pillar': 'people',
                    'target_pillar': 'hardware & software',
                    'controls': ['A.6.7', 'A.8.1', 'A.8.5'],
                    'detail': f'Nhân sự làm từ xa nhưng {len(unencrypted_laptops)} thiết bị chưa mã hóa và {len(insecure_vpn)} kết nối VPN thiếu MFA.',
                    'risk': calculate_triad_risk('A.6.7', dept, 'violation')
                })
                
        # -------------------------------------------------------------
        # CHU KỲ NGHỈ VIỆC (OFFBOARDING): CON NGƯỜI -> PHẦN MỀM + PHẦN CỨNG
        # -------------------------------------------------------------
        if person.get('status') == 'terminated':
            # Kiểm tra phần mềm: Còn tài khoản mở không có ngoại lệ
            unrevoked_accounts = [
                a for a in p_accounts 
                if a.get('active') and not valid_retention(a, today)
            ]
            if unrevoked_accounts:
                software_issues.append({
                    'person_id': pid, 'pillar': 'software', 'control_id': 'A.8.2',
                    'issue': f'Nghỉ việc nhưng còn {len(unrevoked_accounts)} tài khoản chưa đóng',
                    'risk': calculate_triad_risk('A.8.2', dept, 'violation')
                })
                cross_entity_risks.append({
                    'person_id': pid,
                    'type': 'OFFBOARDING_UNREVOKED_SOFTWARE',
                    'title': 'Nhân viên nghỉ việc chưa thu hồi tài khoản phần mềm',
                    'source_pillar': 'people',
                    'target_pillar': 'software',
                    'controls': ['A.6.5', 'A.8.2'],
                    'detail': f'Nhân sự đã thôi việc nhưng {len(unrevoked_accounts)} tài khoản vẫn kích hoạt: {", ".join(a["id"] for a in unrevoked_accounts)}.',
                    'risk': calculate_triad_risk('A.6.5', dept, 'violation')
                })
                
            # Kiểm tra phần cứng: Laptop chưa trả
            unreturned_devices = [d for d in p_devices if not d.get('returned')]
            if unreturned_devices:
                hardware_issues.append({
                    'person_id': pid, 'pillar': 'hardware', 'control_id': 'A.7.9',
                    'issue': f'Nghỉ việc nhưng chưa thu hồi {len(unreturned_devices)} thiết bị laptop',
                    'risk': calculate_triad_risk('A.7.9', dept, 'violation')
                })
                cross_entity_risks.append({
                    'person_id': pid,
                    'type': 'OFFBOARDING_UNRETURNED_HARDWARE',
                    'title': 'Nhân viên nghỉ việc chưa bàn giao thiết bị phần cứng',
                    'source_pillar': 'people',
                    'target_pillar': 'hardware',
                    'controls': ['A.6.5', 'A.7.9', 'A.8.1'],
                    'detail': f'Nhân sự đã thôi việc nhưng chưa thu hồi thiết bị vật lý: {", ".join(d["id"] for d in unreturned_devices)}.',
                    'risk': calculate_triad_risk('A.6.5', dept, 'violation')
                })

    # Summary calculations
    from agent_core.iso_rag import iso_rag
    for r in cross_entity_risks:
        p_obj = people_by_id.get(r['person_id'], {})
        p_name = f"{p_obj.get('name', r['person_id'])} ({r['person_id']})"
        r['iso_guidance'] = iso_rag.generate_remediation_guidance(
            finding_type=r['type'],
            person_name=p_name,
            context={'detail': r.get('detail', '')}
        )

    max_risk = max([r['risk']['risk_score'] for r in cross_entity_risks] or [0.0])
    avg_risk = round(sum(r['risk']['risk_score'] for r in cross_entity_risks) / max(1, len(cross_entity_risks)), 1)
    
    return {
        'focal_pillar': 'people',
        'pillars': {
            'people': {
                'title': 'Con người (People - A.6 Controls)',
                'total_records': len(people),
                'active_employees': sum(1 for p in people if p.get('status') == 'active'),
                'terminated_employees': sum(1 for p in people if p.get('status') == 'terminated'),
                'issue_count': len(people_issues),
                'issues': people_issues
            },
            'software': {
                'title': 'Phần mềm (Software - A.8 & IAM Controls)',
                'total_accounts': len(accounts),
                'active_accounts': sum(1 for a in accounts if a.get('active')),
                'issue_count': len(software_issues),
                'issues': software_issues
            },
            'hardware': {
                'title': 'Phần cứng (Hardware - A.7 & A.8.1 Controls)',
                'total_devices': len(devices),
                'active_devices': sum(1 for d in devices if not d.get('returned')),
                'issue_count': len(hardware_issues),
                'issues': hardware_issues
            }
        },
        'cross_entity_risks': cross_entity_risks,
        'metrics': {
            'total_cross_risks': len(cross_entity_risks),
            'max_risk_score': max_risk,
            'avg_risk_score': avg_risk,
            'risk_level': 'Rất cao (Critical)' if max_risk >= 18.0 else 'Cao (High)' if max_risk >= 12.0 else 'Trung bình (Medium)' if max_risk >= 6.0 else 'Thấp (Low)'
        },
        'iso_citations': ISO_27002_CITATIONS
    }
