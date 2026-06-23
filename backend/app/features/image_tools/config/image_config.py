"""Image tools configuration settings."""


# File validation settings
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB
ALLOWED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.bmp', '.gif']
ALLOWED_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/tiff', 'image/webp',
    'image/heic', 'image/bmp', 'image/gif'
]

# Hash algorithms supported
SUPPORTED_HASH_ALGORITHMS = ['md5', 'sha1', 'sha256']
