import json
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from modules.authentication import AuthenticationService


@dataclass
class ExtractorSelectors:
    course_heading_selectors: tuple[str, ...] = ("h1", "#page-header h1")
    profile_link_selectors: tuple[str, ...] = (
        "a.d-inline-block.aabtn",
        'a[href*="/user/view.php"]',
    )
    profile_card_selectors: tuple[str, ...] = (
        "div.card.card-body.card-profile",
        ".card-profile",
    )


class CourseExtractor:
    def __init__(self, auth_service: AuthenticationService, selectors: ExtractorSelectors | None = None):
        self.auth_service = auth_service
        self.selectors = selectors or ExtractorSelectors()
        self.base_url = "https://elms.uiu.ac.bd"

    def _extract_course_title(self, soup: BeautifulSoup) -> str:
        for selector in self.selectors.course_heading_selectors:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                return node.get_text(strip=True)
        return "Unknown Course"

    def _extract_course_semester(self, course_name: str) -> str:
        match = re.search(
            r"\b(Spring|Summer|Fall)\s+(20\d{2}|\d{2})\b",
            course_name,
            flags=re.IGNORECASE,
        )
        if not match:
            return ""
        year = match.group(2)
        year = f"20{year}" if len(year) == 2 else year
        return f"{match.group(1).title()} {year}"

    def _extract_profile_links(self, soup: BeautifulSoup) -> list[str]:
        links: list[str] = []
        for selector in self.selectors.profile_link_selectors:
            for node in soup.select(selector):
                href = (node.get("href") or "").strip()
                if not href:
                    continue
                if href.startswith("/"):
                    href = f"{self.base_url}{href}"
                if "/user/view.php" not in href:
                    continue
                links.append(href)
        return sorted(set(links))

    def _participant_page_url(self, course_id: str, page: int, perpage: int = 5000) -> str:
        return (
            f"{self.base_url}/user/index.php?page={page}&perpage={perpage}"
            f"&contextid=0&id={course_id}&newcourse"
        )

    def _extract_row_hints(self, soup: BeautifulSoup) -> dict[str, dict[str, str]]:
        hints: dict[str, dict[str, str]] = {}
        for row in soup.select("table tbody tr"):
            user_link = row.select_one('a[href*="/user/view.php"]')
            if not user_link:
                continue
            href = (user_link.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("/"):
                href = f"{self.base_url}{href}"

            name = user_link.get_text(strip=True)
            row_text = row.get_text(" ", strip=True)
            role = ""
            lowered_row_text = row_text.lower()
            if any(marker in lowered_row_text for marker in ("teacher", "instructor", "editingteacher", "course creator")):
                role = "Teacher / Staff"

            email_node = row.select_one('a[href^="mailto:"]')
            email = email_node.get_text(strip=True) if email_node else ""

            student_id = ""
            id_match = re.search(r"\b0\d{9}\b", row_text)
            if id_match:
                student_id = id_match.group(0)

            hints[href] = {
                "full_name": name,
                "email": email,
                "student_id": student_id,
                "record_type": role,
            }
        return hints

    def _collect_profile_links_with_hints(self, session, course_id: str) -> tuple[str, list[str], dict[str, dict[str, str]], str | None]:
        all_links: list[str] = []
        hints: dict[str, dict[str, str]] = {}
        course_name = "Unknown Course"

        page = 0
        max_pages = 200
        previous_link_count = -1

        while page < max_pages:
            url = self._participant_page_url(course_id, page)
            response = session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()

            if "login/index.php" in response.url:
                return "", [], {}, "Unauthorized access or session expired."

            soup = BeautifulSoup(response.text, "html.parser")
            if page == 0:
                course_name = self._extract_course_title(soup)

            page_links = self._extract_profile_links(soup)
            page_hints = self._extract_row_hints(soup)

            for link, hint in page_hints.items():
                existing = hints.get(link, {})
                hints[link] = {
                    "full_name": hint.get("full_name") or existing.get("full_name", ""),
                    "email": hint.get("email") or existing.get("email", ""),
                    "student_id": hint.get("student_id") or existing.get("student_id", ""),
                    "record_type": hint.get("record_type") or existing.get("record_type", ""),
                }

            before = len(set(all_links))
            all_links.extend(page_links)
            deduped = sorted(set(all_links))
            after = len(deduped)
            all_links = deduped

            has_next = bool(soup.select_one('a[rel="next"], .pagination a[aria-label="Next"]'))
            no_growth = after == before or after == previous_link_count
            previous_link_count = after

            if no_growth or not page_links or not has_next:
                break
            page += 1

        if not all_links:
            return course_name, [], hints, "No participant profile links found on this course page."

        return course_name, all_links, hints, None

    def _extract_email(self, profile_soup: BeautifulSoup) -> str:
        content_nodes = profile_soup.select("li.contentnode")
        for node in content_nodes:
            email_tag = node.find("a", href=True)
            if not email_tag:
                continue
            href = (email_tag.get("href") or "").strip().lower()
            if href.startswith("mailto:"):
                txt = email_tag.get_text(strip=True)
                if txt:
                    return txt

        mailto = profile_soup.select_one('a[href^="mailto:"]')
        if mailto and mailto.get_text(strip=True):
            return mailto.get_text(strip=True)
        return ""

    def _extract_name(self, profile_soup: BeautifulSoup) -> str:
        for selector in self.selectors.profile_card_selectors:
            card = profile_soup.select_one(selector)
            if card:
                heading = card.find("h3")
                if heading and heading.get_text(strip=True):
                    return heading.get_text(strip=True)

        fallback = profile_soup.select_one("h1")
        if fallback:
            return fallback.get_text(strip=True)
        return ""

    def _extract_student_id(self, profile_soup: BeautifulSoup) -> str:
        for dt in profile_soup.find_all("dt"):
            label = dt.get_text(" ", strip=True).lower()
            if "id number" in label or "student id" in label:
                dd = dt.find_next_sibling("dd")
                if dd:
                    match = re.search(r"\b\d{10}\b", dd.get_text(" ", strip=True))
                    if match:
                        return match.group(0)

        for node in profile_soup.select("li.contentnode"):
            txt = node.get_text(" ", strip=True)
            if "id number" in txt.lower() or "student id" in txt.lower():
                match = re.search(r"\b\d{10}\b", txt)
                if match:
                    return match.group(0)

        raw_text = profile_soup.get_text(" ", strip=True)
        generic = re.search(r"\b0\d{9}\b", raw_text)
        if generic:
            return generic.group(0)
        return ""

    def _fetch_courses_page(self, offset: int, limit: int) -> list[dict]:
        session = self.auth_service.get_requests_session()
        sesskey = self.auth_service.sesskey
        if session is None or not sesskey:
            return []

        course_url = (
            f"{self.base_url}/lib/ajax/service.php?sesskey={sesskey}"
            "&info=core_course_get_enrolled_courses_by_timeline_classification"
        )
        data = [
            {
                "index": 0,
                "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                "args": {
                    "offset": offset,
                    "limit": limit,
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

        response = session.post(course_url, json=data, timeout=30)
        response.raise_for_status()
        payload = json.loads(response.text)
        return payload[0]["data"].get("courses", [])

    def get_all_courses(self) -> list[dict]:
        if not self.auth_service.ensure_session_alive():
            return []

        offset = 0
        limit = 24
        all_courses: list[dict] = []

        while True:
            page = self._fetch_courses_page(offset=offset, limit=limit)
            if not page:
                break
            all_courses.extend(page)
            if len(page) < limit:
                break
            offset += limit

        return all_courses

    def get_all_course_ids(self) -> list[str]:
        return [str(course.get("id")) for course in self.get_all_courses() if course.get("id")]

    def get_all_course_name_map(self) -> dict[str, str]:
        course_name_id: dict[str, str] = {}
        for course in self.get_all_courses():
            full_name = str(course.get("fullname", "")).strip()
            clean_name = full_name.split(":", 1)[-1].strip() if full_name else "Unknown"
            course_id = str(course.get("id", "")).strip()
            if clean_name and course_id:
                course_name_id[clean_name] = course_id
        return course_name_id

    def extract_course(self, course_id: str) -> tuple[list[dict], str | None]:
        if not self.auth_service.ensure_session_alive():
            return [], "Session expired. Please log in again."

        session = self.auth_service.get_requests_session()
        if session is None:
            return [], "Unable to initialize authenticated HTTP session."

        try:
            course_name, profile_links, row_hints, collect_error = self._collect_profile_links_with_hints(
                session, str(course_id)
            )
            if collect_error:
                return [], collect_error

            records = []
            seen = set()
            for profile_url in profile_links:
                profile_page = session.get(profile_url, timeout=30)
                profile_page.raise_for_status()

                profile_soup = BeautifulSoup(profile_page.text, "html.parser")
                hint = row_hints.get(profile_url, {})

                name = self._extract_name(profile_soup) or hint.get("full_name", "")
                email = self._extract_email(profile_soup) or hint.get("email", "")
                student_id = self._extract_student_id(profile_soup) or hint.get("student_id", "")

                key = (course_id, student_id, name, email)
                if key in seen:
                    continue
                seen.add(key)

                records.append(
                    {
                        "course_id": str(course_id),
                        "course_name": course_name,
                        "course_semester": self._extract_course_semester(course_name),
                        "student_id": student_id,
                        "record_type": hint.get("record_type", ""),
                        "full_name": name,
                        "email": email,
                        "profile_url": profile_url,
                    }
                )

            return records, None
        except Exception as exc:
            return [], f"Extraction error for course {course_id}: {exc}"

    def extract_multiple_courses(self, course_ids: list[str]) -> tuple[list[dict], list[dict]]:
        all_records = []
        logs = []

        for cid in course_ids:
            records, error = self.extract_course(cid)
            all_records.extend(records)
            logs.append(
                {
                    "course_id": cid,
                    "status": "failed" if error else "success",
                    "participants": len(records),
                    "error": error or "",
                }
            )

        return all_records, logs
