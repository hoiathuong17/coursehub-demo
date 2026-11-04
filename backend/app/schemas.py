from pydantic import BaseModel, Field

class EnrollmentCreate(BaseModel):
    student_id: str = Field(
        min_length=8,
        max_length=8,
        examples=["22000004"],
    )
    class_section_id: str = Field(
        min_length=1,
        max_length=20,
        examples=["WEB-01"],
    )

class SectionCapacityUpdate(BaseModel):
    capacity: int = Field(
        ...,
        gt=0,
        description="Suc chua phai la so nguyen lon hon 0",
        examples=[4],
    )


class DemoEnrollmentCreate(BaseModel):
    student_id: str = Field(
        min_length=8,
        max_length=8,
        examples=["22000003"],
    )
    class_section_id: str = Field(
        min_length=1,
        max_length=20,
        examples=["WEB-02"],
    )
    event_type: str = Field(
        default="INVALID_EVENT",
        description="Loai su kien. Truyen gia tri khac CREATED va CANCELLED de gay loi CHECK constraint",
        examples=["INVALID_EVENT"],
    )
