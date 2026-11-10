import streamlit as st
from components.email_ui import render_email_composer
from modules.excel_exporter import generate_csv_bytes, generate_excel_bytes


def render_export_ui(processed: dict, multi_course: bool, selected_course: str = "All"):
    st.subheader("Export center")
    st.caption("Exports use the complete extracted dataset. Apply filters above for review, then download the report you need.")

    excel_bytes = generate_excel_bytes(processed, multi_course=multi_course)
    students_csv = generate_csv_bytes(processed["students"])

    st.download_button(
        label="Download Excel Workbook",
        data=excel_bytes,
        file_name="uiu_elms_student_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        label="Download Students CSV",
        data=students_csv,
        file_name="uiu_elms_students.csv",
        mime="text/csv",
    )

    if not processed["coursewise"].empty:
        course_csv = generate_csv_bytes(processed["coursewise"])
        st.download_button(
            label="Download Course-wise Enrollment CSV",
            data=course_csv,
            file_name="uiu_elms_coursewise.csv",
            mime="text/csv",
        )

        course_options = sorted(processed["coursewise"]["Course ID"].dropna().astype(str).unique().tolist())
        if course_options:
            selected_export_course = st.selectbox(
                "Export single course",
                ["None"] + course_options,
                index=0 if selected_course == "All" else (["None"] + course_options).index(selected_course)
                if selected_course in course_options
                else 0,
                key="export_single_course",
            )
            if selected_export_course != "None":
                per_course_df = processed["coursewise"][
                    processed["coursewise"]["Course ID"].astype(str) == selected_export_course
                ]
                st.download_button(
                    label=f"Download Course {selected_export_course} CSV",
                    data=generate_csv_bytes(per_course_df),
                    file_name=f"uiu_elms_course_{selected_export_course}.csv",
                    mime="text/csv",
                )

    if not processed["invalid"].empty:
        invalid_csv = generate_csv_bytes(processed["invalid"])
        st.download_button(
            label="Download Invalid Records CSV",
            data=invalid_csv,
            file_name="uiu_elms_invalid_records.csv",
            mime="text/csv",
        )

    st.divider()
    render_email_composer(processed, selected_course=selected_course)
