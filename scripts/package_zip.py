"""Distribution archive packager for Aura Workforce OS.

Generates a clean distribution ZIP archive excluding virtual environments,
git metadata, cache directories, bytecode (.pyc/.pyo), and secret .env files.
All paths are computed dynamically relative to the repository root.
"""

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

# Paths computed dynamically relative to this script
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "employee_management_api.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
    ".system_generated",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
}


def clean_pycache(root_dir: Path) -> int:
    """Removes all __pycache__ folders and compiled python bytecode files."""
    removed_count = 0
    for path in list(root_dir.rglob("__pycache__")):
        if ".venv" not in path.parts:
            shutil.rmtree(path, ignore_errors=True)
            removed_count += 1
    for ext in ("*.pyc", "*.pyo"):
        for f in list(root_dir.rglob(ext)):
            if ".venv" not in f.parts:
                try:
                    f.unlink()
                    removed_count += 1
                except OSError:
                    pass
    return removed_count


def package_repository(output_zip: Path) -> Path:
    """Packages the repository into a clean ZIP archive with prefix employee_management_api/."""
    clean_pycache(REPO_ROOT)

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        output_zip.unlink()

    included_count = 0
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(REPO_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file_name in files:
                # Exclude bytecode
                if any(file_name.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                # Exclude secrets (.env, .env.local, etc.) but allow .env.example
                if file_name == ".env" or (file_name.startswith(".env.") and file_name != ".env.example"):
                    continue

                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(REPO_ROOT)
                archive_target = Path("employee_management_api") / rel_path

                archive.write(full_path, str(archive_target).replace("\\", "/"))
                included_count += 1

    # Verify archive contents
    with zipfile.ZipFile(output_zip, "r") as archive:
        all_names = archive.namelist()
        pyc_files = [n for n in all_names if n.endswith((".pyc", ".pyo")) or "__pycache__" in n]
        env_files = [n for n in all_names if n.endswith("/.env") or "/.env." in n and not n.endswith("/.env.example")]

    if pyc_files:
        raise RuntimeError(f"Archive contains unexpected bytecode files: {pyc_files}")
    if env_files:
        raise RuntimeError(f"Archive contains unexpected secret files: {env_files}")

    print(f"Clean ZIP successfully created: {output_zip} ({included_count} files, 0 .pyc, 0 secrets)")
    return output_zip


def main():
    parser = argparse.ArgumentParser(description="Build clean distribution archive.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for destination ZIP file (defaults to dist/employee_management_api.zip)",
    )
    args = parser.parse_args()
    package_repository(args.output.resolve())


if __name__ == "__main__":
    main()
