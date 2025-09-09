
# Kintsugi

> The art of digital memory repair – now with 95% less shame.

## What is Kintsugi?

**Kintsugi** is your over-engineered, possibly paranoid, definitely-too-personal attempt at forensic digital recovery. Inspired by the Japanese art of repairing broken pottery with gold, we try to do the same with your digital footprints – stitching together a map of the past from whatever crumbs, caches, and cosmic accidents you left behind.

### Not just undelete. This is resurrection.

We don't just "undelete" files. We **hunt**, **scan**, **infer**, and **guess** our way back to what once was. Even if you:

- Deleted the file.
- Forgot to save it.
- Watched it vanish in a panic-induced cleanup.
- Had no idea you ever wrote it in the first place.

## Why?

Because sometimes all that’s left is the ghost of a thought.

And also because some hackathon judge said, “Make something magical.”

So we did.

## Core Idea

Kintsugi tries to **reconstruct meaningful digital fragments** from:

- Autosave/Recovery files.
- Recently opened file lists (VS Code, Word, etc).
- Editor undo stacks (if accessible).
- OS-level temp folders and shadow copies.
- Browser caches and localStorage.
- PDF viewers, image editors, Figma temp dirs.
- AI tool logs (you heard us).

We look for **cracks** – not files. And then we fill them with gold.

## Current Plan

### Phase 1: Local Forensics MVP (Mac-first)

- [x] Parse VS Code `storage.json` to get recent file list
- [x] Scan `~/Library/Application Support/Code/` for workspace data
- [x] Search for deleted `.txt`, `.md`, `.json` files in known temp dirs
- [ ] Extract file metadata (e.g., modified time, preview text, etc.)
- [ ] Recover from undo history (VS Code, Obsidian, Notes)
- [ ] Build local timeline graph of file creation/deletion

### Phase 2: Cross-platform & OSS Dataset Stitching

- [ ] Linux: Scan `.config`, `.cache`, `.local/share`, Snap/Flatpak dirs
- [ ] Windows: Recover AppData + Registry MRU keys
- [ ] Build KintsugiDB – a local index of known apps and their trace signatures

### Phase 3: Memory-Laced UX

- [ ] Local timeline UI (react or TUI)
- [ ] Search by fuzzy memory: “that .md file I wrote about frogs last month”
- [ ] Tag fragments by app/source/score
- [ ] Reconstruct fragments into stitched previews

## Tech Stack (Current)

- Python (for file parsing & crawling)
- SQLite (local artifact DB)
- macOS APIs (Spotlight, FSEvents)
- Optional: Rust modules for performance crawling

## Known Limitations

- Can't read your mind (yet)
- If you used Incognito Mode for everything… lol good luck
- Some editor histories are locked/encrypted (working on workarounds)

## Cool Stretch Ideas

- Recover unsaved content from RAM snapshots or hibernation files
- Hook into Spotlight/FSEvents for passive monitoring
- “Undo-based resurrection” – walk the undo stack from cache dirs
- GitHub Copilot/Gemini cache sniffing? Maybe.
- AI auto-tagging: "this file smells like a breakup letter"

## What Makes This Different?

Most recovery tools try to undelete files.

We try to recover **narratives**.

Kintsugi isn’t for everyone. It’s for the forgetful poet. The midnight coder. The panic-deleter. The version-history-hater. The "did I dream that doc?" kid.

If you lost it, we’ll try to remember it with you.

---

## Status

In active madness.
