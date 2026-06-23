import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.features.image_tools.routers import image_routes


@pytest.fixture
def client():
    """A minimal FastAPI app exposing only the image_tools router.

    Avoids spinning up the full application (database, scheduler, other
    feature routers) so this test only exercises the image_tools API contract.
    """
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(image_routes.router)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check_reports_supported_formats(self, client):
        response = client.get('/api/image/health')

        assert response.status_code == 200
        body = response.json()
        assert body['service'] == 'image_tools'
        assert body['status'] == 'healthy'
        assert '.jpg' in body['supported_formats']


class TestAnalyzeEndpoint:
    def test_analyzes_valid_image(self, client, plain_jpeg_bytes):
        response = client.post(
            '/api/image/analyze',
            files={'file': ('photo.jpg', plain_jpeg_bytes, 'image/jpeg')},
        )

        assert response.status_code == 200
        body = response.json()
        assert body['file_info']['filename'] == 'photo.jpg'
        assert body['file_info']['format'] == 'JPEG'
        assert 'md5' in body['hashes']

    def test_extracts_gps_from_uploaded_image(self, client, jpeg_with_gps):
        response = client.post(
            '/api/image/analyze',
            files={'file': ('gps.jpg', jpeg_with_gps, 'image/jpeg')},
        )

        assert response.status_code == 200
        body = response.json()
        assert body['gps'] is not None
        assert body['gps']['latitude'] == pytest.approx(40.446194, abs=1e-5)

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            '/api/image/analyze',
            files={'file': ('document.pdf', b'%PDF-1.4 fake', 'application/pdf')},
        )

        assert response.status_code == 400
        assert 'Invalid file type' in response.json()['detail']

    def test_rejects_empty_file(self, client):
        response = client.post(
            '/api/image/analyze',
            files={'file': ('photo.jpg', b'', 'image/jpeg')},
        )

        assert response.status_code == 400

    def test_rejects_corrupt_image_with_valid_extension(self, client):
        response = client.post(
            '/api/image/analyze',
            files={'file': ('photo.jpg', b'not actually a jpeg', 'image/jpeg')},
        )

        assert response.status_code == 422

    def test_missing_file_is_rejected(self, client):
        response = client.post('/api/image/analyze')

        assert response.status_code == 422
