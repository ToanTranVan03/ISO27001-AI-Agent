"""Read blind evidence and submit only the assessor's interactive answers."""
import argparse
from getpass import getpass
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

ASSESSORS = {"tu": "vantu", "khoa": "ledangkhoa"}
ASSESSMENT_ID = "7f7c009b-bdcd-5b33-934e-15251ad2c976"
STATUSES = {"1": "Compliant", "2": "Partially Compliant",
            "3": "Non-Compliant", "4": "Insufficient Evidence"}


def choose(prompt, choices):
    while True:
        print(prompt)
        for key, value in choices.items():
            print(f"  {key}: {value}")
        answer = input("Chọn (q để dừng): ").strip()
        if answer.lower() == "q":
            raise KeyboardInterrupt
        if answer in choices:
            return choices[answer]
        print("Cần chọn rõ một mục; không có đáp án mặc định.")


def review(request, base, run_id):
    doc = request("GET", f"{base}/runs/{run_id}")
    if doc.get("state") != "finished":
        raise ValueError("Lượt chưa hoàn tất; nhờ người điều phối kiểm tra.")
    if not doc.get("blind"):
        print("Gói này đã mở kết quả hoặc đã chấm đủ. Không nộp thêm nhãn.")
        return
    if not doc.get("can_review"):
        raise ValueError(doc.get("protocol_note", "Giao thức chấm không còn hợp lệ."))
    submitted = set(doc.get("submitted_controls", []))
    pack = doc["evidence_pack"]
    total = len(pack)
    print(f"Đã nộp {len(submitted)}/{total}. Nhãn đã nộp được khóa.")
    for record in pack:
        cid = record["control_id"]
        if cid in submitted:
            continue
        print(f"\n--- {cid}: {record['name']} ---")
        print("Rubric và bằng chứng gốc (không có gợi ý kết luận):")
        print(json.dumps(record, ensure_ascii=False, indent=2))
        verdict = choose("Kết luận của chính người đánh giá:", STATUSES)
        while True:
            rationale = input("Căn cứ, tên nguồn và quan sát cụ thể (10–2000 ký tự; q để dừng): ").strip()
            if rationale.lower() == "q":
                raise KeyboardInterrupt
            if 10 <= len(rationale) <= 2000:
                break
            print("Cần tự nhập căn cứ từ 10 đến 2000 ký tự.")
        assistance = choose("Hình thức hỗ trợ khi đưa ra kết luận:", {
            "1": "unassisted", "2": "ai_assisted", "3": "team_discussion", "4": "unknown"})
        exposure = choose("Đã xem đáp án hoặc dự đoán của lượt này trước khi chấm?", {
            "1": "no", "2": "yes", "3": "unknown"})
        payload = dict(control_id=cid, expected=verdict, rationale=rationale,
                       report_sha256=doc["report_sha256"], assistance=assistance,
                       prior_exposure=exposure)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        confirm = input("Gõ NOP để nộp và khóa kết luận này (q để dừng): ").strip()
        if confirm != "NOP":
            print("Đã dừng; kết luận này chưa được nộp.")
            return
        request("POST", f"{base}/runs/{run_id}/reviews", payload)
        submitted.add(cid)
        print(f"Đã nộp {cid}. Tiến độ {len(submitted)}/{total}.")
    print(f"Đã nộp {len(submitted)}/{total}; ứng dụng sẽ tính đối chiếu theo khai báo thực tế.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=["status", "review"], default="review")
    parser.add_argument("--user", choices=ASSESSORS, default="tu")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--assessment-id", type=UUID, default=UUID(ASSESSMENT_ID))
    parser.add_argument("--run-id", type=UUID)
    args = parser.parse_args()
    if args.action == "review" and not args.run_id:
        parser.error("Cần --run-id do người điều phối cung cấp; không tự tạo/chọn lượt khác.")
    token = None

    def request(method, path, data=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = json.dumps(data).encode() if data is not None else None
        req = Request(args.url.rstrip("/") + path, data=body, headers=headers, method=method)
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    try:
        username = ASSESSORS[args.user]
        session = request("POST", "/api/auth/login", {
            "username": username, "password": getpass(f"Mật khẩu {username}: ")})
        token = session["access_token"]
        user = session["user"]
        if user["username"] != username or user["role"] != "assessor":
            raise ValueError("Cần đăng nhập đúng tài khoản assessor của người chấm.")
        print(f"Người chấm: {user['display_name']} ({username})")
        base = f"/api/assessments/{args.assessment_id}/a8"
        if args.action == "status":
            print(json.dumps(request("GET", base + "/runs"), ensure_ascii=False, indent=2))
        else:
            review(request, base, str(args.run_id))
    except (KeyboardInterrupt, EOFError):
        print("\nĐã dừng; chạy lại cùng run-id để tiếp tục các control chưa nộp.")
    except HTTPError as exc:
        print(f"API {exc.code}: {exc.read().decode('utf-8', errors='replace')}")
        return 1
    except (URLError, ValueError, KeyError) as exc:
        print(f"Không hoàn tất: {exc}")
        return 1
    finally:
        if token:
            try:
                request("POST", "/api/auth/logout")
            except (URLError, ValueError):
                print("Chưa đăng xuất được; phiên sẽ hết hạn theo cấu hình ứng dụng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
