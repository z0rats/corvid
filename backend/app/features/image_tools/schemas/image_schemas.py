from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ImageHashes(BaseModel):
    """Hash values for the image file."""

    md5: str = Field(..., description="MD5 hash of image content", pattern=r"^[a-fA-F0-9]{32}$")
    sha1: str = Field(..., description="SHA1 hash of image content", pattern=r"^[a-fA-F0-9]{40}$")
    sha256: str = Field(
        ..., description="SHA256 hash of image content", pattern=r"^[a-fA-F0-9]{64}$"
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


class PerceptualHash(BaseModel):
    """64-bit perceptual hash (pHash) - fingerprints visual content, not exact bytes.

    Unlike MD5/SHA1/SHA256, two different files with visually similar/identical
    pixels (e.g. after re-compression or a resize) produce a similar hash here.
    """

    hex: str = Field(
        ..., description="16 hex characters encoding the 64-bit hash", pattern=r"^[a-fA-F0-9]{16}$"
    )
    bits: list[bool] = Field(
        ..., description="Same hash as 64 bits, row-major, for rendering as an 8x8 matrix"
    )


class GpsInfo(BaseModel):
    """GPS coordinates extracted from EXIF data."""

    latitude: float = Field(..., description="Decimal latitude")
    longitude: float = Field(..., description="Decimal longitude")
    altitude: float | None = Field(default=None, description="Altitude in meters, if present")
    map_url: str = Field(..., description="Link to view the coordinates on a map")
    address: str | None = Field(
        default=None, description="Reverse-geocoded human-readable address, if lookup succeeded"
    )


class ImageAnalysisResponse(BaseModel):
    """Complete image metadata analysis response."""

    file_info: ImageFileInfo = Field(..., description="Basic file properties")
    hashes: ImageHashes = Field(..., description="Hash values of the image file")
    phash: PerceptualHash | None = Field(
        default=None, description="Perceptual hash of the image content"
    )
    exif: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "All EXIF/IPTC/XMP tags found, keyed by their full tag name (e.g. 'EXIF "
            "DateTimeOriginal', 'GPS GPSLatitude')"
        ),
    )
    gps: GpsInfo | None = Field(default=None, description="Parsed GPS coordinates, if present")
    has_thumbnail: bool = Field(
        default=False, description="Whether an embedded EXIF thumbnail was found"
    )
    thumbnail_base64: str | None = Field(
        default=None, description="Base64-encoded embedded thumbnail (data URI)"
    )
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when analysis was performed",
    )


class GeoClue(BaseModel):
    """A single visual clue the model used to reason about the photo's location."""

    category: str = Field(
        ...,
        description="Kind of clue, e.g. 'road_markings', 'signage_language', 'license_plate', "
        "'architecture', 'vegetation', 'driving_side', 'utility_infrastructure'",
    )
    observation: str = Field(..., description="What was observed in the photo")
    supports: str = Field(..., description="What this observation suggests about the location")


class GeoCandidate(BaseModel):
    """A single candidate location, ranked by confidence."""

    location: str = Field(
        ..., description="Best-guess place name, e.g. a country or region - not a precise address"
    )
    confidence: float = Field(..., description="Model's confidence in this candidate", ge=0, le=1)
    reasoning: str = Field(..., description="Why this candidate fits the observed clues")


class ImageGeolocationAIResult(BaseModel):
    """Structured output requested from the LLM.

    model_used is filled in by the service, not the model.
    """

    candidates: list[GeoCandidate] = Field(
        ..., description="Ranked candidate locations, most likely first"
    )
    clues: list[GeoClue] = Field(..., description="Visual clues the model identified in the photo")
    caveats: str | None = Field(
        default=None, description="Model's own caveats about the reliability of this hypothesis"
    )


class ImageGeolocationResponse(ImageGeolocationAIResult):
    """AI-generated location hypothesis for a photo, with supporting reasoning."""

    model_used: str = Field(..., description="ID of the LLM model that produced this analysis")


class MarkerSegment(BaseModel):
    """A single JPEG marker segment found while walking the file byte-by-byte."""

    marker_type: str = Field(
        ..., description="Human-readable marker name, e.g. 'APP1', 'DQT', 'Scan Data'"
    )
    marker_code: str = Field(
        default="",
        description=(
            "Hex marker code, e.g. '0xE1' - empty for pseudo-entries like scan/trailing data"
        ),
    )
    offset: int = Field(..., description="Byte offset of this segment within the file", ge=0)
    length: int | None = Field(default=None, description="Segment length in bytes, if applicable")
    raw_hex: str | None = Field(
        default=None, description="Hex preview of the segment payload, capped in size"
    )
    truncated: bool = Field(
        default=False, description="Whether raw_hex was capped and doesn't cover the full payload"
    )


class QuantizationTable(BaseModel):
    """An 8x8 DQT quantization table, de-zigzagged into natural (row-major) order."""

    table_id: int = Field(..., description="Quantization table id (0-3)")
    precision: int = Field(..., description="Bits per value: 8 or 16")
    values: list[int] = Field(..., description="64 values in natural row-major order")
    quality_estimate: int | None = Field(
        default=None, description="Estimated JPEG save quality (1-100) derived from this table"
    )


class HuffmanTable(BaseModel):
    """A DHT Huffman table's code-length distribution."""

    table_class: str = Field(..., description="'DC' or 'AC'")
    table_id: int = Field(..., description="Huffman table id (0-3)")
    code_lengths: list[int] = Field(..., description="Number of codes for each code length 1-16")
    total_codes: int = Field(..., description="Total number of Huffman codes defined in this table")


class FrameComponent(BaseModel):
    """A single color component from the SOF frame header."""

    component_id: int = Field(..., description="Component identifier (e.g. 1=Y, 2=Cb, 3=Cr)")
    horizontal_sampling: int = Field(..., description="Horizontal sampling factor")
    vertical_sampling: int = Field(..., description="Vertical sampling factor")
    quantization_table_id: int = Field(
        ..., description="Quantization table id used by this component"
    )


class FrameInfo(BaseModel):
    """Frame parameters decoded from the SOF marker."""

    frame_type: str = Field(..., description="e.g. 'Baseline (SOF0)', 'Progressive (SOF2)'")
    is_progressive: bool = Field(..., description="Whether this is a progressive JPEG")
    precision: int = Field(..., description="Sample precision in bits")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    components: list[FrameComponent] = Field(
        ..., description="Color components and their sampling factors"
    )
    chroma_subsampling: str = Field(
        ..., description="e.g. '4:4:4', '4:2:2', '4:2:0', 'custom', 'N/A'"
    )


class ImageStructureResponse(BaseModel):
    """JPEG structure/quality analysis: marker map, quantization/Huffman tables, frame info."""

    filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="Size of the uploaded file in bytes", ge=0)
    markers: list[MarkerSegment] = Field(
        ..., description="Ordered list of every marker segment found in the file"
    )
    quantization_tables: list[QuantizationTable] = Field(
        default_factory=list, description="DQT tables found"
    )
    huffman_tables: list[HuffmanTable] = Field(default_factory=list, description="DHT tables found")
    frame: FrameInfo | None = Field(
        default=None, description="Frame parameters from the SOF marker"
    )
    overall_quality_estimate: int | None = Field(
        default=None, description="Average quality estimate across all quantization tables"
    )
    compression_ratio: float | None = Field(
        default=None, description="Estimated raw-to-compressed size ratio"
    )
    bits_per_pixel: float | None = Field(default=None, description="Compressed bits per pixel")


class AnomalyFinding(BaseModel):
    """A single forensic check that flagged something worth a closer look."""

    check: str = Field(
        ..., description="Identifier of the check, e.g. 'trailing_data', 'timestamp_consistency'"
    )
    severity: str = Field(..., description="'info' or 'warning'")
    message: str = Field(..., description="Human-readable description of what was found")


class ImageAnomalyResponse(BaseModel):
    """Result of running the image tampering/anomaly heuristics."""

    filename: str = Field(..., description="Original uploaded filename")
    findings: list[AnomalyFinding] = Field(
        default_factory=list, description="Anomalies found - empty means none detected"
    )
    checks_run: int = Field(..., description="Number of forensic checks executed")


class FieldDiff(BaseModel):
    """One EXIF/IPTC/XMP field compared between two images."""

    field: str = Field(..., description="Full tag name, e.g. 'EXIF DateTimeOriginal'")
    left_value: str | None = Field(default=None, description="Value in the first image, if present")
    right_value: str | None = Field(
        default=None, description="Value in the second image, if present"
    )
    status: str = Field(..., description="'match', 'differ', 'only_left', or 'only_right'")


class FieldDiffSummary(BaseModel):
    match_count: int = Field(..., description="Fields present in both with the same value")
    differ_count: int = Field(..., description="Fields present in both with different values")
    only_left_count: int = Field(..., description="Fields only present in the first image")
    only_right_count: int = Field(..., description="Fields only present in the second image")


class ImageCompareResponse(BaseModel):
    """Field-by-field comparison of two images."""

    left: ImageFileInfo = Field(..., description="File properties of the first image")
    right: ImageFileInfo = Field(..., description="File properties of the second image")
    field_diffs: list[FieldDiff] = Field(
        ..., description="Every EXIF/IPTC/XMP field found in either image"
    )
    summary: FieldDiffSummary = Field(..., description="Counts by diff status")
    phash_distance: int = Field(
        ...,
        description=(
            "Hamming distance between the two images' perceptual hashes (0-64, "
            "lower = more visually similar)"
        ),
    )
    pixels_likely_match: bool = Field(
        ...,
        description=(
            "True if the perceptual hash distance is low enough that the pixel "
            "content is probably the same"
        ),
    )


class Histograms(BaseModel):
    """256-bin histograms of pixel intensity, per channel."""

    red: list[int] = Field(..., description="256-bin histogram of the red channel")
    green: list[int] = Field(..., description="256-bin histogram of the green channel")
    blue: list[int] = Field(..., description="256-bin histogram of the blue channel")
    luminance: list[int] = Field(..., description="256-bin histogram of luma (Y)")
    cb: list[int] = Field(..., description="256-bin histogram of the Cb chroma channel")
    cr: list[int] = Field(..., description="256-bin histogram of the Cr chroma channel")


class Vectorscope(BaseModel):
    """2D Cb x Cr histogram - a classic vectorscope for spotting color-balance/cast issues."""

    bin_count: int = Field(..., description="Grid is bin_count x bin_count (Cb x Cr)")
    counts: list[int] = Field(
        ..., description="Row-major counts (Cb rows, Cr columns), length bin_count^2"
    )
    max_count: int = Field(
        ..., description="Highest single-bin count, for normalizing display intensity"
    )


class ImageVisualAnalysisResponse(BaseModel):
    """Pixel-level visual analysis: RGB/luminance/chroma histograms and a CbCr vectorscope."""

    filename: str = Field(..., description="Original uploaded filename")
    histograms: Histograms = Field(..., description="Per-channel intensity histograms")
    vectorscope: Vectorscope = Field(..., description="Cb/Cr color-distribution vectorscope")


class ImageHealthResponse(BaseModel):
    """Health check response for the image tools service."""

    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    endpoints: list[str] = Field(..., description="Available endpoints")
    supported_formats: list[str] = Field(..., description="Supported file extensions")
    max_file_size: str = Field(..., description="Maximum file size")
