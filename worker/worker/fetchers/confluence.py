"""
Confluence Server fetcher.
Находит страницы в указанном space, скачивает draw.io вложения.
draw.io хранит файлы с mediaType "application/vnd.jgraph.mxfile" (без расширения).
Basic auth: token field = "username:password"
"""
import logging

import httpx

log = logging.getLogger(__name__)


def _basic_auth(token: str) -> tuple[str, str]:
    """Разбирает 'username:password' → (username, password)."""
    if ":" not in token:
        raise ValueError("Confluence token must be in 'username:password' format")
    username, password = token.split(":", 1)
    return username, password


async def fetch_drawio_attachments(
    base_url: str,
    space_key: str,
    token: str,
    page_filter: str | None = None,
) -> list[dict]:
    """
    Возвращает список draw.io вложений со всех страниц space.
    Каждый элемент: {page_title, page_id, page_url, filename, content}
    """
    base_url = base_url.rstrip("/")
    username, password = _basic_auth(token)
    auth = (username, password)

    results = []

    async with httpx.AsyncClient(auth=auth, verify=False, timeout=30) as client:
        # Перебираем страницы с пагинацией
        start = 0
        limit = 25
        while True:
            params: dict = {
                "spaceKey": space_key,
                "type": "page",
                "start": start,
                "limit": limit,
            }
            if page_filter:
                params["title"] = page_filter

            r = await client.get(f"{base_url}/rest/api/content", params=params)
            r.raise_for_status()
            data = r.json()
            pages = data.get("results", [])

            for page in pages:
                page_id = page["id"]
                page_title = page["title"]
                log.info(f"Checking page: {page_title} ({page_id})")

                # Получаем вложения страницы с метаданными
                att_r = await client.get(
                    f"{base_url}/rest/api/content/{page_id}/child/attachment",
                    params={"limit": 50, "expand": "metadata.mediaType,metadata.labels"},
                )
                att_r.raise_for_status()

                for att in att_r.json().get("results", []):
                    title = att.get("title", "")
                    media_type = att.get("metadata", {}).get("mediaType", "")
                    labels = [
                        lbl.get("name")
                        for lbl in att.get("metadata", {}).get("labels", {}).get("results", [])
                    ]

                    # draw.io: mediaType vnd.jgraph.mxfile, или расширение .xml/.drawio, или label "drawio"
                    is_drawio = (
                        "vnd.jgraph.mxfile" in media_type
                        or title.endswith(".xml")
                        or title.endswith(".drawio")
                        or "drawio" in labels
                    )
                    if not is_drawio:
                        continue

                    # Скачиваем вложение
                    dl_url = f"{base_url}/rest/api/content/{att['id']}/download"
                    dl_r = await client.get(dl_url)
                    dl_r.raise_for_status()
                    content = dl_r.text

                    # Проверяем что это draw.io XML (может быть обёрнут в <mxfile>)
                    if "<mxGraphModel" not in content and "<mxfile" not in content:
                        continue

                    log.info(f"  Found draw.io: {title}")
                    results.append({
                        "page_title": page_title,
                        "page_id": page_id,
                        "page_url": f"{base_url}/pages/viewpage.action?pageId={page_id}",
                        "filename": title,
                        "content": content,
                    })

            # Пагинация
            total = data.get("totalSize", len(pages))
            start += limit
            if start >= total or not pages:
                break

    log.info(f"Confluence: found {len(results)} draw.io diagrams in space '{space_key}'")
    return results
