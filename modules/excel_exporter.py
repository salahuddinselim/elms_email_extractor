from io import BytesIO

import pandas as pd
from openpyxl.styles import Font


def _format_worksheet(ws) -> None:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            value = "" if cell.value is None else str(cell.value)
            max_len = max(max_len, len(value))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 45)


def generate_excel_bytes(processed: dict, multi_course: bool) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if multi_course:
            processed["students"].to_excel(writer, sheet_name="All Students", index=False)
            processed["coursewise"].to_excel(writer, sheet_name="Course-wise Enrollment", index=False)
            processed.get("staff", pd.DataFrame()).to_excel(writer, sheet_name="Teachers & Staff", index=False)
            processed["trimester_summary"].to_excel(writer, sheet_name="Trimester Summary", index=False)
            processed["department_summary"].to_excel(writer, sheet_name="Department Summary", index=False)
            processed["invalid"].to_excel(writer, sheet_name="Invalid Records", index=False)
        else:
            processed["students"].to_excel(writer, sheet_name="Students", index=False)
            processed["trimester_summary"].to_excel(writer, sheet_name="Trimester Summary", index=False)
            processed["invalid"].to_excel(writer, sheet_name="Invalid Records", index=False)

        for worksheet in writer.book.worksheets:
            _format_worksheet(worksheet)

        for ws in writer.book.worksheets:
            if ws.max_row < 2:
                continue
            header_values = [cell.value for cell in ws[1]]
            if "Student ID" in header_values:
                idx = header_values.index("Student ID") + 1
                for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                    row[0].number_format = "@"

    buffer.seek(0)
    return buffer.getvalue()


def generate_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
