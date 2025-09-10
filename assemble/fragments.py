from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterable, Tuple
import hashlib
import re



@dataclass
class Fragment:
    fragment_id: str          # stable id we assign (e.g., frag_000123)
    path: Path                # source file path
    source_type: str          # e.g., "file" for now; later: autosave, git, editor_undo
    line_start: int           # 1-based paragraph start line in the source
    line_end: int             # 1-based paragraph end line in the source
    byte_start: int           # byte offset of the paragraph start
    byte_end: int             # byte offset of the paragraph end
    mtime_iso: str            # ISO timestamp from the scanner
    confidence: float         # initial heuristic (we’ll tune later)
    raw_sha256: str           # hash of the exact source bytes of this paragraph
    content_sha256: str       # hash after normalization (whitespace/newlines)
    text: str                 # normalized paragraph text
    trust: str                # "Recovered" | "Aligned" | "Bridged" (strict = Recovered)


# Different encodings/newlines produce “same meaning, different bytes”.
def _normalise_text(s: str) -> str:
    
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    
    return s.strip("\n")


# Split into paragraphs by blank lines (simple, robust)
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n", flags=re.MULTILINE)


def _split_into_paragraphs(full_text: str) -> List[Tuple[int, int, str]]:
    """
    Returns a list of tuples: (line_start, line_end, paragraph_text).
    line numbers are 1-based to be user-friendly in receipts.
    """
    lines = full_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: List[Tuple[int, int, str]] = []
    start = 0
    i = 0
    # Scan for blank-line boundaries
    while i < len(lines):

        if lines[i].strip() == "":

            if start < i:
                para_lines = lines[start:i]
                out.append((start + 1, i, "\n".join(para_lines)))
            # skip consecutive blanks
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            start = i
            continue

        i += 1
    # Tail paragraph
    if start < len(lines):
        out.append((start + 1, len(lines), "\n".join(lines[start:len(lines)])))
    
    return out


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_to_fragments(
    path: Path,
    mtime_iso: str,
    source_type: str = "file",
    base_confidence: float = 0.70,
) -> List[Fragment]:
    """
    Read a text file, split into paragraphs, compute byte/line ranges and hashes,
    and return Fragment records (strict mode defaults to trust='Recovered').
    """
    data = path.read_bytes()  # we assume scanner already filtered as text-like
    text = ""
    # Best-effort decode: try utf-8 first, then UTF-16 LE/BE
    for enc in ("utf-8", "utf-16-le", "utf-16-be"):

        try:
            text = data.decode(enc)
            break

        except UnicodeDecodeError:
            continue

    if not text:
        # As a fallback, ignore undecodable files
        return []

    # For byte offsets we need to map paragraph slices back to bytes.
    # Strategy: rebuild by encoding slices as utf-8 and tracking cumulative byte lengths.
    # NOTE: This is a approximation if original encoding wasn’t utf-8.
    paragraphs = _split_into_paragraphs(text)
    fragments: List[Fragment] = []

    cum_bytes = 0
    # Precompute byte lengths per line with utf-8 re-encode for approximate offsets
    utf8_lines = [ (ln + "\n").encode("utf-8") for ln in text.replace("\r\n","\n").replace("\r","\n").split("\n") ]
    byte_offsets = [0]
    
    for b in utf8_lines:
        byte_offsets.append(byte_offsets[-1] + len(b))
    # Now for each paragraph, compute start/end byte offsets from line indices
    for idx, (line_start, line_end, para_text) in enumerate(paragraphs, start=1):
        # Map 1-based line indices to byte offsets
        bs = byte_offsets[line_start - 1]
        be = byte_offsets[line_end]  # exclusive
        # Raw bytes slice based on utf-8 mapping (approx)
        raw_slice = b"".join(utf8_lines[line_start - 1: line_end])
        raw_sha = _sha256_bytes(raw_slice)
        norm = _normalise_text(para_text)
        content_sha = _sha256_bytes(norm.encode("utf-8"))

        frag = Fragment(
            fragment_id=f"frag_{idx:06d}",
            path=path,
            source_type=source_type,
            line_start=line_start,
            line_end=line_end,
            byte_start=bs,
            byte_end=be,
            mtime_iso=mtime_iso,
            confidence=base_confidence,
            raw_sha256=raw_sha,
            content_sha256=content_sha,
            text=norm,
            trust="Recovered",  # strict mode
        )
        # Skip empty paragraphs post-normalization
        if frag.text.strip():
            fragments.append(frag)

    return fragments