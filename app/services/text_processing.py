from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    section_path: str
    content: str
    content_hash: str


BB_CODE = re.compile(r"\[/?[a-zA-Z*][^\]]*\]")
HTML_TAG = re.compile(r"<[^>]+>")
HEADING = re.compile(r"^(?:#{1,6}\s+|\[h[1-6]\].*?\[/h[1-6]\]|={2,}.+={2,})", re.I)


def clean_steam_content(content: str) -> str:
    value = html.unescape(content or "")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = HTML_TAG.sub(" ", value)
    value = BB_CODE.sub(" ", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _split_long_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s*", block)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks or [block[:max_chars]]


def chunk_document(
    *,
    title: str,
    content: str,
    max_chars: int = 1200,
    min_chars: int = 80,
) -> list[TextChunk]:
    cleaned = clean_steam_content(content)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", cleaned) if block.strip()]
    section = title.strip() or "Untitled"
    pending: list[str] = []
    output: list[TextChunk] = []

    def flush() -> None:
        nonlocal pending
        text = "\n\n".join(pending).strip()
        if not text:
            return
        for part in _split_long_block(text, max_chars):
            if len(part) < min_chars and output:
                previous = output[-1]
                merged = f"{previous.content}\n\n{part}"
                output[-1] = TextChunk(
                    chunk_index=previous.chunk_index,
                    section_path=previous.section_path,
                    content=merged,
                    content_hash=hashlib.sha256(merged.encode()).hexdigest(),
                )
            else:
                output.append(
                    TextChunk(
                        chunk_index=len(output),
                        section_path=section,
                        content=part,
                        content_hash=hashlib.sha256(part.encode()).hexdigest(),
                    )
                )
        pending = []

    for block in blocks:
        first_line = block.splitlines()[0].strip()
        looks_like_heading = bool(HEADING.match(first_line)) or (
            len(first_line) <= 80 and len(block.splitlines()) == 1 and not first_line.endswith(".")
        )
        if looks_like_heading:
            flush()
            section = f"{title} > {first_line}" if first_line != title else title
            continue
        if pending and len("\n\n".join(pending)) + len(block) > max_chars:
            flush()
        pending.append(block)
    flush()
    return output
