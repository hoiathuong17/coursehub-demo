from __future__ import annotations

import requests

BASE_URL = "http://127.0.0.1:8000"
STUDENT_ID = "22000004"
SECTION_ID = "WEB-02"


def main() -> None:
    # 1. Kiem tra server hoat dong
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    health.raise_for_status()

    # 2. Xoa dang ky cu (neu co) de dam bao trang thai ban dau sach se
    requests.delete(
        f"{BASE_URL}/enrollments/{STUDENT_ID}/{SECTION_ID}",
        timeout=10,
    )

    # 3. Kiem tra so luong dang ky ban dau cua sinh vien
    initial_res = requests.get(
        f"{BASE_URL}/students/{STUDENT_ID}/enrollments",
        timeout=5,
    )
    initial_res.raise_for_status()
    initial_enrollments = initial_res.json()
    assert not any(e["class_section_id"] == SECTION_ID for e in initial_enrollments), (
        f"Sinh vien {STUDENT_ID} da dang ky {SECTION_ID} tu truoc!"
    )
    initial_count = len(initial_enrollments)
    print(f"[1] Trang thai ban dau: Sinh vien {STUDENT_ID} co {initial_count} dang ky, chua co lop {SECTION_ID}.")

    # 4. Goi endpoint demo co y gay loi (event_type = 'INVALID_TYPE' vi pham CHECK constraint)
    print("[2] Goi POST /demo/enrollments-rollback voi event_type='INVALID_TYPE'...")
    demo_res = requests.post(
        f"{BASE_URL}/demo/enrollments-rollback",
        json={
            "student_id": STUDENT_ID,
            "class_section_id": SECTION_ID,
            "event_type": "INVALID_TYPE",
        },
        timeout=10,
    )

    print(f"    Response Status: {demo_res.status_code}")
    print(f"    Response Body:   {demo_res.json()}")

    # Ky vong: Endpoint nem HTTP 400 do IntegrityError va transaction bi rollback
    assert demo_res.status_code == 400, (
        f"Ky vong status code 400 nhung nhan duoc: {demo_res.status_code}"
    )

    # 5. Xac nhan Transaction Rollback: enrollments KHONG duoc tang!
    after_res = requests.get(
        f"{BASE_URL}/students/{STUDENT_ID}/enrollments",
        timeout=5,
    )
    after_res.raise_for_status()
    after_enrollments = after_res.json()

    assert len(after_enrollments) == initial_count, (
        f"So luong dang ky bi thay doi: {len(after_enrollments)} != {initial_count}"
    )
    assert not any(e["class_section_id"] == SECTION_ID for e in after_enrollments), (
        f"Loi: Lop {SECTION_ID} van ton tai trong enrollments du transaction bi loi!"
    )

    # 6. Xac nhan enrollment_events cung khong luu su kien loi nay
    events_res = requests.get(
        f"{BASE_URL}/enrollment-events",
        params={"student_id": STUDENT_ID, "event_type": "INVALID_TYPE"},
        timeout=5,
    )
    events_res.raise_for_status()
    events = events_res.json()
    assert len(events) == 0, (
        f"Loi: enrollment_events van ton tai ban ghi le: {events}"
    )

    print("\n========================================================")
    print("PASS: Transaction rollback hoat dong chinh xac!")
    print(f"- INSERT vao enrollments da bi huy (rollback).")
    print(f"- Khong co ban ghi le nao trong enrollments hoac enrollment_events.")
    print("========================================================")


if __name__ == "__main__":
    main()

