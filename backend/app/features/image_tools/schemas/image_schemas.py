from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ImageHashes(BaseModel):
    """Hash values for the image file."""

    md5: str = Field(
        ...,
        description="MD5 hash of image content",
        pattern=r'^[a-fA-F0-9]{32}$'
    )
    sha1: str = Field(
        ...,
        description="SHA1 hash of image content",
        pattern=r'^[a-fA-F0-9]{40}$'
    )
    sha256: str = Field(
        ...,
        description="SHA256 hash of image content",
        pattern=r'^[a-fA-F0-9]{64}$'
    )


class ImageFileInfo(BaseModel):
    """Basic file properties of the image."""

    filename: str = Field(..., description="Original uploaded filename")
    format: str | None = Field(default=None, description="Image format (e.g. JPEG, PNG)")
    mime_type: str | None = Field(default=None, description="Detected MIME type")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")
    mode: str | None = Field(default=None, description="Pillow color mode (e.g. RGB, RGBA, L)")
    dpi_x: float | None = Field(default=None, description="Horizontal resolution in DPI")
    dpi_y: float | None = Field(default=None, description="Vertical resolution in DPI")
    file_size: int = Field(..., description="Size of the uploaded file in bytes", ge=0)


class GpsInfo(BaseModel):
    """GPS coordinates extracted from EXIF data."""

    latitude: float = Field(..., description="Decimal latitude")
    longitude: float = Field(..., description="Decimal longitude")
    altitude: float | None = Field(default=None, description="Altitude in meters, if present")
    map_url: str = Field(..., description="Link to view the coordinates on a map")


class ImageAnalysisResponse(BaseModel):
    """Complete image metadata analysis response."""

    file_info: ImageFileInfo = Field(..., description="Basic file properties")
    hashes: ImageHashes = Field(..., description="Hash values of the image file")
    exif: dict[str, str] = Field(
        default_factory=dict,
        description="All EXIF/IPTC/XMP tags found, keyed by their full tag name (e.g. 'EXIF DateTimeOriginal', 'GPS GPSLatitude')"
    )
    gps: GpsInfo | None = Field(default=None, description="Parsed GPS coordinates, if present")
    has_thumbnail: bool = Field(default=False, description="Whether an embedded EXIF thumbnail was found")
    thumbnail_base64: str | None = Field(default=None, description="Base64-encoded embedded thumbnail (data URI)")
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when analysis was performed"
    )


class ImageHealthResponse(BaseModel):
    """Health check response for the image tools service."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    endpoints: list[str] = Field(..., description="Available endpoints")
    supported_formats: list[str] = Field(..., description="Supported file extensions")
    max_file_size: str = Field(..., description="Maximum file size")
