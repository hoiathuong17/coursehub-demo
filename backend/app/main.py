from __future__ import annotations
import logging
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from .database import engine
from .schemas import DemoEnrollmentCreate, EnrollmentCreate, SectionCapacityUpdate
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
title="CourseHub API",
version="0.3.0",
description="API thuc hanh Buoi 3 - Co so du lieu Web va he thong thong tin",
)
app.add_middleware(
CORSMiddleware,
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
allow_credentials=False,
allow_methods=["GET", "POST", "DELETE"],
allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Lỗi máy chủ nội bộ: {str(exc)}"},
    )

# ==========================================
# BUỔI 4 - BÀI 1: API đọc lịch sử đăng ký
# ==========================================
@app.get("/enrollment-events")
def list_enrollment_events(
    student_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, object]]:
    conditions: list[str] = []
    parameters: dict[str, object] = {
        "limit": limit,
        "skip": skip,
    }

    if isinstance(student_id, str) and student_id.strip():
        conditions.append("student_id = :student_id")
        parameters["student_id"] = student_id.strip()

    if isinstance(event_type, str) and event_type.strip():
        conditions.append("event_type = :event_type")
        parameters["event_type"] = event_type.strip().upper()

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT id, student_id, class_section_id, event_type, source, dataset, occurred_at
        FROM enrollment_events
        {where_clause}
        ORDER BY occurred_at DESC, id DESC
        LIMIT :limit OFFSET :skip;
    """

    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()

    return [dict(row) for row in rows]
@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CourseHub API dang hoat dong"}
@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("Khong ket noi duoc co so du lieu")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong ket noi duoc co so du lieu",
        ) from exc
    return {"status": "ok", "database": "connected"}

@app.get("/courses")
def list_courses(
    q: str | None = Query(default=None, min_length=1),
) -> list[dict[str, object]]:
    sql = """
        SELECT code, name, credits
        FROM courses
    """
    parameters: dict[str, object] = {}

    if q is not None:
        keyword = q.strip().lower()
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu khoa tim kiem khong duoc rong",
            )
        sql += """
            WHERE LOWER(code) LIKE :keyword
            OR LOWER(name) LIKE :keyword
        """
        parameters["keyword"] = f"%{keyword}%"
    sql += " ORDER BY code"
    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()
    return [dict(row) for row in rows]

@app.get("/courses/{course_code}")
def get_course(course_code: str) -> dict[str, object]:
    sql = """
    SELECT code, name, credits
    FROM courses
    WHERE code = :course_code
    """
    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"course_code": course_code.upper()},
            ).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay hoc phan",
            )
    return dict(row)

@app.get("/sections")
def list_sections(
    available_only: bool = False,
) -> list[dict[str, object]]:
    sql = """
        SELECT class_id, course_code, capacity, enrolled, remaining
        FROM v_section_summary
    """
    if available_only:
        sql += " WHERE remaining > 0"
    sql += " ORDER BY class_id"
    with engine.connect() as connection:
        rows = connection.execute(text(sql)).mappings().all()
    return [dict(row) for row in rows]

@app.get("/students/{student_id}/enrollments")
def list_student_enrollments(student_id: str) -> list[dict[str, object]]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"
    enrollment_sql = """
        SELECT e.student_id,
        s.name AS student_name,
        cs.id AS class_section_id,
        c.code AS course_code,
        c.name AS course_name,
        e.registered_at
        FROM enrollments AS e
        JOIN students AS s ON s.id = e.student_id
        JOIN class_sections AS cs ON cs.id = e.class_section_id
        JOIN courses AS c ON c.code = cs.course_code
        WHERE e.student_id = :student_id
        ORDER BY cs.id
        """
    with engine.connect() as connection:
        student = connection.execute(
        text(student_sql),
        {"student_id": student_id},
        ).first()
        if student is None:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay sinh vien",
            )
        rows = connection.execute(
            text(enrollment_sql),
            {"student_id": student_id},
        ).mappings().all()
        return [dict(row) for row in rows]


# @app.post(
#     "/enrollments",
#     status_code=status.HTTP_201_CREATED,
# )
# def create_enrollment(payload: EnrollmentCreate) -> dict[str, str]:
#     student_sql = "SELECT id FROM students WHERE id = :student_id"
#     section_sql = """
#         SELECT cs.id,
#         cs.capacity,
#         COUNT(e.student_id) AS enrolled
#         FROM class_sections AS cs
#         LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
#         WHERE cs.id = :class_section_id
#         GROUP BY cs.id, cs.capacity
#     """
#     duplicate_sql = """
#         SELECT 1
#         FROM enrollments
#         WHERE student_id = :student_id
#         AND class_section_id = :class_section_id
#     """
#     insert_sql = """
#         INSERT INTO enrollments (student_id, class_section_id)
#         VALUES (:student_id, :class_section_id)
#     """
#     parameters = {
#         "student_id": payload.student_id,
#         "class_section_id": payload.class_section_id,
#     }
#     with engine.begin() as connection:
#         student = connection.execute(
#             text(student_sql),
#             {"student_id": payload.student_id},
#         ).first()
#         if student is None:
#             raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Khong tim thay sinh vien",
#         )
#         section = connection.execute(
#             text(section_sql),
#             {"class_section_id": payload.class_section_id},
#         ).mappings().first()
#         if section is None:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Khong tim thay lop hoc phan",
#         )
#         duplicated = connection.execute(
#             text(duplicate_sql),
#             parameters,
#         ).first()
#         if duplicated is not None:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Sinh vien da dang ky lop nay",
#         )
#         if int(section["enrolled"]) >= int(section["capacity"]):
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Lop hoc phan da het cho",
#         )
#         connection.execute(text(insert_sql), parameters)
#         return {
#             "message": "Dang ky thanh cong",
#             "student_id": payload.student_id,
#             "class_section_id": payload.class_section_id,
#         }

# @app.delete(
#     "/enrollments/{student_id}/{class_section_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def delete_enrollment(student_id: str, class_section_id: str) -> Response:
#     sql = """
#         DELETE FROM enrollments
#         WHERE student_id = :student_id
#         AND class_section_id = :class_section_id
#     """
#     with engine.begin() as connection:
#         result = connection.execute(
#         text(sql),
#         {
#             "student_id": student_id,
#             "class_section_id": class_section_id,
#         },
#     )
#     if result.rowcount == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Khong tim thay dang ky can huy",
#         )
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================================
# BUỔI 4 - BÀI 1: API đọc lịch sử đăng ký
# =====================================================================
@app.get("/enrollment-events")
def list_enrollment_events(
    student_id: str | None = Query(default=None, description="Lọc theo mã sinh viên"),
    event_type: str | None = Query(default=None, description="Lọc theo loại sự kiện (CREATED, CANCELLED)"),
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=20, ge=1, le=100, description="Giới hạn số bản ghi từ 1 đến 100"),
) -> list[dict[str, object]]:
    conditions: list[str] = []
    parameters: dict[str, object] = {"skip": skip, "limit": limit}

    if student_id is not None:
        conditions.append("student_id = :student_id")
        parameters["student_id"] = student_id

    if event_type is not None:
        conditions.append("event_type = :event_type")
        parameters["event_type"] = event_type

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT id, student_id, class_section_id, event_type, source, dataset, occurred_at
        FROM enrollment_events
        {where_clause}
        ORDER BY occurred_at DESC, id DESC
        LIMIT :limit OFFSET :skip;
    """

    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()

    return [dict(row) for row in rows]


# =====================================================================
# BUỔI 4 - BÀI 2: Endpoint demo kiểm thử rollback nhiều bảng
# =====================================================================
@app.post(
    "/demo/enrollments-rollback",
    status_code=status.HTTP_201_CREATED,
    tags=["Demo - Rollback Test"],
)
def demo_enrollment_with_rollback(payload: DemoEnrollmentCreate) -> dict[str, str]:
    """
    Endpoint demo phục vụ kiểm thử rollback nhiều bảng (Bài 2 - Buổi 4).
    Cố ý làm INSERT enrollment_events thất bại sau khi INSERT enrollments.
    Cả 2 câu lệnh chạy trong cùng khối `with engine.begin()`.
    Khi câu lệnh sau vi phạm ràng buộc CHECK ck_enrollment_events_type,
    toàn bộ transaction sẽ bị ROLLBACK và enrollments không bị tăng.
    """
    insert_enrollment_sql = """
        INSERT INTO enrollments (student_id, class_section_id)
        VALUES (:student_id, :class_section_id)
    """
    insert_event_sql = """
        INSERT INTO enrollment_events
            (student_id, class_section_id, event_type, source, dataset)
        VALUES
            (:student_id, :class_section_id, :event_type, 'demo', 'demo')
    """
    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
        "event_type": payload.event_type,
    }

    try:
        with engine.begin() as connection:
            # 1. Thao tác 1: Thêm vào bảng enrollments
            connection.execute(text(insert_enrollment_sql), parameters)

            # 2. Thao tác 2: Cố ý làm lỗi khi thêm vào bảng enrollment_events
            # Vi phạm ràng buộc CHECK ck_enrollment_events_type nếu event_type không hợp lệ
            connection.execute(text(insert_event_sql), parameters)

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction rolled back: Vi pham rang buoc du lieu khi ghi event",
        ) from exc

    return {
        "message": "Dang ky thanh cong (khong bi rollback)",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }


# =====================================================================
# CÁC BÀI TẬP BUỔI 3
# =====================================================================


@app.post(
    "/enrollments",
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(payload: EnrollmentCreate) -> dict[str, str]:
    student_sql = """
        SELECT id
        FROM students
        WHERE id = :student_id
    """

    lock_section_sql = """
        SELECT id, capacity
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    duplicate_sql = """
        SELECT 1
        FROM enrollments
        WHERE student_id = :student_id
          AND class_section_id = :class_section_id
    """

    count_sql = """
        SELECT COUNT(*)
        FROM enrollments
        WHERE class_section_id = :class_section_id
    """

    insert_sql = """
        INSERT INTO enrollments (student_id, class_section_id)
        VALUES (:student_id, :class_section_id)
    """

    event_sql = """
        INSERT INTO enrollment_events
            (student_id, class_section_id, event_type, source, dataset)
        VALUES
            (:student_id, :class_section_id, 'CREATED', 'api', 'demo')
    """

    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '3s'"))
            student = connection.execute(
                text(student_sql),
                {"student_id": payload.student_id},
            ).first()

            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay sinh vien",
                )

            section = connection.execute(
                text(lock_section_sql),
                {"class_section_id": payload.class_section_id},
            ).mappings().first()

            if section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay lop hoc phan",
                )

            duplicated = connection.execute(
                text(duplicate_sql),
                parameters,
            ).first()

            if duplicated is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Sinh vien da dang ky lop nay",
                )

            enrolled = connection.execute(
                text(count_sql),
                {"class_section_id": payload.class_section_id},
            ).scalar_one()

            if int(enrolled) >= int(section["capacity"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Lop hoc phan da het cho",
                )

            connection.execute(text(insert_sql), parameters)
            connection.execute(text(event_sql), parameters)

    except HTTPException:
        raise
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dang ky xung dot voi du lieu hien tai",
        ) from exc
    except Exception as exc:
        logger.exception("Loi khi dang ky hoc phan")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loi xu ly dang ky: {str(exc)}",
        ) from exc

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }
@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    student_id: str,
    class_section_id: str,
) -> Response:
    lock_section_sql = """
        SELECT id
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    delete_sql = """
        DELETE FROM enrollments
        WHERE student_id = :student_id
          AND class_section_id = :class_section_id
        RETURNING student_id
    """

    event_sql = """
        INSERT INTO enrollment_events
            (student_id, class_section_id, event_type, source, dataset)
        VALUES
            (:student_id, :class_section_id, 'CANCELLED', 'api', 'demo')
    """

    parameters = {
        "student_id": student_id,
        "class_section_id": class_section_id,
    }

    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '3s'"))
            section = connection.execute(
                text(lock_section_sql),
                {"class_section_id": class_section_id},
            ).first()

            if section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay lop hoc phan",
                )

            deleted = connection.execute(
                text(delete_sql),
                parameters,
            ).first()

            if deleted is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay dang ky can huy",
                )

            connection.execute(text(event_sql), parameters)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Loi khi huy dang ky hoc phan")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loi xu ly huy dang ky: {str(exc)}",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================================
# BUỔI 4 - BÀI 1: API đọc lịch sử đăng ký
# =====================================================================
@app.get("/enrollment-events")
def list_enrollment_events(
    student_id: str | None = Query(default=None, description="Lọc theo mã sinh viên"),
    event_type: str | None = Query(default=None, description="Lọc theo loại sự kiện (CREATED, CANCELLED)"),
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=20, ge=1, le=100, description="Giới hạn số bản ghi từ 1 đến 100"),
) -> list[dict[str, object]]:
    conditions: list[str] = []
    parameters: dict[str, object] = {"skip": skip, "limit": limit}

    if student_id is not None:
        conditions.append("student_id = :student_id")
        parameters["student_id"] = student_id

    if event_type is not None:
        conditions.append("event_type = :event_type")
        parameters["event_type"] = event_type

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT id, student_id, class_section_id, event_type, source, dataset, occurred_at
        FROM enrollment_events
        {where_clause}
        ORDER BY occurred_at DESC, id DESC
        LIMIT :limit OFFSET :skip;
    """

    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()

    return [dict(row) for row in rows]


# =====================================================================
# BUỔI 4 - BÀI 2: Endpoint demo kiểm thử rollback nhiều bảng
# =====================================================================
@app.post(
    "/demo/enrollments-rollback",
    status_code=status.HTTP_201_CREATED,
    tags=["Demo - Rollback Test"],
)
def demo_enrollment_with_rollback(payload: DemoEnrollmentCreate) -> dict[str, str]:
    """
    Endpoint demo phục vụ kiểm thử rollback nhiều bảng (Bài 2 - Buổi 4).
    Cố ý làm INSERT enrollment_events thất bại sau khi INSERT enrollments.
    Cả 2 câu lệnh chạy trong cùng khối `with engine.begin()`.
    Khi câu lệnh sau vi phạm ràng buộc CHECK ck_enrollment_events_type,
    toàn bộ transaction sẽ bị ROLLBACK và enrollments không bị tăng.
    """
    insert_enrollment_sql = """
        INSERT INTO enrollments (student_id, class_section_id)
        VALUES (:student_id, :class_section_id)
    """
    insert_event_sql = """
        INSERT INTO enrollment_events
            (student_id, class_section_id, event_type, source, dataset)
        VALUES
            (:student_id, :class_section_id, :event_type, 'demo', 'demo')
    """
    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
        "event_type": payload.event_type,
    }

    try:
        with engine.begin() as connection:
            # 1. Thao tác 1: Thêm vào bảng enrollments
            connection.execute(text(insert_enrollment_sql), parameters)

            # 2. Thao tác 2: Cố ý làm lỗi khi thêm vào bảng enrollment_events
            # Vi phạm ràng buộc CHECK ck_enrollment_events_type nếu event_type không hợp lệ
            connection.execute(text(insert_event_sql), parameters)

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction rolled back: Vi pham rang buoc du lieu khi ghi event",
        ) from exc

    return {
        "message": "Dang ky thanh cong (khong bi rollback)",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }


# =====================================================================
# CÁC BÀI TẬP BUỔI 3
# =====================================================================
# Bài 1
@app.get("/lecturers")
def list_lecturers() -> list[dict[str, object]]:
    sql = """
    SELECT id, name
    FROM lecturers
    ORDER BY id;
    """
    with engine.connect() as connection:
        rows = connection.execute(
            text(sql)
            ).mappings().all()
    
    return [dict(row) for row in rows]
# Bài 2
@app.get("/sections/{section_id}")
def get_section_detail(section_id: str) -> dict[str, object]:
    sql = """
        SELECT class_sections.id,
            class_sections.course_code,
            semesters.name,
            lecturers.name,
            class_sections.capacity,
            enrolled,
            remaining
        FROM class_sections
        JOIN v_section_summary on v_section_summary.class_id = class_sections.id
        JOIN semesters on semesters.code = semester_code
        JOIN lecturers on lecturers.id = class_sections.lecturer_id
        WHERE class_sections.id = :section_id;
    """
    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"section_id": section_id},
        ).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ma khong ton tai",
            )
    return dict(row)

# Bài 3
@app.patch("/sections/{section_id}/capacity")
def update_section_capacity(
    section_id: str, 
    payload: SectionCapacityUpdate
) -> dict[str, object]:
    sec_id = section_id.upper()
    
    with engine.begin() as connection:
        section_sql = """
            SELECT cs.id, cs.capacity, COALESCE(v.enrolled, 0) AS enrolled
            FROM class_sections AS cs
            LEFT JOIN v_section_summary AS v ON cs.id = v.class_id
            WHERE UPPER(cs.id) = :section_id
        """
        section = connection.execute(text(section_sql), {"section_id": sec_id}).mappings().first()
        
        # Lớp không tồn tại trả 404.
        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lop khong ton tai",
            )
            
        # Không cho capacity nhỏ hơn số đã đăng ký;trường hợp này trả 409.
        if payload.capacity < section["enrolled"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Suc chua ({payload.capacity}) khong duoc nho hon so sinh vien da dang ky ({section['enrolled']})",
            )
            
        # Cập nhật sức chứa mới
        update_sql = "UPDATE class_sections SET capacity = :capacity WHERE UPPER(id) = :section_id"
        connection.execute(text(update_sql), {"capacity": payload.capacity, "section_id": sec_id})
        
    return {
        "message": "Cap nhat suc chua thanh cong",
        "section_id": sec_id,
        "new_capacity": payload.capacity
    }
# Bài 4
@app.get("/courses")
def list_courses(
    q: str | None = Query(default=None, min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[dict[str, object]]:
        sql = """
           SELECT code, name, credits
           FROM courses
        """
        parameters: dict[str, object] = {"skip": skip, "limit": limit}
        if q is not None:
            keyword = q.strip().lower()
            if not keyword:
                raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail="Tu khoa tim kiem khong duoc rong",
                )
            sql += """
               WHERE LOWER(code) LIKE :keyword
               OR LOWER(name) LIKE :keyword
            """
            parameters["keyword"] = f"%{keyword}%"
        sql += " ORDER BY code ASC LIMIT :limit OFFSET :skip;"
        with engine.connect() as connection:
            rows = connection.execute(text(sql), parameters).mappings().all()
        return [dict(row) for row in rows]
   