#!/usr/bin/env python3
"""Preview or apply reading metadata and gojuon filing for Markdown notes.

The command is a dry run unless --apply is supplied. It uses only Python's
standard library and never calls a network service.
"""

from __future__ import annotations

import argparse
import codecs
import json
import os
import re
import stat
import tempfile
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


FOLDERS = tuple("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")
FOLDER_SET = set(FOLDERS)
BASE_KANA = str.maketrans(
    {
        "が": "か", "ぎ": "き", "ぐ": "く", "げ": "け", "ご": "こ",
        "ざ": "さ", "じ": "し", "ず": "す", "ぜ": "せ", "ぞ": "そ",
        "だ": "た", "ぢ": "ち", "づ": "つ", "で": "て", "ど": "と",
        "ば": "は", "び": "ひ", "ぶ": "ふ", "べ": "へ", "ぼ": "ほ",
        "ぱ": "は", "ぴ": "ひ", "ぷ": "ふ", "ぺ": "へ", "ぽ": "ほ",
        "ゔ": "う", "ぁ": "あ", "ぃ": "い", "ぅ": "う", "ぇ": "え",
        "ぉ": "お", "っ": "つ", "ゃ": "や", "ゅ": "ゆ", "ょ": "よ",
        "ゎ": "わ", "ゕ": "か", "ゖ": "け",
    }
)
FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---[ \t]*(?P<after>\r?\n|\Z)",
    re.DOTALL,
)
KANA_RE = re.compile(r"[ぁ-ゖァ-ヺー]+")
KANA_ONLY_RE = re.compile(r"^[ぁ-ゖァ-ヺー・･\s‐－—]+$")
BRACKET_RE = re.compile(r"(?<!\[)\[(?!\[)([^\]\r\n]{1,100})\]")


@dataclass
class Plan:
    path: str
    reading: str | None
    source: str
    destination: str | None
    add_reading: bool
    collision: bool


def read_utf8(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    return raw.decode("utf-8-sig"), raw.startswith(codecs.BOM_UTF8)


def write_utf8(path: Path, text: str, had_bom: bool) -> None:
    raw = text.encode("utf-8")
    payload = (codecs.BOM_UTF8 if had_bom else b"") + raw
    original_mode = stat.S_IMODE(path.stat().st_mode)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".kotoba-vault.tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.chmod(temporary_name, original_mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def katakana_to_hiragana(value: str) -> str:
    result: list[str] = []
    for character in value:
        code = ord(character)
        result.append(chr(code - 0x60) if 0x30A1 <= code <= 0x30F6 else character)
    return "".join(result)


def clean_reading(value: object) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else ""
    text = unicodedata.normalize("NFKC", str(value or "")).strip().strip("\"'")
    if not text:
        return None
    runs = KANA_RE.findall(text)
    return katakana_to_hiragana("".join(runs)) or None


def is_kana_only(value: object) -> bool:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().strip("\"'")
    return bool(text and KANA_ONLY_RE.fullmatch(text))


def parse_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    values: dict[str, object] = {}
    lines = match.group("body").splitlines()
    index = 0
    while index < len(lines):
        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$", lines[index])
        if not key_match:
            index += 1
            continue
        key, scalar = key_match.groups()
        if scalar:
            values[key] = scalar.strip().strip("\"'")
            index += 1
            continue
        items: list[str] = []
        index += 1
        while index < len(lines):
            item = re.match(r"^\s+-\s+(.*?)\s*$", lines[index])
            if not item:
                break
            items.append(item.group(1).strip().strip("\"'"))
            index += 1
        values[key] = items
    return values


def extract_reading(path: Path, text: str) -> tuple[str | None, str]:
    frontmatter = parse_frontmatter(text)
    reading = clean_reading(frontmatter.get("reading"))
    if reading:
        return reading, "reading"

    if is_kana_only(path.stem):
        return clean_reading(path.stem), "filename"

    for bracket in BRACKET_RE.findall(text[:1500]):
        if is_kana_only(bracket):
            return clean_reading(bracket), "brackets"

    aliases = frontmatter.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = [aliases]
    for alias in aliases:
        if is_kana_only(alias):
            return clean_reading(alias), "alias"
    return None, "unresolved"


def folder_for_reading(reading: str | None) -> str | None:
    if not reading:
        return None
    normalized = katakana_to_hiragana(unicodedata.normalize("NFKC", reading))
    match = re.search(r"[ぁ-ゖ]", normalized)
    if not match:
        return None
    folder = match.group(0).translate(BASE_KANA)
    return folder if folder in FOLDER_SET else None


def add_reading_property(text: str, reading: str) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    match = FRONTMATTER_RE.match(text)
    if not match:
        return f"---{newline}reading: {reading}{newline}---{newline}{newline}{text}"

    body = match.group("body")
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^reading\s*:", line, re.IGNORECASE):
            if line.split(":", 1)[1].strip():
                return text
            lines[index] = f"reading: {reading}"
            break
    else:
        alias_index = next(
            (index for index, line in enumerate(lines) if re.match(r"^aliases\s*:", line)),
            len(lines),
        )
        lines.insert(alias_index, f"reading: {reading}")

    replacement = newline.join(lines)
    return text[: match.start("body")] + replacement + text[match.end("body") :]


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def build_plans(root: Path) -> list[Plan]:
    plans: list[Plan] = []
    paths = sorted(root.rglob("*.md"), key=lambda item: str(item).casefold())
    existing = {relative(path, root).casefold(): relative(path, root) for path in paths}
    destination_counts: Counter[str] = Counter()

    for path in paths:
        text, _ = read_utf8(path)
        reading, source = extract_reading(path, text)
        folder = folder_for_reading(reading)
        destination = root / folder / path.name if folder else None
        source_relative = relative(path, root)
        destination_relative = relative(destination, root) if destination else None
        changed = bool(reading and add_reading_property(text, reading) != text)
        destination_key = destination_relative.casefold() if destination_relative else None
        collision = bool(
            destination_key
            and destination_key in existing
            and existing[destination_key].casefold() != source_relative.casefold()
        )
        if destination_key:
            destination_counts[destination_key] += 1
        plans.append(
            Plan(
                path=source_relative,
                reading=reading,
                source=source,
                destination=destination_relative,
                add_reading=changed,
                collision=collision,
            )
        )

    for plan in plans:
        if plan.destination and destination_counts[plan.destination.casefold()] > 1:
            plan.collision = True
    return plans


def print_report(plans: list[Plan]) -> None:
    sources = Counter(plan.source for plan in plans)
    print(f"Notes: {len(plans)}")
    print(f"Resolved: {sum(plan.reading is not None for plan in plans)}")
    print(f"Add reading: {sum(plan.add_reading for plan in plans)}")
    print(f"Unresolved: {sum(plan.reading is None for plan in plans)}")
    print(f"Collisions: {sum(plan.collision for plan in plans)}")
    print("Sources: " + ", ".join(f"{key}={value}" for key, value in sorted(sources.items())))


def apply_plans(
    root: Path,
    plans: list[Plan],
    add_reading: bool,
    move: bool,
    fail_on_unresolved: bool = False,
) -> None:
    collisions = [plan for plan in plans if plan.collision]
    if collisions:
        raise SystemExit("Destination collisions exist; nothing was changed.")
    if fail_on_unresolved and any(plan.reading is None for plan in plans):
        raise SystemExit("Unresolved readings exist; nothing was changed.")

    for plan in plans:
        if not plan.reading or not plan.destination:
            continue
        source = root / Path(plan.path)
        destination = root / Path(plan.destination)
        if add_reading and plan.add_reading:
            text, had_bom = read_utf8(source)
            write_utf8(source, add_reading_property(text, plan.reading), had_bom)
        if move and destination != source:
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Vocabulary root")
    parser.add_argument("--apply", action="store_true", help="Apply the plan")
    parser.add_argument("--no-reading", action="store_true", help="Do not add reading")
    parser.add_argument("--no-move", action="store_true", help="Do not move notes")
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help="Refuse all changes when any note has no reviewable reading",
    )
    parser.add_argument("--json", type=Path, help="Write the complete plan as JSON")
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    if not root.is_dir():
        parser.error(f"Vocabulary root does not exist: {root}")

    plans = build_plans(root)
    print_report(plans)
    if arguments.json:
        arguments.json.write_text(
            json.dumps([asdict(plan) for plan in plans], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if not arguments.apply:
        print("Dry run only; pass --apply to modify files.")
        return 1 if any(plan.collision for plan in plans) else 0

    apply_plans(
        root,
        plans,
        not arguments.no_reading,
        not arguments.no_move,
        arguments.fail_on_unresolved,
    )
    print("Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
