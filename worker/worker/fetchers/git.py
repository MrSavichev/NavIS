"""
Git fetcher — скачивает файлы спецификаций из GitHub / GitLab.
Поддерживает фильтрацию по расширению (.yaml, .yml, .json, .proto).
"""
import fnmatch
import logging
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

SPEC_EXTENSIONS = (".yaml", ".yml", ".json", ".proto")


def _parse_github_repo(url: str) -> tuple[str, str]:
    """https://github.com/org/repo → ('org', 'repo')"""
    parts = urlparse(url).path.strip("/").split("/")
    return parts[0], parts[1]


def _parse_gitlab_repo(url: str) -> str:
    """https://gitlab.example.com/org/repo → 'org%2Frepo' (encoded)"""
    path = urlparse(url).path.strip("/")
    return path.replace("/", "%2F")


async def fetch_github(repo_url: str, branch: str, token: str | None, path_filter: str | None) -> list[dict]:
    """
    Возвращает список файлов:
    [{"path": "api/openapi.yaml", "content": "...", "url": "..."}]
    """
    owner, repo = _parse_github_repo(repo_url)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    files = []
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # Получаем дерево файлов
        r = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        )
        r.raise_for_status()
        tree = r.json().get("tree", [])

        for item in tree:
            if item["type"] != "blob":
                continue
            path = item["path"]
            if not path.endswith(SPEC_EXTENSIONS):
                continue
            if path_filter and not fnmatch.fnmatch(path, path_filter):
                continue

            # Скачиваем содержимое
            cr = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            )
            if cr.status_code != 200:
                log.warning(f"Skipping {path}: {cr.status_code}")
                continue

            data = cr.json()
            import base64
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
        # Список файлов рекурсивно
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
                if not path.endswith(SPEC_EXTENSIONS):
                    continue
                if path_filter and not fnmatch.fnmatch(path, path_filter):
                    continue

                # Скачиваем файл
                import urllib.parse
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


async def fetch_files(repo_url: str, branch: str, token: str | None,
                      path_filter: str | None, provider: str) -> list[dict]:
    if provider == "gitlab":
        return await fetch_gitlab(repo_url, branch, token, path_filter)
    return await fetch_github(repo_url, branch, token, path_filter)
