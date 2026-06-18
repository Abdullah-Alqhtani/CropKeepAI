import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Product

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRODUCT_CATALOG_FILE = DATA_DIR / "product_catalog_mar6.json"
CATEGORY_FILE = DATA_DIR / "product_catalog_categories.json"


def import_product_catalog(db: Session) -> None:
    if not PRODUCT_CATALOG_FILE.exists():
        return

    category_lookup = _load_category_lookup()
    rows = json.loads(PRODUCT_CATALOG_FILE.read_text(encoding="utf-8-sig"))
    for row in rows:
        code = _clean(row.get("产品ID"))
        name = _clean(row.get("产品名称"))
        if not name:
            continue

        product = None
        if code:
            product = db.query(Product).filter(Product.product_code == code).first()
        if not product:
            product = db.query(Product).filter(Product.name == name).first()

        category_tags = category_lookup.get(name, [])
        payload = {
            "product_code": code,
            "name": name,
            "english_name": _clean(row.get("英文名称")),
            "product_type": _clean(row.get("产品类型")),
            "active_ingredient": _clean(row.get("主要成分")) or _clean(row.get("产品类型")) or "Not specified",
            "usage_instructions": _first_present(row, ["使用方法和剂量", "中文使用说明", "使用方法(兑水)"]),
            "target_disease": _extract_target_disease(row),
            "safety_notes": _extract_safety_notes(row),
            "tags": _build_tags(row, category_tags),
            "crops": _clean(row.get("对应农作物/植物")),
            "specification": _clean(row.get("规格")),
            "source": _clean(row.get("数据来源")),
        }

        if product:
            for key, value in payload.items():
                setattr(product, key, value)
        else:
            db.add(Product(**payload))
    db.commit()


def _load_category_lookup() -> dict[str, list[str]]:
    if not CATEGORY_FILE.exists():
        return {}
    data = json.loads(CATEGORY_FILE.read_text(encoding="utf-8-sig"))
    lookup: dict[str, list[str]] = {}
    for row in data.get("product_catalog_chinese_to_engl", []):
        name = _clean(row.get("产品名称"))
        if not name:
            continue
        tags = [
            _clean(row.get("一级分类")),
            _clean(row.get("Primary Category")),
            _clean(row.get("二级分类")),
            _clean(row.get("Secondary Category")),
            _clean(row.get("Product Name")),
        ]
        lookup[name] = [tag for tag in tags if tag]
    return lookup


def _first_present(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = _clean(row.get(key))
        if value:
            return value
    return "Follow label directions and local agricultural regulations."


def _extract_target_disease(row: dict) -> str:
    text = _clean(row.get("中文使用说明"))
    markers = ["核心防治对象", "核心功效", "防治对象"]
    for marker in markers:
        if marker in text:
            return text[:260]
    return _clean(row.get("产品类型")) or "Crop disease management"


def _extract_safety_notes(row: dict) -> str:
    text = _clean(row.get("中文使用说明"))
    marker = "注意事项"
    if marker in text:
        return text[text.find(marker) :][:500]
    return "Follow the product label, wear protective equipment, and observe local regulations."


def _build_tags(row: dict, category_tags: list[str]) -> str:
    fields = [
        row.get("产品ID"),
        row.get("产品名称"),
        row.get("英文名称"),
        row.get("产品类型"),
        row.get("对应农作物/植物"),
        row.get("主要成分"),
        row.get("中文使用说明"),
    ]
    text = " ".join(_clean(field) for field in fields if _clean(field))
    compact = " ".join(text.split())
    tags = category_tags + [compact[:900]]
    return " | ".join(tag for tag in tags if tag)


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()
