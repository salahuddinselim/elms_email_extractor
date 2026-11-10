from dataclasses import dataclass


TRIMESTER_MAP = {
    "1": "Spring",
    "2": "Summer",
    "3": "Fall",
}


@dataclass
class ParsedStudentID:
    student_id: str
    department_code: str
    admission_year: int
    trimester: str
    trimester_code: int
    serial_number: str


def parse_student_id(student_id: str) -> tuple[ParsedStudentID | None, str | None]:
    cleaned = (student_id or "").strip()

    if len(cleaned) != 10 or not cleaned.isdigit():
        return None, "Student ID must be exactly 10 digits"

    department_code = cleaned[:3]
    year_2d = cleaned[3:5]
    trimester_code = cleaned[5]
    serial_number = cleaned[6:]

    trimester = TRIMESTER_MAP.get(trimester_code)
    if trimester is None:
        return None, f"Invalid trimester code: {trimester_code}"

    year_num = int(year_2d)
    admission_year = 2000 + year_num

    parsed = ParsedStudentID(
        student_id=cleaned,
        department_code=department_code,
        admission_year=admission_year,
        trimester=trimester,
        trimester_code=int(trimester_code),
        serial_number=serial_number,
    )
    return parsed, None

