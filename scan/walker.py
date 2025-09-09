from __future__ import annotations
import os 
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, Optional



# --- Tunables we'll evolve later ---
TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".rst",
    ".json", ".yaml", ".yml", ".toml",
    ".log",  # we'll soft-cap logs later
    ".bak", ".tmp", ".swp", ".md~",
}

DEFAULT_MAX_BYTES = 300 * 1024 * 1024   # 300 MB global cap
DEFAULT_TIME_BUDGET_S = 120             # 120 seconds soft cap
SAMPLE_BYTES = 4096                     # small probe read per file



@dataclass
class Candidate:
    path: Path
    size: int
    mtime_iso: str


def _is_symlink(p: os.DirEntry) -> bool:

    try:
        return p.is_symlink()
    
    except OSError:
        return False


def _looks_like_text(path: Path) -> bool:
    """
    Heuristic: read a small head sample and try UTF-8/UTF-16; reject if NUL-heavy.
    """
    try:
        with path.open("rb") as f:
            chunk = f.read(SAMPLE_BYTES)
    
    except (OSError, PermissionError):
        return False
    
    if not chunk:
        return False

    # NUL-heavy usually means binary (e.g., images, executables)
    if chunk.count(b"\x00") > len(chunk) // 16:
        return False

    # Try UTF-8 first, then UTF-16 LE/BE
    for enc in ("utf-8", "utf-16-le", "utf-16-be"):
        try:
            chunk.decode(enc)
            return True
        except UnicodeDecodeError:
            continue
    return False


def _is_cloud_placeholder(path: Path) -> bool:
    """
    Minimal placeholder detection:
    - macOS iCloud: .icloud suffix or under Mobile Documents and not downloaded
    - Windows OneDrive: skip known placeholder files by suffix .cloud/.lnk heuristics (basic)
    NOTE: We’ll refine with platform APIs later.
    """
    name = path.name.lower()

    if name.endswith(".icloud"):
        return True
    
    # crude OneDrive/placeholder hints (better detection comes later)
    if name.endswith(".cloud") or name.endswith(".lnk") or name.startswith(".cloudf"):
        return True
    
    # If the file lives in a Mobile Documents/iCloud path and is tiny with no text, skip
    parts = [p.lower() for p in path.parts]

    if "mobile documents" in " ".join(parts) and not _looks_like_text(path):
        return True
    return False


def _ext_allows_consideration(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS


def walk_candidates(
    roots: Iterable[Path],
    max_bytes: int = DEFAULT_MAX_BYTES,
    time_budget_s: int = DEFAULT_TIME_BUDGET_S,
    follow_symlinks: bool = False,
) -> Generator[Candidate, None, dict]:
    """
    Breadth-first directory walk that yields text-like file candidates
    within time/byte budgets. Returns a summary dict when exhausted.
    """
    start = time.time()
    total_files = 0
    total_bytes_read = 0
    skipped_cloud = 0
    skipped_symlink = 0
    skipped_binary = 0

    q: deque[Path] = deque()
    seen_dirs: set[tuple[int, int]] = set()  # (dev, ino) to avoid loops

    for r in roots:
        q.append(r)

    while q:
        # Time budget check
        if time.time() - start > time_budget_s:
            break

        current = q.popleft()

        # Deduplicate directories by (device,inode) to avoid loops/junctions
        try:
            stat = current.stat()
            key = (stat.st_dev, stat.st_ino)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
        except OSError:
            continue

        try:
            with os.scandir(current) as it:
                for entry in it:
                    # Budget check each loop to be responsive
                    if time.time() - start > time_budget_s:
                        raise TimeoutError

                    try:
                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            q.append(Path(entry.path))
                            continue
                    except OSError:
                        continue

                    # Skip symlinked files by default
                    if not follow_symlinks and _is_symlink(entry):
                        skipped_symlink += 1
                        continue

                    # Files only from here
                    try:
                        if not entry.is_file(follow_symlinks=follow_symlinks):
                            continue
                    except OSError:
                        continue

                    path = Path(entry.path)

                    # Extension pre-filter (cheap)
                    if not _ext_allows_consideration(path):
                        continue

                    # Skip cloud placeholders (basic)
                    if _is_cloud_placeholder(path):
                        skipped_cloud += 1
                        continue

                    # Text probe read
                    if not _looks_like_text(path):
                        skipped_binary += 1
                        continue

                    try:
                        st = entry.stat()
                        size = st.st_size
                        mtime_iso = time.strftime(
                            "%Y-%m-%dT%H:%M:%S%z", time.localtime(st.st_mtime)
                        )
                    except OSError:
                        continue

                    # Global byte budget
                    total_files += 1
                    total_bytes_read += min(size, SAMPLE_BYTES)
                    yield Candidate(path=path, size=size, mtime_iso=mtime_iso)

                    if total_bytes_read >= max_bytes:
                        raise MemoryError  # use as a signal to stop early

        except TimeoutError:
            break
        except MemoryError:
            break
        except (OSError, PermissionError):
            continue

    return {
        "elapsed_s": round(time.time() - start, 3),
        "files_seen": total_files,
        "sampled_bytes": total_bytes_read,
        "skipped_cloud": skipped_cloud,
        "skipped_symlink": skipped_symlink,
        "skipped_binary": skipped_binary,
    }
