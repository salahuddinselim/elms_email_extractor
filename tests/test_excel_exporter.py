from io import BytesIO

import pandas as pd
from openpyxl import load_workbook

from modules.excel_exporter import generate_csv_bytes, generate_excel_bytes


def _sample_processed():
    students = pd.DataFrame(
        [
            {
                "Student ID": "0112230512",
                "Full Name": "Alice",
                "Email": "alice@uiu.ac.bd",
                "Department Code": "011",
                "Admission Year": 2022,
                "Trimester": "Fall",
                "Trimester Code": 3,
                "Serial Number": "0512",
                "Course ID": "7818",
            }
        ]
    )
    return {
        "students": students,
        "coursewise": students.copy(),
        "staff": pd.DataFrame(columns=students.columns),
        "invalid": pd.DataFrame(columns=["Student ID", "Error"]),
        "trimester_summary": pd.DataFrame(
            [{"Admission Year": 2022, "Trimester": "Fall", "Trimester Code": 3, "Student Count": 1}]
        ),
        "department_summary": pd.DataFrame([{"Department Code": "011", "Student Count": 1}]),
    }


def test_excel_generation_multi_course_sheets():
    data = _sample_processed()
    binary = generate_excel_bytes(data, multi_course=True)
    wb = load_workbook(BytesIO(binary))
    assert set(wb.sheetnames) == {
        "All Students",
        "Course-wise Enrollment",
        "Teachers & Staff",
        "Trimester Summary",
        "Department Summary",
        "Invalid Records",
    }


def test_csv_generation_contains_headers():
    data = _sample_processed()
    csv_data = generate_csv_bytes(data["students"]).decode("utf-8")
    assert "Student ID" in csv_data
    assert "Alice" in csv_data
