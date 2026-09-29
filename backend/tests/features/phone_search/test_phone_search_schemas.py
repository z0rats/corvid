import pytest
from pydantic import ValidationError

from app.features.phone_search.schemas.phone_search_schemas import ScanRequest


class TestScanRequestPhoneNumberValidation:
    @pytest.mark.parametrize(
        "phone_number", ["+15551234567", "+442071838750", "+79991234567", "+861012345678"]
    )
    def test_accepts_valid_e164_numbers(self, phone_number):
        assert ScanRequest(phone_number=phone_number).phone_number == phone_number

    def test_strips_surrounding_whitespace(self):
        assert ScanRequest(phone_number="  +15551234567  ").phone_number == "+15551234567"

    @pytest.mark.parametrize(
        "phone_number",
        [
            "15551234567",  # missing leading '+'
            "+0551234567",  # leading zero after '+'
            "+1555123",  # too short
            "not-a-number",
            "+1 555 123 4567",  # formatting punctuation not accepted
            "",
        ],
    )
    def test_rejects_invalid_input(self, phone_number):
        with pytest.raises(ValidationError):
            ScanRequest(phone_number=phone_number)
