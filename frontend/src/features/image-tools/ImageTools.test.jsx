import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImageTools from './ImageTools';
import { imageAnalyzerApi } from './services/api/imageAnalyzerApi';

jest.mock('./services/api/imageAnalyzerApi');

beforeEach(() => {
  global.URL.createObjectURL = jest.fn(() => 'blob:mock-preview-url');
  global.URL.revokeObjectURL = jest.fn();
});

afterEach(() => {
  jest.clearAllMocks();
});

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('ImageTools', () => {
  it('shows the welcome screen before any image is analyzed', () => {
    render(<ImageTools />);

    expect(screen.getByText(/lets you inspect an image file/i)).toBeInTheDocument();
  });

  it('shows reverse-search links as soon as a URL is typed, with no file uploaded', async () => {
    const user = userEvent.setup();
    render(<ImageTools />);

    expect(screen.getByText(/no image url provided/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'TinEye' })).toHaveAttribute(
      'href',
      'https://tineye.com/'
    );

    await user.type(screen.getByLabelText(/image url/i), 'https://example.com/photo.jpg');

    expect(screen.getByText(/open this image in a reverse-search engine/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'TinEye' })).toHaveAttribute(
      'href',
      'https://tineye.com/search?url=https%3A%2F%2Fexample.com%2Fphoto.jpg'
    );
    expect(imageAnalyzerApi.analyzeImage).not.toHaveBeenCalled();
  });

  it('uploads an image and renders the analysis result', async () => {
    imageAnalyzerApi.analyzeImage.mockResolvedValue({
      file_info: {
        filename: 'photo.jpg',
        format: 'JPEG',
        mime_type: 'image/jpeg',
        width: 100,
        height: 80,
        mode: 'RGB',
        dpi_x: 72,
        dpi_y: 72,
        file_size: 1024,
      },
      hashes: { md5: 'a'.repeat(32), sha1: 'b'.repeat(40), sha256: 'c'.repeat(64) },
      exif: { 'Image Software': 'TestSoftware 1.0' },
      gps: null,
      has_thumbnail: false,
      thumbnail_base64: null,
    });

    const user = userEvent.setup();
    render(<ImageTools />);

    const input = document.querySelector('input[type="file"]');
    await user.upload(input, makeFile());

    await waitFor(() => expect(screen.getByRole('button', { name: /analyze/i })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    await waitFor(() => expect(screen.getByText('photo.jpg')).toBeInTheDocument());

    expect(imageAnalyzerApi.analyzeImage).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/lets you inspect an image file/i)).not.toBeInTheDocument();
    expect(screen.getByText('Software')).toBeInTheDocument();
    expect(screen.getByText('TestSoftware 1.0')).toBeInTheDocument();
    expect(screen.getByText(/no gps data found/i)).toBeInTheDocument();
  });

  it('shows an error message when analysis fails', async () => {
    imageAnalyzerApi.analyzeImage.mockRejectedValue({
      response: { data: { detail: 'Image analysis failed' } },
    });

    const user = userEvent.setup();
    render(<ImageTools />);

    const input = document.querySelector('input[type="file"]');
    await user.upload(input, makeFile());
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    await waitFor(() => expect(screen.getByText('Image analysis failed')).toBeInTheDocument());
    expect(screen.getByText(/lets you inspect an image file/i)).toBeInTheDocument();
  });
});
