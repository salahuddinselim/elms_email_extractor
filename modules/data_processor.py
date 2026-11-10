from collections import defaultdict

import pandas as pd

from modules.student_parser import parse_student_id
from modules.validators import validate_email


EXPECTED_COLUMNS = [
    "Record Type",
    "Student ID",
    "Full Name",
    "Email",
    "Course Name",
    "Course Semester",
    "Department Code",
    "Admission Year",
    "Trimester",
    "Trimester Code",
    "Serial Number",
    "Course ID",
]


def _base_student_row(raw: dict, parsed: dict) -> dict:
    return {
        "Record Type": "Student",
        "Student ID": parsed["student_id"],
        "Full Name": raw.get("full_name", "").strip(),
        "Email": raw.get("email", "").strip(),
        "Course Name": raw.get("course_name", "").strip(),
        "Course Semester": raw.get("course_semester", "").strip(),
        "Department Code": parsed["department_code"],
        "Admission Year": parsed["admission_year"],
        "Trimester": parsed["trimester"],
        "Trimester Code": parsed["trimester_code"],
        "Serial Number": parsed["serial_number"],
    }


def process_records(records: list[dict]) -> dict:
    valid_rows = []
    staff_rows = []
    invalid_rows = []
    coursewise_rows = []
    dedup_map: dict[str, dict] = {}
    course_sets: dict[str, set[str]] = defaultdict(set)
    duplicate_count = 0

    for record in records:
        student_id = str(record.get("student_id", "")).strip()
        full_name = str(record.get("full_name", "")).strip()
        email = str(record.get("email", "")).strip()
        course_id = str(record.get("course_id", "")).strip()

        base_coursewise = {
            "Record Type": str(record.get("record_type", "")).strip() or ("Teacher / Staff" if not student_id else "Student"),
            "Student ID": student_id,
            "Full Name": full_name,
            "Email": email,
            "Course Name": str(record.get("course_name", "")).strip(),
            "Course Semester": str(record.get("course_semester", "")).strip(),
            "Department Code": "",
            "Admission Year": "",
            "Trimester": "",
            "Trimester Code": "",
            "Serial Number": "",
            "Course ID": course_id,
        }

        if not student_id:
            coursewise_rows.append(base_coursewise)
            if email and validate_email(email):
                staff_rows.append(base_coursewise)
            else:
                invalid_rows.append(
                    {
                        "Student ID": "",
                        "Full Name": full_name,
                        "Email": email,
                        "Course ID": course_id,
                        "Error": "Missing student ID and invalid or missing email",
                    }
                )
            continue

        parsed_obj, parse_error = parse_student_id(student_id)
        if parse_error:
            coursewise_rows.append(base_coursewise)
            invalid_rows.append(
                {
                    "Student ID": student_id,
                    "Full Name": full_name,
                    "Email": email,
                    "Course ID": course_id,
                    "Error": parse_error,
                }
            )
            continue

        if email and not validate_email(email):
            parsed_preview = parsed_obj.__dict__
            partial_row = {
                **base_coursewise,
                "Department Code": parsed_preview["department_code"],
                "Admission Year": parsed_preview["admission_year"],
                "Trimester": parsed_preview["trimester"],
                "Trimester Code": parsed_preview["trimester_code"],
                "Serial Number": parsed_preview["serial_number"],
            }
            coursewise_rows.append(partial_row)
            invalid_rows.append(
                {
                    "Student ID": student_id,
                    "Full Name": full_name,
                    "Email": email,
                    "Course ID": course_id,
                    "Error": "Invalid email format",
                }
            )
            continue

        parsed = parsed_obj.__dict__
        student_key = parsed["student_id"]

        coursewise_row = _base_student_row(record, parsed)
        coursewise_row["Course ID"] = course_id
        coursewise_rows.append(coursewise_row)

        if student_key in dedup_map:
            duplicate_count += 1
        else:
            dedup_map[student_key] = _base_student_row(record, parsed)
        course_sets[student_key].add(course_id)

    for student_id, base in dedup_map.items():
        courses = sorted(course_sets[student_id])
        merged = dict(base)
        merged["Course ID"] = ", ".join(courses)
        if len(courses) > 1:
            merged["Course Name"] = "Multiple courses"
            merged["Course Semester"] = "Multiple semesters"
        valid_rows.append(merged)

    students_df = pd.DataFrame(valid_rows, columns=EXPECTED_COLUMNS)
    coursewise_df = pd.DataFrame(coursewise_rows, columns=EXPECTED_COLUMNS)
    staff_df = pd.DataFrame(staff_rows, columns=EXPECTED_COLUMNS)
    invalid_df = pd.DataFrame(invalid_rows)

    if not students_df.empty:
        students_df = students_df.sort_values(
            by=["Admission Year", "Trimester Code", "Department Code", "Serial Number"],
            ascending=[True, True, True, True],
        ).reset_index(drop=True)

    trimester_summary = (
        students_df.groupby(["Admission Year", "Trimester", "Trimester Code"], dropna=False)
        .size()
        .reset_index(name="Student Count")
        if not students_df.empty
        else pd.DataFrame(columns=["Admission Year", "Trimester", "Trimester Code", "Student Count"])
    )

    if not trimester_summary.empty:
        trimester_summary = trimester_summary.sort_values(
            by=["Admission Year", "Trimester Code"], ascending=[True, True]
        ).reset_index(drop=True)

    department_summary = (
        students_df.groupby(["Department Code"], dropna=False)
        .size()
        .reset_index(name="Student Count")
        if not students_df.empty
        else pd.DataFrame(columns=["Department Code", "Student Count"])
    )

    return {
        "students": students_df,
        "coursewise": coursewise_df,
        "staff": staff_df,
        "invalid": invalid_df,
        "trimester_summary": trimester_summary,
        "department_summary": department_summary,
        "metrics": {
            "total_courses_processed": len({str(r.get("course_id", "")).strip() for r in records if r.get("course_id")}),
            "total_participant_records": len(records),
            "unique_students": len(students_df),
            "duplicate_records": duplicate_count,
            "invalid_student_ids": len(invalid_df),
            "teachers_and_staff": len(staff_df),
        },
    }
