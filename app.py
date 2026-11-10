from pathlib import Path

import pandas as pd
import streamlit as st

from components.dashboard import render_dashboard
from components.export_ui import render_export_ui
from components.login_ui import render_login_page
from components.results_table import render_results
from modules.authentication import AuthenticationService
from modules.course_extractor import CourseExtractor
from modules.data_processor import process_records


def _render_footer() -> None:
    st.markdown(
        '<div class="footer">© 2026 SabrWare. All rights reserved. · Built for authorized academic use only.</div>',
        unsafe_allow_html=True,
    )


def _get_auth_service() -> AuthenticationService:
    if "auth_service" not in st.session_state:
        st.session_state.auth_service = AuthenticationService(headless=True)
    return st.session_state.auth_service


def _render_sidebar(auth_service: AuthenticationService):
    st.sidebar.caption("## ELMS student workspace")
    st.sidebar.caption("© 2026 SabrWare · All rights reserved")
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Workspace")
    if st.sidebar.button("Course Evaluation · Upcoming", use_container_width=True):
        st.session_state.show_course_evaluation = True
        st.session_state.show_github_note = False
    if st.sidebar.button("GitHub repository", use_container_width=True):
        st.session_state.show_github_note = True
        st.session_state.show_course_evaluation = False
    status = "Authenticated" if auth_service.is_authenticated else "Logged out"
    st.sidebar.write(f"Status: **{status}**")
    if auth_service.is_authenticated and st.sidebar.button("Logout", use_container_width=True):
        auth_service.logout()
        st.session_state.pop("processed", None)
        st.session_state.pop("logs", None)
        st.success("Logged out and browser session cleaned up.")
        st.rerun()


def main():
    st.set_page_config(page_title="UIU ELMS Student Extractor", page_icon="🎓", layout="wide")
    colors = {
        "page": "#f7fafc",
        "surface": "#ffffff",
        "ink": "#132238",
        "muted": "#607087",
        "line": "#dce5ef",
        "sidebar": "#f1630d",
        "primary": "#0e7490",
    }
    st.markdown(
        f"""
        <style>
        :root {{ --ink: {colors["ink"]}; --muted: {colors["muted"]}; --line: {colors["line"]}; --accent: {colors["primary"]}; }}
        .stApp {{ background: {colors["page"]}; color: var(--ink); }}
        [data-testid="stHeader"] {{ background: {colors["page"]}; }}
        [data-testid="stDeployButton"] {{ display: none !important; }}
        [data-testid="stSidebar"] {{ background: #f1630d; border-right: 1px solid #d04e08; }}
        [data-testid="stSidebar"] * {{ color: #000000 !important; }}
        [data-testid="stSidebar"] button {{ background: #ffffff; border-color: #b7c8d6; color: #000000 !important; }}
        [data-testid="stSidebar"] button:hover {{ border-color: #132238; color: #000000 !important; background: #fff7ed; }}
        [data-testid="stMainBlockContainer"] {{ background: {colors["page"]}; }}
        [data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stDataFrame"] {{ background: {colors["surface"]}; border-color: var(--line); }}
        [data-baseweb="input"], [data-baseweb="textarea"] {{ background: {colors["surface"]}; border-color: var(--line); }}
        [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{ color: var(--ink); caret-color: var(--accent); }}
        [data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder {{ color: {colors["muted"]}; opacity: 1; }}
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{ color: var(--ink); }}
        [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder {{ color: {colors["muted"]}; opacity: 1; }}
        [data-testid="stSelectbox"] [role="combobox"] {{ color: var(--ink); }}
        .stButton > button, [data-testid="stDownloadButton"] button, [data-testid="stLinkButton"] a {{
            border: 1px solid {colors["primary"]};
            color: {colors["primary"]};
            background: transparent;
        }}
        .stButton > button:hover, [data-testid="stDownloadButton"] button:hover, [data-testid="stLinkButton"] a:hover {{
            border-color: #f28c28;
            color: #f28c28;
            background: rgba(242, 140, 40, .1);
        }}
        .brand-mark {{ display: flex; gap: .75rem; align-items: center; margin: .25rem 0 1.75rem; }}
        .brand-mark strong {{ font-size: 1.15rem; letter-spacing: -.02em; }}
        .brand-dot {{ width: .75rem; height: .75rem; border-radius: 50%; background: #38b2ac; box-shadow: 0 0 0 6px rgba(56,178,172,.15); }}
        h1, h2, h3, label, [data-testid="stMetricValue"] {{ color: var(--ink); letter-spacing: -.03em; }}
        .hero {{ border-bottom: 1px solid var(--line); padding-bottom: 1.25rem; margin-bottom: 1.5rem; }}
        .hero p, .muted {{ color: var(--muted); }}
        .footer {{ border-top: 1px solid var(--line); margin-top: 3rem; padding: 1.25rem 0 2rem; color: var(--muted); font-size: .82rem; text-align: center; }}
        .stButton > button[kind="primary"] {{ background: {colors["primary"]}; border-color: {colors["primary"]}; color: #06121f; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    auth_service = _get_auth_service()
    _render_sidebar(auth_service)

    st.markdown(
        '<div class="brand-mark"><span class="brand-dot"></span><strong>SabrWare / ELMS tools</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero"><h1>Student data workspace</h1>'
        '<p>Extract enrolled course participants, explore the dataset, and export clean reports from one focused workspace.</p></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("show_course_evaluation"):
        st.info("Course Evaluation is upcoming. This workspace will support evaluation collection and reporting in a future release.")
    if st.session_state.get("show_github_note"):
        st.success("Thank you for using SabrWare ELMS tools. If this project helps you, please consider starring it on GitHub.")
        st.link_button(
            "Star the project on GitHub",
            "https://github.com/salahuddinselim/elms_email_extractor",
        )
    with st.expander("How to use", expanded=False):
        st.markdown(
            "1. Login with your ELMS account.\n"
            "2. Use **Extract All Courses** to pull every course available to your account.\n"
            "3. Review by course, semester, department, trimester, or search term.\n"
            "4. Sort ascending or descending, then download an Excel or CSV report."
        )

    if not auth_service.is_authenticated:
        logged_in = render_login_page(auth_service)
        if logged_in:
            st.rerun()
        _render_footer()
        return

    extractor = CourseExtractor(auth_service)

    def run_extraction(target_course_ids: list[str], multi_course: bool) -> None:
        if not target_course_ids:
            st.error("No course IDs found to extract.")
            return

        with st.spinner("Extracting participant records..."):
            progress = st.progress(0.0)
            all_records = []
            logs = []
            total = len(target_course_ids)

            for idx, cid in enumerate(target_course_ids, start=1):
                records, err = extractor.extract_course(cid)
                all_records.extend(records)
                logs.append(
                    {
                        "course_id": cid,
                        "status": "failed" if err else "success",
                        "participants": len(records),
                        "error": err or "",
                    }
                )
                progress.progress(idx / total)

            st.session_state.processed = process_records(all_records)
            st.session_state.logs = logs
            st.session_state.last_multi_course = multi_course

        st.success(f"Extraction finished for {len(target_course_ids)} course(s).")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Actions")
    if st.sidebar.button("Extract All Courses", type="primary", use_container_width=True):
        run_extraction(extractor.get_all_course_ids(), multi_course=True)
    if st.sidebar.button("Load Course Name/ID List", use_container_width=True):
        st.session_state.course_map = extractor.get_all_course_name_map()

    st.subheader("Quick Actions")
    st.caption("No course IDs needed for Extract All Courses.")
    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

    if action_col1.button("Show All Course ID with Name", use_container_width=True):
        with st.spinner("Loading enrolled courses..."):
            st.session_state.course_map = extractor.get_all_course_name_map()

    if action_col2.button("Extract All Courses", type="primary", use_container_width=True):
        run_extraction(extractor.get_all_course_ids(), multi_course=True)

    if action_col3.button("Clear Results", use_container_width=True):
        st.session_state.pop("processed", None)
        st.session_state.pop("logs", None)
        st.success("Cleared previous results.")

    if st.session_state.get("course_map"):
        st.markdown("**Enrolled Courses (Name to ID)**")
        rows = [{"Course Name": k, "Course ID": v} for k, v in st.session_state["course_map"].items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    mode, course_ids, can_extract = render_dashboard()
    if can_extract:
        if mode == "Single Course" and len(course_ids) != 1:
            st.error("Please provide exactly one course ID for Single Course mode.")
        elif not course_ids:
            st.error("Please provide at least one valid course ID.")
        else:
            run_extraction(course_ids, multi_course=(mode == "Multiple Courses"))

    st.divider()
    processed = st.session_state.get("processed")
    logs = st.session_state.get("logs", [])
    if processed:
        selected_course = render_results(processed, logs)
        render_export_ui(
            processed,
            multi_course=bool(st.session_state.get("last_multi_course", False)),
            selected_course=selected_course,
        )
    else:
        st.info("No extracted data yet. Use Extract All Courses or run Dashboard extraction.")

    _render_footer()


if __name__ == "__main__":
    main()
