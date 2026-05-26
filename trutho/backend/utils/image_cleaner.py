import io
import os
from PIL import Image
import piexif

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

MAX_IMAGE_DIMENSION = 2048  # px — resize if larger


def strip_exif_and_clean(file_bytes: bytes, content_type: str) -> bytes:
    """
    Strip ALL EXIF metadata (GPS, camera model, timestamps, etc.)
    Re-encode image as clean JPEG/PNG with no metadata.
    """
    if content_type not in ALLOWED_IMAGE_TYPES:
        # For video we just return as-is (ffprobe strip in production)
        return file_bytes

    try:
        img = Image.open(io.BytesIO(file_bytes))

        # Remove EXIF via piexif if JPEG
        if img.format in ("JPEG", "JPG"):
            try:
                piexif.remove(file_bytes)
            except Exception:
                pass

        # Convert to RGB to drop alpha / ICC profiles
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if too large
        if max(img.size) > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

        # Re-encode with NO metadata whatsoever
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=88, optimize=True, exif=b"")
        return output.getvalue()

    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")


def is_valid_upload(content_type: str, size_bytes: int, max_mb: int = 50) -> tuple[bool, str]:
    if content_type not in ALLOWED_TYPES:
        return False, f"File type not allowed: {content_type}"
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        return False, f"File too large. Max size: {max_mb}MB"
    return True, ""
