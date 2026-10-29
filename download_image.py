"""Download images from URLs.

Usage:
    python download_image.py URL [URL ...] [-o OUTPUT_DIR]
    python download_image.py -f urls.txt [-o OUTPUT_DIR]
"""
import argparse
import mimetypes
import os
import sys
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_BYTES = 50 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (compatible; image-downloader/1.0)"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def download(url: str, out_dir: Path) -> Path:
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("only http/https URLs are supported")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get_content_type()
        if not content_type.startswith("image/"):
            raise ValueError(f"not an image (Content-Type: {content_type})")

        name = os.path.basename(unquote(urlparse(url).path)) or "image"
        stem, ext = os.path.splitext(name)
        if not ext:
            ext = mimetypes.guess_extension(content_type) or ".img"
        dest = unique_path(out_dir / f"{stem}{ext}")

        size = 0
        try:
            with open(dest, "wb") as f:
                while chunk := resp.read(64 * 1024):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("file exceeds 50 MB limit")
                    f.write(chunk)
        except Exception:
            dest.unlink(missing_ok=True)
            raise
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Download images from URLs.")
    parser.add_argument("urls", nargs="*", help="image URLs")
    parser.add_argument("-f", "--file", help="text file with one URL per line")
    parser.add_argument("-o", "--output", default="downloads", help="output folder")
    args = parser.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls += [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not urls:
        parser.error("provide at least one URL or --file")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for url in urls:
        try:
            print(f"OK    {url} -> {download(url, out_dir)}")
        except Exception as e:
            failures += 1
            print(f"FAIL  {url}: {e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
