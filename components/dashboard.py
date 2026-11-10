import streamlit as st
from modules.validators import parse_course_ids_input, validate_course_id


def render_dashboard() -> tuple[str, list[str], bool]:
    st.subheader("Dashboard")
    mode = st.radio("Extraction Mode", ["Single Course", "Multiple Courses"], horizontal=True)
    raw_input = st.text_area(
        "Course ID(s)",
        placeholder="Single: 7818\nMultiple: 7818, 7820, 7835",
        help="Enter IDs using commas, spaces, or new lines.",
    )
    clicked = st.button("Start Extraction", type="primary")

    course_ids = parse_course_ids_input(raw_input)
    invalids = [cid for cid in course_ids if not validate_course_id(cid)]

    if invalids:
        st.error(f"Invalid course IDs: {', '.join(invalids)}")
    elif course_ids:
        st.caption(f"Parsed {len(course_ids)} course ID(s): {', '.join(course_ids)}")

    if mode == "Single Course" and len(course_ids) > 1:
        st.warning("Single Course mode expects exactly one course ID.")

    return mode, course_ids, clicked and not invalids

