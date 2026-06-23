"""Hash calculation utilities for image tools."""

import hashlib

from ..schemas.image_schemas import ImageHashes


def calculate_image_hashes(data: bytes) -> ImageHashes:
    """Calculate MD5/SHA1/SHA256 hashes of image file content."""
    return ImageHashes(
        md5=hashlib.md5(data).hexdigest(),
        sha1=hashlib.sha1(data).hexdigest(),
        sha256=hashlib.sha256(data).hexdigest(),
    )
