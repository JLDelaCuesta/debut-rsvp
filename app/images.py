import os
import uuid

from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def save_image(upload, destination):
    original_name = secure_filename(upload.filename or "")
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Use a JPG, PNG, or WEBP image.")
    image = Image.open(upload.stream)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(destination, filename)
    image.save(path, "JPEG", quality=88, optimize=True)
    return filename
