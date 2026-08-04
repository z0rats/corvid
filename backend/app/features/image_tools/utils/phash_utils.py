"""Perceptual hash (pHash) - a 64-bit fingerprint of an image's visual content,
robust to re-encoding/resizing/minor edits (unlike the cryptographic MD5/SHA1/
SHA256 hashes, which change on any byte difference).

Standard DCT-based pHash algorithm (as popularized by Dr. Neal Krawetz and
implemented by libraries like `imagehash`): downscale to 32x32 grayscale, take
a 2D DCT, keep the top-left 8x8 low-frequency coefficients, threshold against
their median to get 64 bits.
"""

import numpy as np
from PIL import Image

HASH_SIZE = 8
HIGH_FREQ_FACTOR = 4
DCT_IMAGE_SIZE = HASH_SIZE * HIGH_FREQ_FACTOR  # 32


def _dct_matrix(size: int) -> np.ndarray:
    """Orthonormal DCT-II basis matrix, so `basis @ pixels @ basis.T` is the 2D DCT-II."""
    i = np.arange(size).reshape(1, -1)
    k = np.arange(size).reshape(-1, 1)
    matrix = np.cos(np.pi * (2 * i + 1) * k / (2 * size))
    matrix[0, :] *= 1 / np.sqrt(2)
    return matrix * np.sqrt(2.0 / size)


_DCT_BASIS = _dct_matrix(DCT_IMAGE_SIZE)


def compute_phash(image: Image.Image) -> int:
    """Compute a 64-bit perceptual hash, returned as a plain Python int."""
    pixels = np.asarray(
        image.convert("L").resize((DCT_IMAGE_SIZE, DCT_IMAGE_SIZE), Image.LANCZOS),
        dtype=float,
    )
    dct = _DCT_BASIS @ pixels @ _DCT_BASIS.T
    low_frequencies = dct[:HASH_SIZE, :HASH_SIZE]
    median = np.median(low_frequencies)

    bits = 0
    for value in low_frequencies.flatten():
        bits = (bits << 1) | int(value > median)
    return bits


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def phash_to_hex(phash: int) -> str:
    return f"{phash:016x}"


def phash_to_bits(phash: int, bit_count: int = HASH_SIZE * HASH_SIZE) -> list[bool]:
    """MSB-first bit list, e.g. for rendering as an 8x8 matrix (row-major)."""
    return [bool((phash >> (bit_count - 1 - i)) & 1) for i in range(bit_count)]
