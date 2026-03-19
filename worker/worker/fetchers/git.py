"""
Git fetcher — скачивает файлы спецификаций из GitHub / GitLab / Bitbucket Server.
Поддерживает фильтрацию по расширению (.yaml, .yml, .json, .proto).
"""
import base64
import fnmatch
import logging
import urllib.parse
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

SPEC_EXTENSIONS = (".yaml", ".yml", ".json", ".proto")


def _parse_github_repo(url: str) -> tuple[str, str]:
    """https://github.com/org/repo → ('org', 'repo')"""
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Некорректный GitHub URL: '{url}'. "
            f"Ожидается формат: https://github.com/org/repo"
        )
    return parts[0], parts[1]


def _parse_bitbucket_server(url: str) -> tuple[str, str, str]:
    """
    https://bitbucket.company.com/projects/KEY/repos/my-repo → (base, 'KEY', 'my-repo')
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parts = parsed.path.strip("/").split("/")
    # Ожидаем: projects / KEY / repos / SLUG
    try:
        proj_idx = parts.index("projects")
        project_key = parts[proj_idx + 1]
        repo_slug = parts[proj_idx + 3]  # projects/KEY/repos/SLUG
    except (ValueError, IndexError):
        raise ValueError(
            f"Некорректный Bitbucket Server URL: '{url}'. "
            f"Ожидается: https://bitbucket.company.com/projects/KEY/repos/my-repo"
        )
    return base, project_key, repo_slug


async def fetch_github(repo_url: str, branch: str, token: str | None, path_filter: str | None) -> list[dict]:
    """GitHub REST API v3."""
    owner, repo = _parse_github_repo(repo_url)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    files = []
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        r = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        )
        r.raise_for_status()
        tree = r.json().get("tree", [])

        for item in tree:
            if item["type"] != "blob":
                continue
            path = item["path"]
            if not any(path.endswith(ext) for ext in SPEC_EXTENSIONS):
                continue
            if path_filter and not fnmatch.fnmatch(path, path_filter):
                continue

            cr = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            )
            if cr.status_code != 200:
                log.warning(f"Skipping {path}: {cr.status_code}")
                continue

            data = cr.json()
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            files.append({
                "path": path,
                "content": content,
                "url": data.get("html_url", ""),
            })
            log.info(f"Fetched: {path}")

    return files


async def fetch_gitlab(repo_url: str, branch: str, token: str | None, path_filter: str | None) -> list[dict]:
    """GitLab REST API v4."""
    parsed = urlparse(repo_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    project_id = parsed.path.strip("/").replace("/", "%2F")

    headers = {}
    if token:
        headers["PRIVATE-TOKEN"] = token

    files = []
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        page = 1
        while True:
            r = await client.get(
                f"{base}/api/v4/projects/{project_id}/repository/tree",
                params={"ref": branch, "recursive": True, "per_page": 100, "page": page}
            )
            r.raise_for_status()
            items = r.json()
            if not items:
                break

            for item in items:
                if item["type"] != "blob":
                    continue
                path = item["path"]
                if not any(path.endswith(ext) for ext in SPEC_EXTENSIONS):
                    continue
                if path_filter and not fnmatch.fnmatch(path, path_filter):
                    continue

                encoded_path = urllib.parse.quote(path, safe="")
                cr = await client.get(
                    f"{base}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw",
                    params={"ref": branch}
                )
                if cr.status_code != 200:
                    log.warning(f"Skipping {path}: {cr.status_code}")
                    continue

                files.append({
                    "path": path,
                    "content": cr.text,
                    "url": f"{repo_url}/-/blob/{branch}/{path}",
                })
                log.info(f"Fetched: {path}")

            page += 1

    return files


async def fetch_bitbucket(repo_url: str, branch: str, token: str | None, path_filter: str | None) -> list[dict]:
    """
    Bitbucket Server (Data Center) REST API 1.0.
    URL формат: https://bitbucket.company.com/projects/KEY/repos/my-repo
    Токен: Personal Access Token (Bearer).
    """
    base, project_key, repo_slug = _parse_bitbucket_server(repo_url)

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api = f"{base}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}"
    files = []

    async with httpx.AsyncClient(headers=headers, timeout=30, verify=False) as client:
        # Получаем список всех файлов (рекурсивно, постранично)
        start = 0
        all_paths = []
        while True:
            r = await client.get(
                f"{api}/files",
                params={"at": branch, "limit": 500, "start": start}
            )
            r.raise_for_status()
            data = r.json()
            all_paths.extend(data.get("values", []))
            if data.get("isLastPage", True):
                break
            start = data.get("nextPageStart", start + 500)

        log.info(f"Bitbucket: found {len(all_paths)} files total")

        for path in all_paths:
            if not any(path.endswith(ext) for ext in SPEC_EXTENSIONS):
                continue
            if path_filter and not fnmatch.fnmatch(path, path_filter):
                continue

            encoded_path = urllib.parse.quote(path, safe="")
            cr = await client.get(
                f"{api}/raw/{encoded_path}",
                params={"at": branch}
            )
            if cr.status_code != 200:
                log.warning(f"Skipping {path}: {cr.status_code}")
                continue

            files.append({
                "path": path,
                "content": cr.text,
                "url": f"{repo_url}/browse/{path}?at={branch}",
            })
            log.info(f"Fetched: {path}")

    return files


async def fetch_files(repo_url: str, branch: str, token: str | None,
                      path_filter: str | None, provider: str) -> list[dict]:
    if provider == "gitlab":
        return await fetch_gitlab(repo_url, branch, token, path_filter)
    if provider == "bitbucket":
        return await fetch_bitbucket(repo_url, branch, token, path_filter)
    return await fetch_github(repo_url, branch, token, path_filter)
