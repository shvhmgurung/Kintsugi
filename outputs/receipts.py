from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json

from assemble.fragments import Fragment


def fragments_to_receipts(fragments: List[Fragment]) -> List[Dict[str, Any]]:
    """
    Convert internal Fragment records to the JSON schema we agreed.
    LLM block is filled later; for strict MVP, used=False.
    """
    out: List[Dict[str, Any]] = []

    for f in fragments:
        out.append({
            "fragment_id": f.fragment_id,
            "source_type": "file",              # for now; later: autosave|git|editor_undo|image_carve
            "path": str(f.path),
            "line_start": f.line_start,
            "line_end": f.line_end,
            "byte_start": f.byte_start,
            "byte_end": f.byte_end,
            "mtime": f.mtime_iso,
            "confidence": f.confidence,
            "raw_sha256": f.raw_sha256,
            "content_sha256": f.content_sha256,
            "trust": f.trust,                  # Recovered | Aligned | Bridged
            "llm": {
                "used": False,
                "model": None,
                "tokens_in": 0,
                "tokens_out": 0,
                "duration_ms": 0
            }
        })
        
    return out

def write_receipts_json(dest: Path, receipts: List[dict]) -> None:
    dest.write_text(json.dumps(receipts, indent=2, ensure_ascii=False))