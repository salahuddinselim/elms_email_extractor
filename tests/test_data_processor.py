from modules.data_processor import process_records


def test_duplicate_removal_and_course_merge():
    records = [
        {"course_id": "7818", "student_id": "0112230512", "full_name": "A", "email": "a@uiu.ac.bd"},
        {"course_id": "7820", "student_id": "0112230512", "full_name": "A", "email": "a@uiu.ac.bd"},
        {"course_id": "7835", "student_id": "0112210123", "full_name": "B", "email": "b@uiu.ac.bd"},
    ]

    processed = process_records(records)
    students = processed["students"]

    assert len(students) == 2
    merged = students[students["Student ID"] == "0112230512"].iloc[0]
    assert merged["Course ID"] == "7818, 7820"
    assert processed["metrics"]["duplicate_records"] == 1


def test_sorting_by_trimester_order_within_year():
    records = [
        {"course_id": "1", "student_id": "0112230003", "full_name": "Fall", "email": "f@uiu.ac.bd"},
        {"course_id": "1", "student_id": "0112210001", "full_name": "Spring", "email": "s@uiu.ac.bd"},
        {"course_id": "1", "student_id": "0112220002", "full_name": "Summer", "email": "u@uiu.ac.bd"},
    ]
    processed = process_records(records)
    ordered_ids = processed["students"]["Student ID"].tolist()
    assert ordered_ids == ["0112210001", "0112220002", "0112230003"]


def test_invalid_id_is_reported():
    records = [
        {"course_id": "1", "student_id": "INVALID", "full_name": "X", "email": "x@uiu.ac.bd"}
    ]
    processed = process_records(records)
    assert len(processed["students"]) == 0
    assert len(processed["invalid"]) == 1


def test_teacher_without_id_is_kept_without_fabricated_id():
    processed = process_records(
        [
            {
                "course_id": "7818",
                "record_type": "Teacher / Staff",
                "student_id": "",
                "full_name": "Dr. Teacher",
                "email": "teacher@uiu.ac.bd",
            }
        ]
    )
    assert len(processed["students"]) == 0
    assert len(processed["staff"]) == 1
    assert processed["staff"].iloc[0]["Student ID"] == ""
    assert len(processed["invalid"]) == 0
