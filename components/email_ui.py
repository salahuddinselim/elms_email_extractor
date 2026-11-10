from urllib.parse import quote

import streamlit as st


DEFAULT_SUBJECT = "ELMS group invitation"
DEFAULT_BODY = """Hello everyone,

I am sharing the following group invitation or course update:

[Paste your invitation link or message here]

Course: {course_name}

Best regards,
[Your name]
"""


def render_email_composer(processed: dict, selected_course: str = "All") -> None:
    coursewise = processed.get("coursewise")
    if coursewise is None or coursewise.empty:
        return

    st.subheader("Group email composer")
    st.caption("Create one email for a course section. The app prepares a mailto link; it never sends email or stores your message.")

    available_courses = sorted(coursewise["Course ID"].dropna().astype(str).unique().tolist())
    default_course_index = (
        available_courses.index(selected_course)
        if selected_course in available_courses
        else 0
    )
    course_id = st.selectbox("Course section", available_courses, index=default_course_index)
    section = coursewise[coursewise["Course ID"].astype(str) == course_id].copy()
    students = section[
        (section["Record Type"] == "Student")
        & section["Email"].astype(str).str.strip().ne("")
    ]
    staff = section[
        (section["Record Type"] == "Teacher / Staff")
        & section["Email"].astype(str).str.strip().ne("")
    ]

    recipient_group = st.radio(
        "Recipients",
        ["Students", "Students and teachers", "Teachers only"],
        horizontal=True,
    )
    if recipient_group == "Teachers only":
        recipients = staff["Email"].drop_duplicates().tolist()
    elif recipient_group == "Students and teachers":
        recipients = (
            section[section["Email"].astype(str).str.strip().ne("")]["Email"]
            .drop_duplicates()
            .tolist()
        )
    else:
        recipients = students["Email"].drop_duplicates().tolist()

    subject = st.text_input("Subject", value=DEFAULT_SUBJECT)
    body = st.text_area(
        "Message template",
        value=DEFAULT_BODY.format(
            course_name=str(section["Course Name"].dropna().iloc[0])
            if not section["Course Name"].dropna().empty
            else course_id
        ),
        height=220,
    )

    cc = ",".join(recipients)
    st.caption(f"{len(recipients)} recipient(s) will be added to CC.")
    if len(cc) > 1800:
        st.warning("This section has many recipients. Your email client may reject a very long mailto link; use the CC list below instead.")
    st.text_area("CC list", value=cc, height=90, key=f"cc_list_{course_id}")

    mailto_url = f"mailto:?cc={quote(cc)}&subject={quote(subject)}&body={quote(body)}"
    st.link_button("Open in email client", mailto_url, type="primary")
