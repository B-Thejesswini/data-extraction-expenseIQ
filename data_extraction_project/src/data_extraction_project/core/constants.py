IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


# Gemini accepts only these image formats
GEMINI_IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

CATEGORIES = [
    "Travel",
    "Meals",
    "Accommodation",
    "Fuel",
    "Software",
    "Office Supplies",
    "Other",
]

# Groq vision models accept these image formats
GROQ_IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

PDF_EXTS = frozenset({".pdf"})
PDF_MAGIC = b"%PDF-"
MIN_MARKDOWN_CHARS = 20  # below this, the PDF is almost certainly scanned/image-only

MARKDOWN_EXTS = frozenset({".md", ".markdown"})
