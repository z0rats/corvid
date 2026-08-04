from PIL import Image

from app.features.image_tools.utils.phash_utils import (
    compute_phash,
    hamming_distance,
    phash_to_bits,
    phash_to_hex,
)


def _gradient_image() -> Image.Image:
    image = Image.new('RGB', (100, 100))
    for x in range(100):
        for y in range(100):
            image.putpixel((x, y), (x * 2 % 256, y * 2 % 256, (x + y) % 256))
    return image


class TestComputePhash:
    def test_identical_images_produce_identical_hashes(self):
        image = _gradient_image()

        assert compute_phash(image) == compute_phash(image.copy())

    def test_visually_similar_images_have_a_small_hamming_distance(self):
        image = _gradient_image()
        slightly_resized = image.resize((96, 96)).resize((100, 100))

        distance = hamming_distance(compute_phash(image), compute_phash(slightly_resized))

        assert distance <= 10

    def test_very_different_images_have_a_large_hamming_distance(self):
        gradient = _gradient_image()
        solid = Image.new('RGB', (100, 100), color=(10, 200, 50))

        distance = hamming_distance(compute_phash(gradient), compute_phash(solid))

        assert distance > 10

    def test_returns_a_64_bit_value(self):
        phash = compute_phash(_gradient_image())

        assert 0 <= phash < (1 << 64)


class TestHammingDistance:
    def test_zero_for_identical_hashes(self):
        assert hamming_distance(0b1010, 0b1010) == 0

    def test_counts_differing_bits(self):
        assert hamming_distance(0b0000, 0b1111) == 4


class TestPhashFormatting:
    def test_hex_is_16_lowercase_hex_chars(self):
        hex_value = phash_to_hex(0xABCDEF0123456789)

        assert hex_value == 'abcdef0123456789'
        assert len(hex_value) == 16

    def test_bits_round_trip_to_the_same_integer(self):
        phash = compute_phash(_gradient_image())
        bits = phash_to_bits(phash)

        assert len(bits) == 64
        reconstructed = 0
        for bit in bits:
            reconstructed = (reconstructed << 1) | int(bit)
        assert reconstructed == phash
