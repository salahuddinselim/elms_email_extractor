import csv
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://elms.uiu.ac.bd"
LOGIN_URL = f"{BASE_URL}/login/index.php"
AJAX_SERVICE_URL = f"{BASE_URL}/lib/ajax/service.php"


def extract_csrf_token(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.find("input", {"name": "logintoken"})
    return token_input["value"] if token_input else None


def extract_session_key(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.find("input", {"name": "sesskey"})
    return token_input["value"] if token_input else None


def login() -> tuple[requests.Session, str] | None:
    session = requests.Session()
    login_page = session.get(LOGIN_URL, timeout=30)
    login_page.raise_for_status()

    csrf_token = extract_csrf_token(login_page.text)
    if not csrf_token:
        print("Failed to extract CSRF token.")
        return None

    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()

    payload = {
        "username": username,
        "password": password,
        "logintoken": csrf_token,
    }

    response = session.post(LOGIN_URL, data=payload, timeout=30)
    response.raise_for_status()

    if "Dashboard" not in response.text:
        print("Login failed. Please verify username/password.")
        return None

    session_key = extract_session_key(response.text)
    if not session_key:
        print("Login succeeded, but failed to extract session key.")
        return None

    print("Login successful!")
    return session, session_key


def _fetch_courses(session: requests.Session, session_key: str) -> list[dict]:
    params = {
        "sesskey": session_key,
        "info": "core_course_get_enrolled_courses_by_timeline_classification",
    }

    data = [
        {
            "index": 0,
            "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
            "args": {
                "offset": 0,
                "limit": 100,
                "classification": "all",
                "sort": "fullname",
                "customfieldname": "",
                "customfieldvalue": "",
                "requiredfields": [
                    "id",
                    "fullname",
                    "shortname",
                    "showcoursecategory",
                    "showshortname",
                    "visible",
                    "enddate",
                ],
            },
        }
    ]

    response = session.post(AJAX_SERVICE_URL, params=params, json=data, timeout=30)
    response.raise_for_status()

    payload = json.loads(response.text)
    return payload[0]["data"]["courses"]


def get_all_course_id(session: requests.Session, session_key: str) -> list[str]:
    courses = _fetch_courses(session, session_key)
    return [str(course["id"]) for course in courses]


def extract_all_course_with_name(session: requests.Session, session_key: str) -> dict[str, str]:
    courses = _fetch_courses(session, session_key)
    return {
        course["fullname"].split(":", 1)[-1].strip(): str(course["id"])
        for course in courses
    }


def _safe_course_code(course_name: str) -> str:
    match = re.search(r"(Spring|Fall|Summer)\s\d{2,4}\s([^:]+)", course_name)
    if match:
        code = match.group(2).strip()
    else:
        code = course_name.strip()

    code = re.sub(r"\s+", "_", code)
    code = code.replace("/", "_")
    code = re.sub(r"[^\w.-]", "_", code)
    return code


def extract_course_by_id(session: requests.Session, course_id: str, output_dir: Path | None = None) -> None:
    if output_dir is None:
        output_dir = Path.cwd()

    full_list_url = f"{BASE_URL}/user/index.php?page=0&perpage=5000&contextid=0&id={course_id}&newcourse"
    response = session.get(full_list_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    heading = soup.find("h1")
    if not heading:
        print(f"Could not find course title for course id {course_id}")
        return

    course_name = heading.text.strip()
    print(f"Extracting data for course: {course_name}")

    course_code = _safe_course_code(course_name)

    profile_links = [
        a["href"]
        for a in soup.find_all("a", class_="d-inline-block aabtn", href=True)
    ]
    profile_links = list(set(profile_links))

    emails: list[str] = []
    users_data: list[tuple[str, str]] = []

    for profile_url in profile_links:
        profile_page = session.get(profile_url, timeout=30)
        profile_page.raise_for_status()

        profile_soup = BeautifulSoup(profile_page.text, "html.parser")
        profile_details = profile_soup.find("div", class_="card card-body card-profile")
        if not profile_details:
            continue

        name_tag = profile_details.find("h3")
        name = name_tag.text.strip() if name_tag else "Unknown"

        email_node = profile_soup.find("li", class_="contentnode")
        if not email_node:
            continue

        email_tag = email_node.find("a", href=True)
        email = email_tag.text.strip() if email_tag else None
        if not email:
            continue

        emails.append(email)
        users_data.append((name, email))
        print(f"Name: {name}, Email: {email}")

    print(f"\nTotal Emails Found: {len(emails)}")

    csv_filename = output_dir / f"{course_code}_users.csv"
    with csv_filename.open(mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email"])
        writer.writerows(users_data)

    print(f"CSV file '{csv_filename.name}' saved successfully.")

    email_filename = output_dir / f"{course_code}_emails.txt"
    with email_filename.open(mode="w", encoding="utf-8") as file:
        for email in emails:
            file.write(email + "\n")

    print(f"Email list file '{email_filename.name}' saved successfully.")


def main() -> None:
    login_result = login()
    if login_result is None:
        print("Failed to login properly. Exiting program.")
        raise SystemExit(1)

    session, session_key = login_result

    try:
        courses = extract_all_course_with_name(session, session_key)
        if not courses:
            print("No enrolled courses found.")
            return

        print("\nEnrolled courses:")
        for index, (name, cid) in enumerate(courses.items(), start=1):
            print(f"{index}. {name} (id={cid})")

        chosen = input("\nEnter a course id to extract emails from: ").strip()
        if chosen not in set(courses.values()):
            print("Invalid course id.")
            return

        extract_course_by_id(session, chosen)

    finally:
        session.close()


if __name__ == "__main__":
    main()
