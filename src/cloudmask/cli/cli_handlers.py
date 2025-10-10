"""CLI command handlers."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from ..config.config_loader import load_config, validate_config
from ..config.config_templates import list_templates, save_template
from ..core import CloudMask, CloudUnmask
from ..exceptions import ClipboardError
from ..io.storage import get_default_config_path, get_default_mapping_path, get_storage_dir
from ..io.streaming import stream_anonymize_file, stream_unanonymize_file
from ..utils.security import load_encrypted_mapping, save_encrypted_mapping


def check_clipboard_available() -> bool:
    """Check if clipboard is available."""
    if not CLIPBOARD_AVAILABLE:
        print(
            "Error: pyperclip not available. Install with: pip install pyperclip", file=sys.stderr
        )
        return False
    return True


def get_clipboard_text() -> str:
    """Get text from clipboard."""
    try:
        text: str = pyperclip.paste()
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
    return text


def set_clipboard_text(text: str) -> None:
    """Set clipboard text."""
    try:
        pyperclip.copy(text)
    except Exception as e:
        raise ClipboardError(
            f"Cannot write to clipboard: {e}",
            "Ensure clipboard access is available on your system",
        ) from e


def get_password(prompt: str, args_password: str | None) -> str:
    """Get password from args or prompt."""
    import getpass

    return args_password or getpass.getpass(prompt)


def save_mapping_with_encryption(
    mask: CloudMask, mapping_path: Path, encrypt: bool, password: str | None, quiet: bool
) -> None:
    """Save mapping with optional encryption."""
    if encrypt:
        pwd = get_password("Enter password for mapping: ", password)
        save_encrypted_mapping(mask.mapping, mapping_path, pwd)
        if not quiet:
            print(f"✓ Encrypted mapping saved to: {mapping_path}")
    else:
        mask.save_mapping(mapping_path)
        if not quiet:
            print(f"✓ Mapping saved to: {mapping_path}")


def load_mapping_with_decryption(
    mapping_path: Path, encrypted: bool, password: str | None
) -> dict[str, str] | None:
    """Load mapping with optional decryption."""
    if encrypted:
        pwd = get_password("Enter password for mapping: ", password)
        return load_encrypted_mapping(mapping_path, pwd)
    return None


def handle_init_config(args: Any) -> int:
    """Handle init-config command."""
    if args.list_templates:
        print("Available templates:")
        for template in list_templates():
            print(f"  - {template}")
        return 0

    save_template(args.template, args.config)
    print(f"✓ Config file created from '{args.template}' template: {args.config}")
    print("\nEdit this file to customize your configuration.")
    print(f"\nMappings will be stored in: {get_storage_dir()}")
    return 0


def handle_anonymize(args: Any) -> int:
    """Handle anonymize command."""
    if args.clipboard:
        if not check_clipboard_available():
            return 1
        if args.input or args.output:
            print(
                "Error: --clipboard cannot be used with -i/--input or -o/--output", file=sys.stderr
            )
            return 1
    elif not args.input or not args.output:
        print(
            "Error: -i/--input and -o/--output are required when not using --clipboard",
            file=sys.stderr,
        )
        return 1

    # Load config
    config_path = args.config or get_default_config_path()
    config = (
        load_config(config_path, format=args.format, use_env=not args.no_env)
        if config_path
        else load_config(use_env=not args.no_env)
    )

    if args.seed:
        config.seed = args.seed

    mask = CloudMask(config)
    mapping_path = args.mapping or get_default_mapping_path()

    if args.clipboard:
        text = get_clipboard_text()
        anonymized = mask.anonymize(text)
        set_clipboard_text(anonymized)
        save_mapping_with_encryption(mask, mapping_path, args.encrypt, args.password, args.quiet)
        if not args.quiet:
            print(f"✓ Anonymized clipboard content ({len(mask.mapping)} unique identifiers)")
    else:
        if args.stream:
            count = stream_anonymize_file(
                mask, args.input, args.output, show_progress=args.progress
            )
        else:
            count = mask.anonymize_file(args.input, args.output)

        save_mapping_with_encryption(mask, mapping_path, args.encrypt, args.password, args.quiet)
        if not args.quiet:
            print(f"✓ Anonymized content written to: {args.output}")
            print(f"✓ Anonymized {count} unique identifiers")

    return 0


def handle_unanonymize(args: Any) -> int:
    """Handle unanonymize command."""
    if args.clipboard:
        if not check_clipboard_available():
            return 1
        if args.input or args.output:
            print(
                "Error: --clipboard cannot be used with -i/--input or -o/--output", file=sys.stderr
            )
            return 1
    elif not args.input or not args.output:
        print(
            "Error: -i/--input and -o/--output are required when not using --clipboard",
            file=sys.stderr,
        )
        return 1

    mapping_path = args.mapping or get_default_mapping_path()
    mapping = load_mapping_with_decryption(mapping_path, args.encrypted, args.password)
    unmask = CloudUnmask(mapping=mapping) if mapping else CloudUnmask(mapping_file=mapping_path)

    if args.clipboard:
        text = get_clipboard_text()
        unanonymized = unmask.unanonymize(text)
        set_clipboard_text(unanonymized)
        if not args.quiet:
            print(
                f"✓ Unanonymized clipboard content ({len(unmask.reverse_mapping)} identifiers restored)"
            )
    else:
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


def handle_validate(args: Any) -> int:
    """Handle validate command."""
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

            print(f"✓ Configuration is valid: {args.config}")
            print(f"  Seed length: {len(config.seed)} characters")
            print(f"  Company names: {len(config.company_names)}")
            print(f"  Custom patterns: {len(config.custom_patterns)}")

        if args.mapping:
            mapping = load_mapping_with_decryption(args.mapping, args.encrypted, args.password)
            if not mapping:
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


def handle_batch(args: Any) -> int:
    """Handle batch command."""
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config_path = args.config or get_default_config_path()
    config = load_config(config_path) if config_path else load_config(use_env=True)

    if args.seed:
        config.seed = args.seed

    mask = CloudMask(config)
    total_files = len(args.files)
    processed = failed = total_identifiers = 0

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

    if args.mapping:
        save_mapping_with_encryption(mask, args.mapping, args.encrypt, args.password, args.quiet)

    if not args.quiet:
        print(f"\n{'='*50}")
        print("Batch processing complete:")
        print(f"  Total files: {total_files}")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")
        print(f"  Total identifiers: {total_identifiers}")
        print(f"  Unique identifiers: {len(mask.mapping)}")

    return 0 if failed == 0 else 1


def handle_stats(args: Any) -> int:
    """Handle stats command."""
    mapping = load_mapping_with_decryption(args.mapping, args.encrypted, args.password)
    if not mapping:
        with Path(args.mapping).open() as f:
            mapping = json.load(f)

    total = len(mapping)
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
