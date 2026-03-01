import argparse
import datetime as dt
import mimetypes
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

# Ensure app imports resolve when running this script directly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import get_settings
from app.services import s3_service


# 1x1 transparent PNG
_TINY_PNG_BYTES = bytes([
    137, 80, 78, 71, 13, 10, 26, 10,
    0, 0, 0, 13, 73, 72, 68, 82,
    0, 0, 0, 1, 0, 0, 0, 1,
    8, 6, 0, 0, 0, 31, 21, 196,
    137, 0, 0, 0, 13, 73, 68, 65,
    84, 120, 156, 99, 248, 15, 4, 0,
    9, 251, 3, 253, 166, 157, 37, 29,
    0, 0, 0, 0, 73, 69, 78, 68,
    174, 66, 96, 130,
])


def _build_default_key() -> str:
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    return f"debug/image-upload/{ts}.png"


def _guess_content_type(path: str) -> str:
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"


def _verify_public_url(url: str, timeout: int = 15) -> tuple[bool, str]:
    try:
        with urlopen(url, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            ctype = resp.headers.get("Content-Type", "")
            return 200 <= status < 300, f"HTTP {status}, Content-Type={ctype}"
    except HTTPError as exc:
        return False, f"HTTPError {exc.code}: {exc.reason}"
    except URLError as exc:
        return False, f"URLError: {exc.reason}"
    except Exception as exc:
        return False, f"Error: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload one image to S3 and verify URL access.")
    parser.add_argument("--image", help="Path to a local image file. If omitted, uploads a generated 1x1 PNG.")
    parser.add_argument("--key", default="", help="S3 object key. Defaults to debug/image-upload/<timestamp>.png")
    parser.add_argument("--private", action="store_true", help="Upload without public-read ACL")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip HTTP fetch verification of public URL")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.S3_BUCKET_NAME:
        print("ERROR: S3_BUCKET_NAME is not configured")
        return 2
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("ERROR: AWS credentials are not configured")
        return 2

    s3_key = args.key or _build_default_key()
    is_public = not args.private

    try:
        if args.image:
            image_path = os.path.abspath(args.image)
            if not os.path.isfile(image_path):
                print(f"ERROR: image file not found: {image_path}")
                return 2
            content_type = _guess_content_type(image_path)
            s3_service.upload_file(image_path, s3_key, content_type=content_type, public=is_public)
            print(f"Uploaded local file: {image_path}")
        else:
            s3_service.upload_bytes(_TINY_PNG_BYTES, s3_key, content_type="image/png", public=is_public)
            print("Uploaded generated 1x1 PNG")

        url = s3_service.get_url(s3_key)
        print(f"S3 key: {s3_key}")
        print(f"URL: {url}")

        if args.skip_fetch:
            print("Skipped URL fetch verification")
            return 0

        ok, detail = _verify_public_url(url)
        if ok:
            print(f"SUCCESS: URL is accessible ({detail})")
            return 0

        print(f"FAIL: URL not accessible ({detail})")
        if args.private:
            print("Note: --private was set, so non-public access is expected.")
        return 1

    except Exception as exc:
        print(f"ERROR: upload failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
