import os
import uuid

from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
import io

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def process_image(upload):
    original_name = secure_filename(upload.filename or "")
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Use a JPG, PNG, or WEBP image.")
    image = Image.open(upload.stream)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, "JPEG", quality=88, optimize=True)
    return f"{uuid.uuid4().hex}.jpg", output.getvalue()

def save_image(upload, destination):
    filename, image_bytes = process_image(upload)
    save_image_bytes(filename, image_bytes, destination)
    return filename


def save_image_bytes(filename, image_bytes, destination):
    os.makedirs(destination, exist_ok=True)
    with open(os.path.join(destination, filename), "wb") as image_file:
        image_file.write(image_bytes)
