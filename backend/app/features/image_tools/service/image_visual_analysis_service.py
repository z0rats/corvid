"""Pixel-level visual analysis: RGB/luminance/chroma histograms and a CbCr vectorscope.

Downsamples large images first - histogram/vectorscope shape is statistically
representative without every pixel, and this keeps analysis fast even for a
50MB upload.
"""

import logging
from io import BytesIO

import numpy as np
from PIL import Image

from ..schemas.image_schemas import Histograms, ImageVisualAnalysisResponse, Vectorscope

logger = logging.getLogger(__name__)

MAX_ANALYSIS_DIMENSION = 512
VECTORSCOPE_BINS = 64


def _downsampled_rgb_array(data: bytes) -> np.ndarray:
    image = Image.open(BytesIO(data))
    image.load()
    rgb = image.convert("RGB")
    if max(rgb.size) > MAX_ANALYSIS_DIMENSION:
        rgb.thumbnail((MAX_ANALYSIS_DIMENSION, MAX_ANALYSIS_DIMENSION), Image.LANCZOS)
    return np.asarray(rgb, dtype=np.float64)


def _histogram(values: np.ndarray) -> list[int]:
    counts, _ = np.histogram(values, bins=256, range=(0, 256))
    return counts.astype(int).tolist()


def analyze_image_visuals(filename: str, data: bytes) -> ImageVisualAnalysisResponse:
    """Raises ValueError if the file isn't a readable image."""
    try:
        rgb = _downsampled_rgb_array(data)
    except Exception as e:
        raise ValueError("File is not a recognized image format") from e

    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    # ITU-R BT.601 full-range conversion - the same convention Pillow's own
    # Image.convert("YCbCr") uses, so this matches what a JPEG's own SOF/scan
    # data (already stored as YCbCr) actually encodes.
    y = np.clip(0.299 * r + 0.587 * g + 0.114 * b, 0, 255)
    cb = np.clip(128 - 0.168736 * r - 0.331264 * g + 0.5 * b, 0, 255)
    cr = np.clip(128 + 0.5 * r - 0.418688 * g - 0.081312 * b, 0, 255)

    histograms = Histograms(
        red=_histogram(r),
        green=_histogram(g),
        blue=_histogram(b),
        luminance=_histogram(y),
        cb=_histogram(cb),
        cr=_histogram(cr),
    )

    counts_2d, _, _ = np.histogram2d(
        cb.flatten(), cr.flatten(), bins=VECTORSCOPE_BINS, range=[[0, 256], [0, 256]]
    )
    counts_flat = counts_2d.astype(int).flatten().tolist()

    vectorscope = Vectorscope(
        bin_count=VECTORSCOPE_BINS,
        counts=counts_flat,
        max_count=max(counts_flat) if counts_flat else 0,
    )

    logger.info(
        "Visual analysis completed for '%s' (%sx%s after downsampling)",
        filename,
        rgb.shape[1],
        rgb.shape[0],
    )

    return ImageVisualAnalysisResponse(
        filename=filename, histograms=histograms, vectorscope=vectorscope
    )
