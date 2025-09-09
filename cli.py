import argparse
from pathlib import Path


def positive_path(p: str) -> Path:
    """
        argparse converter: expand ~, resolve, and ensure the path exists
    """
    path = Path(p).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"Path {p} does not exist")

    return path


def main(argv=None) -> int:
    """
        Entry point for the kintsugi command
    """
    parser = argparse.ArgumentParser(
        prog="kintsugi",
        description="Kintsugi: offline, receipts-first recovery agent."
    )

    # We'll eventually have multiple commands; start with 'recover'
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("recover", help="Recover fragments from a folder")
    rec.add_argument("root", type=positive_path, help="Folder to scan")

    # Modes: strict (verbatim only) vs creative (tiny bridges, marked).
    rec.add_argument("--strict", action="store_true", help="Verbatim-only reconstruction")
    rec.add_argument("--creative", action="store_true", help="Allow minimal bridges (marked)")

    args = parser.parse_args(argv)

    if args.command == "recover":

        if args.strict and args.creative:
            parser.error("Cannot use both strict and creative modes")
        
        mode = "strict" if args.strict or not args.creative else "creative"
        print(f"[kintsugi] starting recovery in {args.root} (mode: {mode})")

        # Placeholder: next steps will implement scanning + merging.
        return 0

    # Fallback; argparse would have errored earlier, but keep explicit.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())