students = [
{"id": "22000001", "name": "Nguyen Minh Anh", "major": "KHDL"},
{"id": "22000002", "name": "Tran Duc Long", "major": "KHDL"},
]
courses = [
{
"code": "INT2204",
"name": "Co so du lieu Web va he thong thong tin",
"capacity": 3,
"enrolled": 2,
},
{
"code": "INT2205",
"name": "Khai pha du lieu",
"capacity": 2,
"enrolled": 2,
},
]
enrollments = [
{"student_id": "22000001", "course_code": "INT2204"}
]

for course in courses:
    remaining = course["capacity"] - course["enrolled"]
    print(course["code"], "- con", remaining, "cho")

def find_course(course_code):
    for course in courses:
        if course["code"] == course_code:
            return course
    return None


def find_student(student_id):
    for student in students:
        if student["id"] == student_id:
            return student
    return None

def can_enroll(student_id, course_code):

    course = find_course(course_code)
    if course is None:
        return False, "Hoc phan khong ton tai"
    if course["enrolled"] >= course["capacity"]:
        return False, "Lop da du so luong"
    duplicated = any(
    item["student_id"] == student_id and item["course_code"] == course_code
        for item in enrollments
        )
    if duplicated:
        return False, "Sinh vien da dang ky hoc phan nay"
    return True, "Co the dang ky"

"""try:
    limit = int(input("Nhap so luong hoc phan muon hien thi: "))
    print(courses[:limit])
except ValueError:
    print("So luong phai la so nguyen")
"""
def search_courses(keyword):
    normalized = keyword.strip().lower()
    results = []
    for course in courses:
        code = course["code"].lower()
        name = course["name"].lower()
        if normalized in code or normalized in name:
            results.append(course)
        return results

# Ham dang ki tin
def enroll_student(student_id, course_code):

    # Kiểm tra học phần tồn tại hay không 
    course = find_course(course_code)
    if course is None:
        return course_code, "Hoc phan khong ton tai"

    # Kiểm tra mã sinh viên có tồn tại hay không 
    student = find_student(student_id)
    if student is None:
        return student_id,"Sinh vien khong ton tai"

    # Kiểm tra lớp còn chỗ hay không
    if course.get('capacity') == course.get('enrolled'):
        return "Lop hoc da het cho"

    # Kiểm tra sinh viên đăng kí trùng
    for enroll in enrollments:
        if enroll.get('student_id') == student_id and enroll.get('course_code') == course_code:
            return "Sinh vien dang ki trung"

    new_enroll = {"student_id": student_id , "course_code": course_code}
    enrollments.append(new_enroll)
    return("dang ki thanh cong")
# Kiểm thử
# sinh vien ko ton tai
print(enroll_student('22000003','INT2204'))
# ma lop khong ton tai
print(enroll_student('22000001','INT2207'))
# het cho
print(enroll_student('22000001','INT2205'))
# sinh dang ki trung
print(enroll_student('22000001','INT2204'))
# dang ki thanh cong
print(enroll_student('22000002','INT2204'))


