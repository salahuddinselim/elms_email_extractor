import re


def validate_course_id(course_id: str) -> bool:
    return bool(re.fullmatch(r"\d{1,10}", course_id.strip()))


def parse_course_ids_input(raw_input: str) -> list[str]:
    parts = re.split(r"[\s,]+", raw_input.strip())
    ids = [part for part in parts if part]
    return list(dict.fromkeys(ids))


def validate_email(email: str) -> bool:
    if not email:
        return False
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))

