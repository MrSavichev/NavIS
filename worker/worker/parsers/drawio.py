"""
draw.io XML parser.
Извлекает сущности (верхнеуровневые узлы) и рёбра (связи с протоколом/направлением).
Поддерживает оба формата хранения: plain XML и base64+deflate (сжатый <diagram>).
"""
import base64
import logging
import re
import zlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class DrawioEntity:
    cell_id: str
    name: str


@dataclass
class DrawioEdge:
    source_name: str
    target_name: str
    label: str          # протокол + направление из диаграммы, напр. "REST/POST →"


@dataclass
class DrawioResult:
    entities: list[DrawioEntity] = field(default_factory=list)
    edges: list[DrawioEdge] = field(default_factory=list)


def _strip_html(text: str) -> str:
    """Убирает HTML-теги из значений ячеек draw.io."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#xa;", " ")
    return text.strip()


def _decompress_diagram(encoded: str) -> str | None:
    """
    draw.io хранит <diagram> в двух форматах:
    1. Plain XML (внутри — <mxGraphModel ...>)
    2. base64(deflate(url-encoded(XML))) — compressed формат

    Возвращает XML-строку или None при ошибке.
    """
    encoded = encoded.strip()
    if not encoded:
        return None
    try:
        compressed = base64.b64decode(encoded)
        # raw deflate (без zlib-заголовка)
        xml_bytes = zlib.decompress(compressed, -zlib.MAX_WBITS)
        from urllib.parse import unquote
        return unquote(xml_bytes.decode("utf-8"))
    except Exception:
        return None


def parse_drawio_xml(xml_content: str) -> DrawioResult:
    """
    Парсит draw.io XML.
    - Сущности: vertex="1", parent=layer_id (верхний уровень)
    - Рёбра: edge="1" с source и target
    Поддерживает <mxfile> обёртку со сжатым или plain <diagram>.
    """
    result = DrawioResult()

    xml_content = xml_content.strip()

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        log.warning(f"XML parse error: {e}")
        return result

    # Найти mxGraphModel (может быть корнем или вложенным)
    if root.tag == "mxGraphModel":
        graph_model = root
    else:
        # Попробуем найти вложенный <mxGraphModel> (plain XML внутри <diagram>)
        graph_model = root.find(".//mxGraphModel")
        if graph_model is None:
            # Контент внутри <diagram> может быть сжат (base64+deflate)
            diagram_el = root.find(".//diagram")
            if diagram_el is not None and diagram_el.text:
                decompressed = _decompress_diagram(diagram_el.text)
                if decompressed:
                    try:
                        inner = ET.fromstring(decompressed)
                        graph_model = inner if inner.tag == "mxGraphModel" else inner.find(".//mxGraphModel")
                    except ET.ParseError as e:
                        log.warning(f"Decompressed XML parse error: {e}")
            if graph_model is None:
                log.warning("No mxGraphModel found (tried plain and compressed)")
                return result

    cells = graph_model.findall(".//mxCell")

    # Найти layer cell: parent="0" → это обычно id="1"
    layer_id = None
    for cell in cells:
        if cell.get("parent") == "0":
            layer_id = cell.get("id")
            break

    if layer_id is None:
        log.warning("No layer cell found in draw.io XML")
        return result

    # Карта cell_id → name для сущностей верхнего уровня
    entity_map: dict[str, str] = {}

    for cell in cells:
        if (
            cell.get("vertex") == "1"
            and cell.get("parent") == layer_id
        ):
            raw_value = cell.get("value", "")
            name = _strip_html(raw_value)
            if name:
                entity_map[cell.get("id")] = name
                result.entities.append(DrawioEntity(cell_id=cell.get("id"), name=name))

    # Рёбра
    for cell in cells:
        if cell.get("edge") != "1":
            continue
        source_id = cell.get("source")
        target_id = cell.get("target")
        if not source_id or not target_id:
            continue

        source_name = entity_map.get(source_id)
        target_name = entity_map.get(target_id)
        if not source_name or not target_name:
            continue

        label = _strip_html(cell.get("value", "")).strip() or "depends"
        result.edges.append(DrawioEdge(
            source_name=source_name,
            target_name=target_name,
            label=label,
        ))

    log.info(f"draw.io: {len(result.entities)} entities, {len(result.edges)} edges")
    return result


def match_entity_to_service(name: str, services: list) -> str | None:
    """
    Сопоставляет имя сущности из draw.io с сервисом в каталоге.
    Возвращает service.id или None.
    Стратегия: точное → без регистра → partial containment.
    """
    name_lower = name.lower().replace("-", "").replace("_", "").replace(" ", "")

    for svc in services:
        svc_lower = svc.name.lower().replace("-", "").replace("_", "").replace(" ", "")
        if name_lower == svc_lower:
            return svc.id

    # Partial match: имя диаграммы содержит имя сервиса или наоборот
    for svc in services:
        svc_lower = svc.name.lower().replace("-", "").replace("_", "").replace(" ", "")
        if name_lower in svc_lower or svc_lower in name_lower:
            return svc.id

    return None
