# UIU ELMS Student Extractor

**SabrWare · © 2026 SabrWare. All rights reserved.**

A local Streamlit workspace for authorized UIU ELMS users. It signs in with the
user's own ELMS account, extracts participant information from enrolled courses,
and produces searchable, filterable reports without writing credentials to disk.

## What it does

- Authenticates against the UIU ELMS Moodle login page using its CSRF token.
- Loads every course available to the authenticated account, including paginated
  course lists.
- Extracts participant name, email, student ID, profile URL, course name, course
  ID, and detected course semester.
- Keeps teachers and staff without fabricating a student ID. They appear in a
  dedicated staff view and export sheet.
- Deduplicates students across courses while retaining the course-wise enrollment
  view.
- Filters the extracted workspace by:
  - course ID, course name, student ID, or student name search
  - course semester
  - department
  - admission year
  - student trimester
- Sorts the visible table by key fields in ascending or descending order.
- Exports Excel, all-student CSV, course-wise CSV, per-course CSV, and invalid
  record CSV files.
- Includes a group email composer with an editable subject/body template and a
  single CC list for a course section. It opens the user's local email client
  and never sends or stores messages.
- Uses a focused UIU-inspired light theme with SabrWare rights notices and
  readable controls.
- The orange sidebar uses `#f1630d`, with black text and navy/white hover
  states for clear interaction.

## Visual theme

The interface uses a UIU-inspired palette based on publicly described UIU
visual guidance: deep navy for structure, teal for action, white/gray for
surfaces, and orange for hover emphasis. Inputs, placeholders, download
buttons, and links share the same light-theme treatment.

## Important authorization notice

Use this application only with an ELMS account and courses you are authorized
to access. It does not bypass authentication or permissions. Do not share
credentials, exported personal data, or session cookies. SabrWare is not
responsible for unauthorized use of the application or its exports.

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the application

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, normally
`http://localhost:8501`.

## Usage

1. Enter your ELMS username and password on the login screen.
2. Select **Extract All Courses** to collect all enrolled courses, or use the
   dashboard for one or more course IDs.
3. Use the Student Workspace controls to switch between combined students and
   course-wise enrollment.
4. Apply filters and choose a sort column/direction.
5. Use Export Center to download the report format required.
6. Log out when finished. The in-memory requests session is closed on logout.

## Project structure

```text
student_email_extractor/
├── app.py                         # Streamlit entry point and branded shell
├── requirements.txt
├── modules/
│   ├── authentication.py          # ELMS login/session handling
│   ├── course_extractor.py        # Course and participant extraction
│   ├── data_processor.py          # Parsing, validation, deduplication
│   ├── excel_exporter.py          # Excel and CSV byte generation
│   ├── student_parser.py          # UIU student ID parsing
│   └── validators.py
├── components/
│   ├── login_ui.py
│   ├── dashboard.py
│   ├── email_ui.py              # Course-section email composer
│   ├── results_table.py           # Filters, sorting, and data table
│   └── export_ui.py
├── tests/
└── assets/
```

## Data behavior

Student IDs are parsed into department, admission year, trimester, and serial
number using the UIU 10-digit format. Records identified as teachers/staff, or
participant records with no student ID and a valid email, are kept in the
Teachers & Staff view without an artificial ID. Records with invalid IDs or
invalid email addresses are kept in Invalid Records rather than being silently
discarded. Combined student results merge course IDs for duplicates; the
course-wise dataset preserves one row per enrollment.

The ELMS course title is searched for `Spring`, `Summer`, or `Fall` plus a year
to populate the course semester filter. If a title has no recognizable
semester, that field remains blank.

## Testing

```bash
pytest -q
```

## Troubleshooting

- **Login token error:** ELMS may have changed its login form. Check network
  access and update the token selector in `modules/authentication.py`.
- **Session expired:** Log in again; the app validates the session before each
  course extraction.
- **No participant links:** Confirm that your account can open the course's
  participant page in ELMS.
- **Slow extraction:** The app requests each participant profile from ELMS.
  Keep the browser open and avoid starting duplicate extractions.
- **Email client does not open:** Copy the generated CC list and template into
  your mail provider manually. Very large sections may exceed mailto URL limits.

## Ownership

This project and its application branding are owned by **SabrWare**.
