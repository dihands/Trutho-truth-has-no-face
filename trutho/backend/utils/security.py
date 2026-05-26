import uuid
import os


def secure_filename(original_filename: str) -> str:
    """Generate a UUID-based filename, keeping only the extension."""
    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mov"}
        if ext not in allowed_exts:
            ext = ".bin"
    return f"{uuid.uuid4().hex}{ext}"


def get_upload_path(upload_dir: str, filename: str) -> str:
    return os.path.join(upload_dir, filename)
