import re

import requests
from bs4 import BeautifulSoup


class AuthenticationService:
    def __init__(self, headless: bool = True):
        self.base_url = "https://elms.uiu.ac.bd"
        self.login_url = f"{self.base_url}/login/index.php"
        self._authenticated = False
        self._last_error = ""
        self._requests_session: requests.Session | None = None
        self._sesskey: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def sesskey(self) -> str | None:
        return self._sesskey

    def _extract_csrf_token(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        token_input = soup.find("input", {"name": "logintoken"})
        return token_input.get("value") if token_input else None

    def _extract_sesskey(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        token_input = soup.find("input", {"name": "sesskey"})
        if token_input and token_input.get("value"):
            return token_input.get("value")

        patterns = [
            r'"sesskey"\s*:\s*"([a-zA-Z0-9]+)"',
            r'"sesskey"\s*,\s*"([a-zA-Z0-9]+)"',
            r"sesskey=([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def login(self, username: str, password: str) -> bool:
        self._last_error = ""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        try:
            login_page = session.get(self.login_url, timeout=30)
            login_page.raise_for_status()
        except requests.RequestException:
            self._last_error = "Unable to load ELMS login page. Check network and try again."
            return False

        csrf_token = self._extract_csrf_token(login_page.text)
        if not csrf_token:
            self._last_error = "Failed to extract login token. ELMS login page may have changed."
            return False

        payload = {
            "username": username,
            "password": password,
            "logintoken": csrf_token,
        }

        try:
            response = session.post(self.login_url, data=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            self._last_error = "Login request failed. Please try again."
            return False

        if "Dashboard" not in response.text and "login/index.php" in response.url:
            self._last_error = "Login failed. Invalid username or password."
            return False

        sesskey = self._extract_sesskey(response.text)
        if not sesskey:
            try:
                my_page = session.get(f"{self.base_url}/my/", timeout=30)
                my_page.raise_for_status()
                sesskey = self._extract_sesskey(my_page.text)
            except requests.RequestException:
                sesskey = None

        if not sesskey:
            self._last_error = "Login succeeded but session key was not found."
            return False

        self._requests_session = session
        self._sesskey = sesskey
        self._authenticated = True
        return True

    def get_requests_session(self) -> requests.Session | None:
        if not self._authenticated:
            return None
        return self._requests_session

    def ensure_session_alive(self) -> bool:
        if not self._authenticated or not self._requests_session:
            return False

        try:
            probe = self._requests_session.get(f"{self.base_url}/my/", timeout=30, allow_redirects=True)
            if "login/index.php" in probe.url:
                self._authenticated = False
                self._last_error = "Session expired. Please log in again."
                return False
            if not self._sesskey:
                self._sesskey = self._extract_sesskey(probe.text)
        except requests.RequestException:
            self._last_error = "Network error while validating session."
            return False

        return True

    def logout(self) -> None:
        if self._requests_session:
            try:
                self._requests_session.get(f"{self.base_url}/login/logout.php", timeout=15)
            except requests.RequestException:
                pass
            self._requests_session.close()

        self._authenticated = False
        self._requests_session = None
        self._sesskey = None
        self._last_error = ""

