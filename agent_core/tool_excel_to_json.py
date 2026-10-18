import pandas as pd
import json
import os

def convert_excel_to_rubric():
    # 1. Đường dẫn file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(base_dir, "docs", "ISO_27001_Rubric.xlsx")
    json_path = os.path.join(base_dir, "docs", "compliance_rubrics.json")

    print(f"Đang đọc dữ liệu từ: {excel_path}...")
    
    # 2. Đọc file Excel
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file Excel. Vui lòng tạo file ISO_27001_Rubric.xlsx trong thư mục docs/")
        return

    # 3. Chuyển đổi thành Dictionary
    rubric_dict = {}
    for index, row in df.iterrows():
        control_id = str(row['Control_ID']).strip()
        if pd.isna(row['Control_ID']): continue
        
        rubric_dict[control_id] = {
            "control_name": str(row['Control_Name']).strip(),
            "Compliant": str(row['Compliant']).strip(),
            "Partially Compliant": str(row['Partially_Compliant']).strip(),
            "Non-Compliant": str(row['Non_Compliant']).strip()
        }

    # 4. Xuất ra file JSON cho AI đọc
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rubric_dict, f, ensure_ascii=False, indent=2)
        
    print(f"Thành công! Đã chuyển đổi {len(rubric_dict)} Controls ra file: {json_path}")

if __name__ == "__main__":
    convert_excel_to_rubric()