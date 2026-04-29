#!/usr/bin/env python3
"""
Build a KiCad PCM (Plugin and Content Manager) custom-repository release.

Reads the source-of-truth ``metadata.json`` at the repo root, builds a
versioned plugin zip under ``releases/``, and regenerates ``packages.json``
and ``repository.json`` so the repository can be served straight off
``raw.githubusercontent.com``.

Run from the repo root:

    python3 tools/build_pcm_release.py

By default it publishes for the URL base
``https://raw.githubusercontent.com/Wadam100/via-stitching/main/`` -- pass
``--base-url`` to override.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/Wadam100/via-stitching/main/"
PLUGIN_PKG_DIR = "via_stitching"  # directory inside the repo with the .py files
RELEASES_DIR = "releases"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    now = _dt.datetime.now(_dt.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S"), int(now.timestamp())


def join_url(base: str, path: str) -> str:
    if not base.endswith("/"):
        base += "/"
    return base + path.lstrip("/")


# ---------------------------------------------------------------------------
# Build the plugin zip
# ---------------------------------------------------------------------------

def build_plugin_zip(repo_root: Path, metadata: dict, version: str) -> Path:
    """
    Produce releases/via_stitching-<version>.zip with the layout PCM expects:

        metadata.json
        plugins/
            __init__.py
            plugin.py
            via_stitcher.py
            stitcher_dialog.py

    PCM extracts plugins/ into <KICAD_USER>/scripting/plugins/<identifier>/
    so the plugin's ``__init__.py`` lands at the correct place.
    """
    src_pkg = repo_root / PLUGIN_PKG_DIR
    if not src_pkg.is_dir():
        raise SystemExit(f"Source plugin folder not found: {src_pkg}")

    out_dir = repo_root / RELEASES_DIR
    out_dir.mkdir(exist_ok=True)
    out_zip = out_dir / f"via_stitching-{version}.zip"

    # The metadata.json inside the package zip should NOT include
    # download_url / download_sha256 (the spec puts those in the repo's
    # packages.json, not the package's own metadata.json).
    pkg_metadata = json.loads(json.dumps(metadata))

    # We're shipping a single version per zip, so trim the versions array
    # to just this one to keep the in-zip metadata tidy.
    versions_for_zip = []
    for v in pkg_metadata.get("versions", []):
        if v.get("version") == version:
            v_copy = {k: v[k] for k in v if k not in ("download_url", "download_sha256", "download_size", "install_size")}
            versions_for_zip.append(v_copy)
    pkg_metadata["versions"] = versions_for_zip

    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(pkg_metadata, indent=2) + "\n")
        # plugins/ holds the Python package KiCad will install
        for path in sorted(src_pkg.rglob("*")):
            # skip caches and presets
            if "__pycache__" in path.parts:
                continue
            if path.name == "last_settings.json":
                continue
            if path.is_dir():
                continue
            arc = Path("plugins") / PLUGIN_PKG_DIR / path.relative_to(src_pkg)
            zf.write(path, arcname=str(arc).replace(os.sep, "/"))

    return out_zip


def install_size_of_zip(zip_path: Path) -> int:
    """Sum of *uncompressed* sizes -- this is what PCM means by install_size."""
    total = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            total += info.file_size
    return total


# ---------------------------------------------------------------------------
# packages.json + repository.json
# ---------------------------------------------------------------------------

def build_packages_json(metadata: dict, version: str, zip_path: Path, base_url: str) -> dict:
    download_url = join_url(base_url, f"{RELEASES_DIR}/{zip_path.name}")
    download_sha = sha256_file(zip_path)
    download_size = zip_path.stat().st_size
    install_size = install_size_of_zip(zip_path)

    pkg = json.loads(json.dumps(metadata))  # deep copy
    new_versions = []
    for v in pkg.get("versions", []):
        v = dict(v)
        if v.get("version") == version:
            v["download_url"] = download_url
            v["download_sha256"] = download_sha
            v["download_size"] = download_size
            v["install_size"] = install_size
        new_versions.append(v)
    pkg["versions"] = new_versions

    return {
        "$schema": "https://go.kicad.org/pcm/schemas/v1",
        "packages": [pkg],
    }


def build_repository_json(packages_json_path: Path, base_url: str, maintainer: dict) -> dict:
    pkg_bytes = packages_json_path.read_bytes()
    when_str, when_ts = utc_now()
    return {
        "$schema": "https://go.kicad.org/pcm/schemas/v1",
        "maintainer": maintainer,
        "name": "Via Stitching repository",
        "packages": {
            "url": join_url(base_url, "packages.json"),
            "sha256": sha256_bytes(pkg_bytes),
            "update_time_utc": when_str,
            "update_timestamp": when_ts,
        },
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL,
                    help=f"Base URL where the repo is served (default: {DEFAULT_BASE_URL})")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent),
                    help="Path to the repo root (default: parent of tools/)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    metadata_path = repo_root / "metadata.json"
    if not metadata_path.is_file():
        print(f"metadata.json not found at {metadata_path}", file=sys.stderr)
        return 1
    metadata = json.loads(metadata_path.read_text())

    versions = metadata.get("versions") or []
    if not versions:
        print("metadata.json has no versions[]", file=sys.stderr)
        return 1
    # Build for every declared version
    last_zip = None
    for v in versions:
        version = v["version"]
        last_zip = build_plugin_zip(repo_root, metadata, version)
        print(f"  built {last_zip.relative_to(repo_root)} "
              f"({last_zip.stat().st_size:,} bytes)")

    # packages.json (only writes the latest version's download_* hashes —
    # if you need to retain older versions in the repo, re-run for each.)
    # Always write LF newlines: Git serves the LF-normalized blob from
    # raw.githubusercontent.com, so the sha256 we record in repository.json
    # has to be computed against LF bytes — not the CRLF that Path.write_text
    # would produce on Windows.
    pkg_json = build_packages_json(metadata, versions[-1]["version"],
                                   last_zip, args.base_url)
    packages_path = repo_root / "packages.json"
    packages_path.write_bytes((json.dumps(pkg_json, indent=2) + "\n").encode("utf-8"))
    print(f"  wrote {packages_path.relative_to(repo_root)}")

    # repository.json
    maintainer = {
        "name": metadata.get("author", {}).get("name", ""),
        "contact": metadata.get("author", {}).get("contact", {}),
    }
    repo_json = build_repository_json(packages_path, args.base_url, maintainer)
    repo_path = repo_root / "repository.json"
    repo_path.write_bytes((json.dumps(repo_json, indent=2) + "\n").encode("utf-8"))
    print(f"  wrote {repo_path.relative_to(repo_root)}")

    install_url = join_url(args.base_url, "repository.json")
    print()
    print("Done. PCM custom-repository URL to give KiCad users:")
    print(f"  {install_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
