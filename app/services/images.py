"""Image uploads: verify, auto-rotate, resize, convert to WebP, strip metadata (EXIF/GPS)."""
import uuid
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

from ..i18n import t

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_PIXELS = 40_000_000  # ~ 8000 x 5000; blocks "decompression bomb" images
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

# kind -> (folder, max size of the large version)
KINDS = {
    "event": ("events", (1600, 1600)),
    "offer": ("offers", (1600, 1600)),
    "cover": ("orgs", (1920, 1080)),
    "logo": ("orgs", (512, 512)),
}
THUMB_SIZE = (640, 640)  # small variant for cards on phones
QUALITY = 80


class ImageError(ValueError):
    """Upload rejected; the message is shown to the user."""


def _upload_root() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"]).resolve()


def save_image(file_storage, kind: str) -> str:
    """Process an uploaded file and return its path relative to UPLOAD_FOLDER."""
    folder_name, max_size = KINDS[kind]
    filename = (file_storage.filename or "").lower()
    if "." not in filename or filename.rsplit(".", 1)[1] not in ALLOWED_EXTENSIONS:
        raise ImageError(t("validation.image_type"))

    # 1) Check the real content, not the file name or browser-sent MIME type.
    try:
        with Image.open(file_storage.stream) as probe:
            image_format = probe.format
            width, height = probe.size
            probe.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ImageError(t("validation.image_invalid")) from None
    if image_format not in ALLOWED_FORMATS:
        raise ImageError(t("validation.image_type"))
    if width * height > MAX_PIXELS:
        raise ImageError(t("validation.image_pixels"))

    # 2) Re-open (verify() leaves the image unusable) and normalize.
    file_storage.stream.seek(0)
    with Image.open(file_storage.stream) as original:
        img = ImageOps.exif_transpose(original)  # apply phone rotation before EXIF is dropped
        has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
        img = img.convert("RGBA" if has_alpha else "RGB")
        img.info.clear()  # drop EXIF, GPS, comments, ICC
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        name = uuid.uuid4().hex  # random name: no user input in paths, nothing guessable
        folder = _upload_root() / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        img.save(folder / f"{name}.webp", "WEBP", quality=QUALITY, method=6, exif=b"")
        thumb = img.copy()
        thumb.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        thumb.save(folder / f"{name}_sm.webp", "WEBP", quality=QUALITY, method=6, exif=b"")

    return f"{folder_name}/{name}.webp"


def small_variant(path: str) -> str:
    return path[:-5] + "_sm.webp" if path.endswith(".webp") else path


def delete_image(path: str | None) -> None:
    """Remove an image and its small variant. Ignores paths outside UPLOAD_FOLDER."""
    if not path:
        return
    root = _upload_root()
    for rel in {path, small_variant(path)}:
        target = (root / rel).resolve()
        if target.is_relative_to(root) and target.is_file():
            target.unlink()
