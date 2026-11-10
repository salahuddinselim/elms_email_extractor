import pandas as pd
import streamlit as st


def render_results(processed: dict, extraction_logs: list[dict]) -> str:
    st.subheader("Student workspace")

    metrics = processed["metrics"]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Courses Processed", metrics["total_courses_processed"])
    c2.metric("Total Records", metrics["total_participant_records"])
    c3.metric("Unique Students", metrics["unique_students"])
    c4.metric("Duplicates", metrics["duplicate_records"])
    c5.metric("Invalid IDs", metrics["invalid_student_ids"])
    c6.metric("Teachers / Staff", metrics["teachers_and_staff"])

    if extraction_logs:
        st.markdown("**Extraction Log**")
        st.dataframe(extraction_logs, width="stretch", hide_index=True)

    students_df = processed["students"]
    coursewise_df = processed.get("coursewise")

    selected_course = "All"
    course_options = ["All"]
    if coursewise_df is not None and not coursewise_df.empty and "Course ID" in coursewise_df.columns:
        course_options += sorted(coursewise_df["Course ID"].dropna().astype(str).unique().tolist())

    view_col1, view_col2, view_col3 = st.columns([1.2, 1, 1])
    view_mode = view_col1.radio(
        "Data View",
        ["Combined Students", "Course-wise Enrollment"],
        horizontal=True,
    )
    selected_course = view_col2.selectbox("Course Filter", course_options)
    sort_direction = view_col3.selectbox("Sort direction", ["Ascending", "Descending"])

    if selected_course != "All" and coursewise_df is not None and not coursewise_df.empty:
        course_count = int((coursewise_df["Course ID"].astype(str) == selected_course).sum())
        st.caption(f"Showing {course_count} participant record(s) for course {selected_course}.")

    df = students_df
    if view_mode == "Course-wise Enrollment" and coursewise_df is not None and not coursewise_df.empty:
        df = coursewise_df.copy()

    if df.empty:
        st.warning("No valid student records found.")
        return selected_course

    st.markdown("**Filter Students**")
    dep_options = ["All"] + sorted(df["Department Code"].dropna().astype(str).unique().tolist())
    year_values = pd.to_numeric(df["Admission Year"], errors="coerce").dropna().astype(int).unique().tolist()
    year_options = ["All"] + sorted(year_values)
    tri_options = ["All"] + sorted(df["Trimester"].dropna().astype(str).unique().tolist())
    semester_options = ["All"] + sorted(df["Course Semester"].dropna().astype(str).unique().tolist())

    f1, f2, f3, f4, f5 = st.columns(5)
    dep = f1.selectbox("Department", dep_options)
    year = f2.selectbox("Admission Year", year_options)
    tri = f3.selectbox("Trimester", tri_options)
    semester = f4.selectbox("Course semester", semester_options)
    course = f5.text_input("Search course / student")

    filtered = df.copy()
    if dep != "All":
        filtered = filtered[filtered["Department Code"].astype(str) == str(dep)]
    if year != "All":
        filtered = filtered[filtered["Admission Year"] == int(year)]
    if tri != "All":
        filtered = filtered[filtered["Trimester"] == tri]
    if semester != "All":
        filtered = filtered[filtered["Course Semester"].astype(str) == semester]
    if selected_course != "All":
        filtered = filtered[filtered["Course ID"].astype(str).str.contains(selected_course, case=False, regex=False)]
    if course.strip():
        query = course.strip()
        searchable = (
            filtered["Course ID"].astype(str)
            + " "
            + filtered["Course Name"].astype(str)
            + " "
            + filtered["Student ID"].astype(str)
            + " "
            + filtered["Full Name"].astype(str)
        )
        filtered = filtered[searchable.str.contains(query, case=False, regex=False)]

    sort_column = st.selectbox(
        "Sort rows by",
        [column for column in ["Student ID", "Full Name", "Course Name", "Course Semester", "Department Code"] if column in filtered.columns],
    )
    filtered = filtered.sort_values(
        by=sort_column,
        ascending=sort_direction == "Ascending",
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)

    st.caption(f"Showing {len(filtered):,} record(s)")
    st.dataframe(filtered, width="stretch", hide_index=True)

    if not processed["invalid"].empty:
        st.markdown("**Invalid Records**")
        st.dataframe(processed["invalid"], width="stretch", hide_index=True)

    staff_df = processed.get("staff")
    if staff_df is not None and not staff_df.empty:
        with st.expander("Teachers and staff without student IDs"):
            st.caption("These records are kept without fabricated IDs and are available for email composition.")
            st.dataframe(staff_df, width="stretch", hide_index=True)

    return selected_course
