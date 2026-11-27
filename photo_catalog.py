"""Read-only local photo catalog for the NAS service."""
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

class PhotoCatalog:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("photo root must be a directory")

    def resolve(self, name):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("invalid photo path")
        path = (self.root / relative).resolve(strict=True)
        if not path.is_relative_to(self.root) or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            raise ValueError("invalid photo path")
        return path

    def list(self):
        names = []
        for path in self.root.rglob("*"):
            if path.suffix.lower() not in EXTENSIONS:
                continue
            name = path.relative_to(self.root).as_posix()
            try:
                self.resolve(name)
            except (ValueError, OSError, RuntimeError):
                continue
            names.append(name)
        return sorted(names)

    def render(self, name, size, *, palette="bwr", method="floyd"):
        from image_pipeline import convert
        if len(size) != 2 or any(not isinstance(n, int) or n <= 0 or n > 2048 for n in size):
            raise ValueError("invalid output dimensions")
        with Image.open(self.resolve(name)) as image:
            if palette == "rgb":
                preview = ImageOps.fit(ImageOps.exif_transpose(image).convert("RGB"), size, Image.Resampling.LANCZOS)
                indices = None
            else:
                preview, indices = convert(image, size, palette, method)
        output = BytesIO()
        preview.save(output, format="PNG")
        return output.getvalue(), indices
