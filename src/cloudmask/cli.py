#!/usr/bin/env python3
"""Command-line interface for CloudMask."""

import argparse
import sys
from pathlib import Path

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from .config_loader import load_config, validate_config
from .config_templates import list_templates, save_template
from .core import CloudMask, CloudUnmask
from .exceptions import ClipboardError, CloudMaskError
from .logging import log_error, setup_logging
from .security import load_encrypted_mapping, save_encrypted_mapping
from .streaming import stream_anonymize_file, stream_unanonymize_file


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cloudmask",
        description="Anonymize AWS infrastructure identifiers for LLM processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate default config file
  cloudmask init-config -c config.yaml

  # Anonymize a file with config
  cloudmask anonymize -i input.txt -o anonymized.txt -m mapping.json -c config.yaml

  # Anonymize clipboard content
  cloudmask anonymize --clipboard -m mapping.json -s "custom-seed"

  # Unanonymize a file
  cloudmask unanonymize -i anonymized.txt -o output.txt -m mapping.json

  # Unanonymize clipboard content
  cloudmask unanonymize --clipboard -m mapping.json
        """,
    )

    # Global options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init config command
    init_parser = subparsers.add_parser("init-config", help="Generate default config file")
    init_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default="cloudmask.yaml",
        help="Config file path (default: cloudmask.yaml)",
    )
    init_parser.add_argument(
        "-t",
        "--template",
        choices=list_templates(),
        default="standard",
        help="Configuration template to use",
    )
    init_parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates",
    )

    # Anonymize command
    anon_parser = subparsers.add_parser("anonymize", help="Anonymize AWS identifiers")
    anon_parser.add_argument("-i", "--input", type=Path, help="Input file to anonymize")
    anon_parser.add_argument("-o", "--output", type=Path, help="Output file for anonymized content")
    anon_parser.add_argument("-m", "--mapping", type=Path, help="Output file for mapping (JSON)")
    anon_parser.add_argument("-c", "--config", type=Path, help="Config file (YAML/JSON/TOML)")
    anon_parser.add_argument(
        "--format",
        choices=["yaml", "json", "toml"],
        help="Config file format (auto-detected if not specified)",
    )
    anon_parser.add_argument(
        "--no-env",
        action="store_true",
        help="Don't load configuration from environment variables",
    )
    anon_parser.add_argument(
        "-s", "--seed", help="Seed for deterministic anonymization (overrides config)"
    )
    anon_parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Read from clipboard and write anonymized result back to clipboard",
    )
    anon_parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt mapping file with password",
    )
    anon_parser.add_argument(
        "--password",
        help="Password for encrypted mapping (prompted if not provided)",
    )
    anon_parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode for large files (memory efficient)",
    )
    anon_parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bar during processing",
    )

    # Unanonymize command
    unanon_parser = subparsers.add_parser("unanonymize", help="Restore original identifiers")
    unanon_parser.add_argument("-i", "--input", type=Path, help="Input file to unanonymize")
    unanon_parser.add_argument(
        "-o", "--output", type=Path, help="Output file for unanonymized content"
    )
    unanon_parser.add_argument(
        "-m", "--mapping", required=True, type=Path, help="Mapping file (JSON)"
    )
    unanon_parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Read from clipboard and write unanonymized result back to clipboard",
    )
    unanon_parser.add_argument(
        "--encrypted",
        action="store_true",
        help="Mapping file is encrypted",
    )
    unanon_parser.add_argument(
        "--password",
        help="Password for encrypted mapping (prompted if not provided)",
    )
    unanon_parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode for large files (memory efficient)",
    )
    unanon_parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bar during processing",
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate configuration or mapping file"
    )
    validate_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Config file to validate",
    )
    validate_parser.add_argument(
        "-m",
        "--mapping",
        type=Path,
        help="Mapping file to validate",
    )
    validate_parser.add_argument(
        "--format",
        choices=["yaml", "json", "toml"],
        help="Config file format",
    )
    validate_parser.add_argument(
        "--encrypted",
        action="store_true",
        help="Mapping file is encrypted",
    )
    validate_parser.add_argument(
        "--password",
        help="Password for encrypted mapping",
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch process multiple files")
    batch_parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Files to process",
    )
    batch_parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        type=Path,
        help="Output directory for processed files",
    )
    batch_parser.add_argument(
        "-m",
        "--mapping",
        type=Path,
        help="Mapping file (shared across all files)",
    )
    batch_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Config file",
    )
    batch_parser.add_argument(
        "-s",
        "--seed",
        help="Seed for deterministic anonymization",
    )
    batch_parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt mapping file",
    )
    batch_parser.add_argument(
        "--password",
        help="Password for encrypted mapping",
    )
    batch_parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bar",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics about anonymization")
    stats_parser.add_argument(
        "-m",
        "--mapping",
        required=True,
        type=Path,
        help="Mapping file to analyze",
    )
    stats_parser.add_argument(
        "--encrypted",
        action="store_true",
        help="Mapping file is encrypted",
    )
    stats_parser.add_argument(
        "--password",
        help="Password for encrypted mapping",
    )
    stats_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed statistics",
    )

    args = parser.parse_args()

    # Setup logging
    if args.quiet:
        log_level = "ERROR"
    elif args.debug:
        log_level = "DEBUG"
    elif hasattr(args, "verbose") and args.verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"
    setup_logging(level=log_level, log_file=args.log_file, debug=args.debug)

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "init-config":
            if args.list_templates:
                print("Available templates:")
                for template in list_templates():
                    print(f"  - {template}")
                return 0

            save_template(args.template, args.config)
            print(f"✓ Config file created from '{args.template}' template: {args.config}")
            print("\nEdit this file to customize your configuration.")
            return 0

        if args.command == "anonymize":
            if args.clipboard and not CLIPBOARD_AVAILABLE:
                print(
                    "Error: pyperclip not available. Install with: pip install pyperclip",
                    file=sys.stderr,
                )
                return 1

            if args.clipboard and (args.input or args.output):
                print(
                    "Error: --clipboard cannot be used with -i/--input or -o/--output",
                    file=sys.stderr,
                )
                return 1

            if not args.clipboard and (not args.input or not args.output):
                print(
                    "Error: -i/--input and -o/--output are required when not using --clipboard",
                    file=sys.stderr,
                )
                return 1

            # Load config
            config = (
                load_config(args.config, format=args.format, use_env=not args.no_env)
                if args.config
                else load_config(use_env=not args.no_env)
            )

            # Override seed if provided
            if args.seed:
                config.seed = args.seed

            # Create anonymizer
            mask = CloudMask(config)

            if args.clipboard:
                # Read from clipboard
                try:
                    text = pyperclip.paste()
                except Exception as e:
                    raise ClipboardError(
                        f"Cannot access clipboard: {e}",
                        "Ensure clipboard access is available on your system",
                    ) from e

                if not text.strip():
                    raise ClipboardError(
                        "Clipboard is empty",
                        "Copy some text to clipboard before running this command",
                    )

                # Anonymize
                anonymized = mask.anonymize(text)

                # Write back to clipboard
                try:
                    pyperclip.copy(anonymized)
                except Exception as e:
                    raise ClipboardError(
                        f"Cannot write to clipboard: {e}",
                        "Ensure clipboard access is available on your system",
                    ) from e

                # Save mapping if specified
                if args.mapping:
                    if args.encrypt:
                        import getpass

                        password = args.password or getpass.getpass("Enter password for mapping: ")
                        save_encrypted_mapping(mask.mapping, args.mapping, password)
                        if not args.quiet:
                            print(f"✓ Encrypted mapping saved to: {args.mapping}")
                    else:
                        mask.save_mapping(args.mapping)
                        if not args.quiet:
                            print(f"✓ Mapping saved to: {args.mapping}")

                if not args.quiet:
                    print(
                        f"✓ Anonymized clipboard content ({len(mask.mapping)} unique identifiers)"
                    )
                return 0
            else:
                # File-based processing
                if args.stream:
                    count = stream_anonymize_file(
                        mask, args.input, args.output, show_progress=args.progress
                    )
                else:
                    count = mask.anonymize_file(args.input, args.output)

                # Save mapping
                if args.mapping:
                    if args.encrypt:
                        import getpass

                        password = args.password or getpass.getpass("Enter password for mapping: ")
                        save_encrypted_mapping(mask.mapping, args.mapping, password)
                        if not args.quiet:
                            print(f"✓ Encrypted mapping saved to: {args.mapping}")
                    else:
                        mask.save_mapping(args.mapping)
                        if not args.quiet:
                            print(f"✓ Mapping saved to: {args.mapping}")

                if not args.quiet:
                    print(f"✓ Anonymized content written to: {args.output}")
                    print(f"✓ Anonymized {count} unique identifiers")
                return 0

        elif args.command == "unanonymize":
            if args.clipboard and not CLIPBOARD_AVAILABLE:
                print(
                    "Error: pyperclip not available. Install with: pip install pyperclip",
                    file=sys.stderr,
                )
                return 1

            if args.clipboard and (args.input or args.output):
                print(
                    "Error: --clipboard cannot be used with -i/--input or -o/--output",
                    file=sys.stderr,
                )
                return 1

            if not args.clipboard and (not args.input or not args.output):
                print(
                    "Error: -i/--input and -o/--output are required when not using --clipboard",
                    file=sys.stderr,
                )
                return 1

            if args.clipboard:
                # Clipboard-based processing
                try:
                    text = pyperclip.paste()
                except Exception as e:
                    raise ClipboardError(
                        f"Cannot access clipboard: {e}",
                        "Ensure clipboard access is available on your system",
                    ) from e

                if not text.strip():
                    raise ClipboardError(
                        "Clipboard is empty",
                        "Copy some text to clipboard before running this command",
                    )

                # Load mapping
                if args.encrypted:
                    import getpass

                    password = args.password or getpass.getpass("Enter password for mapping: ")
                    mapping = load_encrypted_mapping(args.mapping, password)
                    unmask = CloudUnmask(mapping=mapping)
                else:
                    unmask = CloudUnmask(mapping_file=args.mapping)

                # Unanonymize
                unanonymized = unmask.unanonymize(text)

                # Write back to clipboard
                try:
                    pyperclip.copy(unanonymized)
                except Exception as e:
                    raise ClipboardError(
                        f"Cannot write to clipboard: {e}",
                        "Ensure clipboard access is available on your system",
                    ) from e

                if not args.quiet:
                    print(
                        f"✓ Unanonymized clipboard content ({len(unmask.reverse_mapping)} identifiers restored)"
                    )
                return 0
            else:
                # File-based processing
                if args.encrypted:
                    import getpass

                    password = args.password or getpass.getpass("Enter password for mapping: ")
                    mapping = load_encrypted_mapping(args.mapping, password)
                    unmask = CloudUnmask(mapping=mapping)
                else:
                    unmask = CloudUnmask(mapping_file=args.mapping)

                if args.stream:
                    count = stream_unanonymize_file(
                        unmask, args.input, args.output, show_progress=args.progress
                    )
                else:
                    count = unmask.unanonymize_file(args.input, args.output)

                if not args.quiet:
                    print(f"✓ Unanonymized content written to: {args.output}")
                    print(f"✓ Restored {count} unique identifiers")
                return 0

        elif args.command == "validate":
            if not args.config and not args.mapping:
                print("Error: Either --config or --mapping must be specified", file=sys.stderr)
                return 1

            try:
                if args.config:
                    config = load_config(args.config, format=args.format, use_env=False)
                    issues = validate_config(config)

                    if issues:
                        print(f"✗ Configuration has {len(issues)} issue(s):")
                        for issue in issues:
                            print(f"  - {issue}")
                        return 1
                    else:
                        print(f"✓ Configuration is valid: {args.config}")
                        print(f"  Seed length: {len(config.seed)} characters")
                        print(f"  Company names: {len(config.company_names)}")
                        print(f"  Custom patterns: {len(config.custom_patterns)}")

                if args.mapping:
                    import json

                    if args.encrypted:
                        import getpass

                        password = args.password or getpass.getpass("Enter password: ")
                        mapping = load_encrypted_mapping(args.mapping, password)
                    else:
                        with Path(args.mapping).open() as f:
                            mapping = json.load(f)

                    if not isinstance(mapping, dict):
                        print("✗ Invalid mapping format: must be a JSON object", file=sys.stderr)
                        return 1

                    print(f"✓ Mapping is valid: {args.mapping}")
                    print(f"  Total mappings: {len(mapping)}")

                return 0
            except Exception as e:
                print(f"✗ Validation failed: {e}", file=sys.stderr)
                return 1

        elif args.command == "batch":
            # Create output directory
            args.output_dir.mkdir(parents=True, exist_ok=True)

            # Load config
            config = load_config(args.config) if args.config else load_config(use_env=True)

            if args.seed:
                config.seed = args.seed

            # Create anonymizer
            mask = CloudMask(config)

            # Process files
            total_files = len(args.files)
            processed = 0
            failed = 0
            total_identifiers = 0

            if args.progress:
                try:
                    from tqdm import tqdm

                    file_iter = tqdm(args.files, desc="Processing files")
                except ImportError:
                    file_iter = args.files
                    print(f"Processing {total_files} files...")
            else:
                file_iter = args.files

            for input_file in file_iter:
                try:
                    output_file = args.output_dir / input_file.name
                    count = mask.anonymize_file(input_file, output_file)
                    total_identifiers += count
                    processed += 1
                    if not args.progress and not args.quiet:
                        print(f"✓ {input_file.name} -> {output_file}")
                except Exception as e:
                    failed += 1
                    if not args.quiet:
                        print(f"✗ Failed to process {input_file}: {e}", file=sys.stderr)

            # Save mapping
            if args.mapping:
                if args.encrypt:
                    import getpass

                    password = args.password or getpass.getpass("Enter password for mapping: ")
                    save_encrypted_mapping(mask.mapping, args.mapping, password)
                else:
                    mask.save_mapping(args.mapping)
                if not args.quiet:
                    print(f"✓ Mapping saved to: {args.mapping}")

            # Summary
            if not args.quiet:
                print(f"\n{'='*50}")
                print("Batch processing complete:")
                print(f"  Total files: {total_files}")
                print(f"  Processed: {processed}")
                print(f"  Failed: {failed}")
                print(f"  Total identifiers: {total_identifiers}")
                print(f"  Unique identifiers: {len(mask.mapping)}")

            return 0 if failed == 0 else 1

        elif args.command == "stats":
            import json
            from collections import Counter

            # Load mapping
            if args.encrypted:
                import getpass

                password = args.password or getpass.getpass("Enter password: ")
                mapping = load_encrypted_mapping(args.mapping, password)
            else:
                with Path(args.mapping).open() as f:
                    mapping = json.load(f)

            # Analyze mapping
            total = len(mapping)

            # Categorize by type
            categories: Counter[str] = Counter()
            for original in mapping:
                if original.startswith(("vpc-", "subnet-", "sg-", "i-", "ami-", "vol-", "snap-")):
                    categories["AWS Resources"] += 1
                elif original.startswith("arn:"):
                    categories["ARNs"] += 1
                elif original.replace(".", "").isdigit() and len(original.split(".")) == 4:
                    categories["IP Addresses"] += 1
                elif "." in original and not original[0].isdigit():
                    categories["Domains"] += 1
                elif original.isdigit() and len(original) == 12:
                    categories["Account IDs"] += 1
                else:
                    categories["Other"] += 1

            # Display stats
            print(f"Mapping Statistics: {args.mapping}")
            print(f"{'='*50}")
            print(f"Total mappings: {total}")
            print("\nBy category:")
            for category, count in categories.most_common():
                percentage = (count / total * 100) if total > 0 else 0
                print(f"  {category:20s}: {count:5d} ({percentage:5.1f}%)")

            if args.detailed:
                print("\nSample mappings (first 10):")
                for original, anonymized in list(mapping.items())[:10]:
                    print(f"  {original} -> {anonymized}")

            return 0

        return 1

    except CloudMaskError as e:
        # Our custom exceptions with suggestions
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
