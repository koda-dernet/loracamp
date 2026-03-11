import argparse
from pathlib import Path
from .engine import LoraCampEngine

def main():
    parser = argparse.ArgumentParser(description="LoraCamp: Static Site Generator for Models")
    parser.add_argument("catalog", type=str, help="Path to your model catalog directory")
    parser.add_argument("--build", action="store_true", help="Build the site")
    parser.add_argument("--cdn-url", type=str, help="Optional CDN URL for large files")
    parser.add_argument("--output", type=str, default=".", help="Output directory (default: current)")
    parser.add_argument(
        "--include", action="append", dest="include_patterns", metavar="PATTERN",
        help="Only process paths containing this pattern (can be used multiple times)"
    )
    parser.add_argument(
        "--exclude", action="append", dest="exclude_patterns", metavar="PATTERN",
        help="Skip paths containing this pattern (can be used multiple times)"
    )

    args = parser.parse_args()

    catalog_path = Path(args.catalog).resolve()
    output_path = Path(args.output).resolve()
    
    if args.build:
        engine = LoraCampEngine(
            catalog_dir=catalog_path,
            output_dir=output_path,
            cdn_url=args.cdn_url,
            include_patterns=args.include_patterns,
            exclude_patterns=args.exclude_patterns,
        )
        engine.build()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
