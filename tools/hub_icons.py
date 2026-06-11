#!/usr/bin/env python3
"""人気カード用アイコン解決（用語辞典・学習ガイド・キャリア共通）。"""

from __future__ import annotations

import json
import re
from typing import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "images"
ALIASES_FILE = ROOT / "data" / "hub-icon-aliases.json"
ICON_EXTS = (".svg", ".png", ".webp", ".jpg")

PREFIX_VENDOR = (
    ("claude-", "Anthropic"),
    ("gpt-", "OpenAI"),
    ("gemini-", "Google"),
)


def load_featured_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_section_aliases(section: str) -> dict:
    if not ALIASES_FILE.is_file():
        return {"vendors": {}, "terms": {}}
    data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    block = data.get(section) or {}
    if section == "glossary":
        return {
            "vendors": block.get("vendors") or {},
            "terms": block.get("terms") or {},
        }
    return {"vendors": {}, "terms": block.get("terms") or {}}


def build_featured(
    featured_ids: list[str],
    *,
    resolve_icon: Callable[[str, dict], str | None],
    context_by_id: dict[str, dict],
    is_live: Callable[[str], bool],
    label: str = "featured",
) -> tuple[list[str], list[dict]]:
    featured: list[dict] = []
    for item_id in featured_ids:
        ctx = context_by_id.get(item_id)
        if not ctx:
            print(f"warn: {label} id not found: {item_id}")
            continue
        if not is_live(item_id):
            print(f"warn: {label} id not published: {item_id}")
            continue
        entry: dict = {"id": item_id}
        icon = resolve_icon(item_id, ctx)
        if icon:
            entry["icon"] = icon
        featured.append(entry)
    return [item["id"] for item in featured], featured


def rel_image(path: Path) -> str | None:
    try:
        return path.relative_to(IMAGES).as_posix()
    except ValueError:
        return None


def first_existing_dir(base: Path, names: list[str]) -> Path | None:
    for name in names:
        for ext in ICON_EXTS:
            candidate = base / f"{name}{ext}"
            if candidate.is_file():
                return candidate
    return None


def first_existing_glob(base: Path, patterns: list[str]) -> Path | None:
    if not base.is_dir():
        return None
    for pattern in patterns:
        for candidate in sorted(base.glob(pattern)):
            if candidate.is_file():
                return candidate
    return None


def resolve_glossary_icon(term_id: str, csv_row: dict, aliases: dict) -> str | None:
    terms_map = aliases.get("terms") or {}
    if term_id in terms_map:
        return terms_map[term_id]

    found = first_existing_dir(IMAGES / "glossary", [term_id])
    if found:
        return rel_image(found)

    notes = csv_row.get("notes") or ""
    vendor_match = re.search(r"開発元:\s*(.+)", notes)
    vendors = aliases.get("vendors") or {}
    if vendor_match:
        vendor = vendor_match.group(1).strip()
        if vendor in vendors:
            return vendors[vendor]

    for prefix, vendor in PREFIX_VENDOR:
        if term_id.startswith(prefix) and vendor in vendors:
            return vendors[vendor]

    category = csv_row.get("category") or ""
    found = first_existing_dir(IMAGES / "glossary" / "categories", [category])
    if found:
        return rel_image(found)

    return None


def resolve_guide_icon(article_id: str, category: str, aliases: dict) -> str | None:
    terms_map = aliases.get("terms") or {}
    if article_id in terms_map:
        return terms_map[article_id]

    found = first_existing_dir(IMAGES / "guide" / article_id, ["icon"])
    if found:
        return rel_image(found)

    if category.startswith("g-kentei"):
        found = first_existing_dir(IMAGES / "guide" / "categories", ["g-kentei"])
        if found:
            return rel_image(found)

    if category.startswith("genai"):
        found = first_existing_dir(IMAGES / "guide" / "categories", ["genai"])
        if found:
            return rel_image(found)

    found = first_existing_dir(IMAGES / "guide" / "categories", [category])
    if found:
        return rel_image(found)

    return None


def resolve_career_icon(article_id: str, category: str, aliases: dict) -> str | None:
    terms_map = aliases.get("terms") or {}
    if article_id in terms_map:
        return terms_map[article_id]

    found = first_existing_glob(
        IMAGES / "career" / article_id,
        ["role-*.png", "role_*.png", "role*.png", "icon.svg", "icon.png"],
    )
    if found:
        return rel_image(found)

    found = first_existing_dir(IMAGES / "career" / "categories", [category])
    if found:
        return rel_image(found)

    return None
