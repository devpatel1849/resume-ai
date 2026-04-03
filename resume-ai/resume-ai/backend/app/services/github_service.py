import requests
from urllib.parse import urlparse

from app.config import settings


class GitHubService:
    def _normalize_username(self, username: str) -> str:
        raw = (username or "").strip()
        if not raw:
            return ""

        # Support full profile URLs and plain usernames.
        if raw.startswith("http://") or raw.startswith("https://"):
            parsed = urlparse(raw)
            path = (parsed.path or "").strip("/")
            raw = path.split("/")[0] if path else ""

        raw = raw.replace("@", "").strip()

        # Remove query/hash fragments pasted with username text.
        raw = raw.split("?")[0].split("#")[0].strip("/")
        return raw

    def _fetch_with_headers(self, url: str, headers: dict) -> requests.Response | None:
        try:
            return requests.get(url, headers=headers, timeout=12)
        except requests.RequestException:
            return None

    def get_repos(self, username: str):
        normalized = self._normalize_username(username)
        if not normalized:
            return []

        url = f"https://api.github.com/users/{normalized}/repos"
        base_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        headers = {}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        headers.update(base_headers)

        response = self._fetch_with_headers(url, headers)

        # Invalid or expired token should not block public repo fetches.
        if response is not None and response.status_code in {401, 403} and settings.GITHUB_TOKEN:
            response = self._fetch_with_headers(url, base_headers)

        if response is None:
            return []

        if response.status_code != 200:
            return []

        repos = response.json()

        extracted = []
        for repo in repos:
            extracted.append({
                "name": repo["name"],
                "description": repo["description"],
                "language": repo["language"]
            })

        return extracted


github_service = GitHubService()