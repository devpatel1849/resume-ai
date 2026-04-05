import requests
import re
from urllib.parse import urlparse

from app.config import settings


class GitHubService:
    _STOPWORDS = {
        "the", "and", "for", "with", "that", "this", "from", "into", "your", "you", "our", "are",
        "was", "were", "will", "can", "able", "role", "team", "work", "using", "use", "used", "have",
        "has", "had", "job", "description", "years", "year", "experience", "responsible", "build", "built",
        "develop", "developed", "developer", "engineer", "strong", "good", "skills", "skill", "etc", "about",
    }

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

    def _tokenize(self, text: str) -> set[str]:
        if not text:
            return set()

        tokens = re.findall(r"[a-zA-Z0-9+#.]+", text.lower())
        cleaned = {
            token
            for token in tokens
            if len(token) > 2 and token not in self._STOPWORDS and not token.isdigit()
        }
        return cleaned

    def _has_meaningful_description(self, description: str | None) -> bool:
        if not description:
            return False

        normalized = re.sub(r"\s+", " ", description.strip()).lower()
        if not normalized:
            return False

        banned = {
            "no description",
            "no description provided",
            "n/a",
            "na",
            "none",
        }
        return normalized not in banned

    def _score_repo(self, repo: dict, jd_tokens: set[str]) -> int:
        haystack = " ".join([
            repo.get("name") or "",
            repo.get("description") or "",
            repo.get("language") or "",
        ])
        repo_tokens = self._tokenize(haystack)
        overlap = len(repo_tokens & jd_tokens)

        score = overlap
        language = (repo.get("language") or "").lower()
        if language and language in jd_tokens:
            score += 2

        name = (repo.get("name") or "").lower()
        if any(token in name for token in jd_tokens):
            score += 1

        return score

    def _select_relevant_repos(self, repos: list[dict], job_description: str | None, max_projects: int) -> list[dict]:
        if not repos:
            return []

        max_projects = max(3, min(max_projects or 4, 4))
        target_count = min(max_projects, len(repos))
        min_count = min(3, len(repos), target_count)

        jd_tokens = self._tokenize(job_description or "")
        if not jd_tokens:
            sorted_fallback = sorted(
                repos,
                key=lambda repo: (repo.get("stars", 0), repo.get("updated_at") or ""),
                reverse=True,
            )
            return sorted_fallback[:target_count]

        scored = []
        for repo in repos:
            score = self._score_repo(repo, jd_tokens)
            scored.append((score, repo))

        scored.sort(
            key=lambda item: (
                item[0],
                item[1].get("stars", 0),
                item[1].get("updated_at") or "",
            ),
            reverse=True,
        )

        selected = [repo for score, repo in scored if score > 0][:target_count]
        if len(selected) < min_count:
            for _, repo in scored:
                if repo in selected:
                    continue
                selected.append(repo)
                if len(selected) >= min_count:
                    break

        return selected[:target_count]

    def get_repos(self, username: str, job_description: str | None = None, max_projects: int = 4):
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
                "language": repo["language"],
                "stars": repo.get("stargazers_count", 0),
                "updated_at": repo.get("updated_at"),
            })

        extracted = [repo for repo in extracted if self._has_meaningful_description(repo.get("description"))]
        if not extracted:
            return []

        selected = self._select_relevant_repos(extracted, job_description, max_projects)
        return [
            {
                "name": repo["name"],
                "description": repo["description"],
                "language": repo["language"],
            }
            for repo in selected
        ]


github_service = GitHubService()