#!/usr/bin/env python3
"""Command-line interface for CloudMask."""

import argparse
import sys
from pathlib import Path

from ..exceptions import CloudMaskError
from ..logging import log_error, setup_logging
from .cli_handlers import (
    handle_anonymize,
    handle_batch,
    handle_init_config,
    handle_stats,
    handle_unanonymize,
    handle_validate,
)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="cloudmask",
        description="Anonymize AWS infrastructure identifiers for LLM processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cloudmask init-config -c config.yaml
  cloudmask anonymize -i input.txt -o anonymized.txt
  cloudmask anonymize --clipboard
  cloudmask unanonymize -i anonymized.txt -o output.txt
        """,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--log-file", type=Path, help="Write logs to file")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init config
    init_parser = subparsers.add_parser("init-config", help="Generate default config file")
    init_parser.add_argument("-c", "--config", type=Path, default="cloudmask.yaml")
    init_parser.add_argument("-t", "--template", default="standard")
    init_parser.add_argument("--list-templates", action="store_true")

    # Anonymize
    anon_parser = subparsers.add_parser("anonymize", help="Anonymize AWS identifiers")
    anon_parser.add_argument("-i", "--input", type=Path)
    anon_parser.add_argument("-o", "--output", type=Path)
    anon_parser.add_argument("-m", "--mapping", type=Path)
    anon_parser.add_argument("-c", "--config", type=Path)
    anon_parser.add_argument("--format", choices=["yaml", "json", "toml"])
    anon_parser.add_argument("--no-env", action="store_true")
    anon_parser.add_argument("-s", "--seed")
    anon_parser.add_argument("--clipboard", action="store_true")
    anon_parser.add_argument("--encrypt", action="store_true")
    anon_parser.add_argument("--password")
    anon_parser.add_argument("--stream", action="store_true")
    anon_parser.add_argument("--progress", action="store_true")

    # Unanonymize
    unanon_parser = subparsers.add_parser("unanonymize", help="Restore original identifiers")
    unanon_parser.add_argument("-i", "--input", type=Path)
    unanon_parser.add_argument("-o", "--output", type=Path)
    unanon_parser.add_argument("-m", "--mapping", type=Path)
    unanon_parser.add_argument("--clipboard", action="store_true")
    unanon_parser.add_argument("--encrypted", action="store_true")
    unanon_parser.add_argument("--password")
    unanon_parser.add_argument("--stream", action="store_true")
    unanon_parser.add_argument("--progress", action="store_true")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate configuration or mapping")
    validate_parser.add_argument("-c", "--config", type=Path)
    validate_parser.add_argument("-m", "--mapping", type=Path)
    validate_parser.add_argument("--format", choices=["yaml", "json", "toml"])
    validate_parser.add_argument("--encrypted", action="store_true")
    validate_parser.add_argument("--password")

    # Batch
    batch_parser = subparsers.add_parser("batch", help="Batch process multiple files")
    batch_parser.add_argument("files", nargs="+", type=Path)
    batch_parser.add_argument("-o", "--output-dir", required=True, type=Path)
    batch_parser.add_argument("-m", "--mapping", type=Path)
    batch_parser.add_argument("-c", "--config", type=Path)
    batch_parser.add_argument("-s", "--seed")
    batch_parser.add_argument("--encrypt", action="store_true")
    batch_parser.add_argument("--password")
    batch_parser.add_argument("--progress", action="store_true")

    # Stats
    stats_parser = subparsers.add_parser("stats", help="Show statistics about anonymization")
    stats_parser.add_argument("-m", "--mapping", required=True, type=Path)
    stats_parser.add_argument("--encrypted", action="store_true")
    stats_parser.add_argument("--password")
    stats_parser.add_argument("--detailed", action="store_true")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = (
        "ERROR"
        if args.quiet
        else (
            "DEBUG"
            if args.debug
            else "INFO" if hasattr(args, "verbose") and args.verbose else "WARNING"
        )
    )
    setup_logging(level=log_level, log_file=args.log_file, debug=args.debug)

    if not args.command:
        parser.print_help()
        return 0

    try:
        handlers = {
            "init-config": handle_init_config,
            "anonymize": handle_anonymize,
            "unanonymize": handle_unanonymize,
            "validate": handle_validate,
            "batch": handle_batch,
            "stats": handle_stats,
        }

        handler = handlers.get(args.command)
        if handler:
            return handler(args)

        return 1

    except CloudMaskError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        if e.suggestion:
            print(f"💡 {e.suggestion}", file=sys.stderr)
        log_error(e, "CLI operation failed")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        log_error(e, "Unexpected error")
        if args.debug:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
