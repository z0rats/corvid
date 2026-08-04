import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ImageTools from './ImageTools';
import { imageAnalyzerApi } from './services/api/imageAnalyzerApi';
import { imageAnomalyApi } from './services/api/imageAnomalyApi';
import { imageStructureApi } from './services/api/imageStructureApi';
import { imageVisualAnalysisApi } from './services/api/imageVisualAnalysisApi';

vi.mock('./services/api/imageAnalyzerApi');
// Every chapter mounts at once now (scroll-spy, not a tab switcher), so the
// chapters that auto-analyze on mount need their API calls stubbed here too -
// otherwise they'd fire real, unmocked network requests during this test.
vi.mock('./services/api/imageAnomalyApi');
vi.mock('./services/api/imageStructureApi');
vi.mock('./services/api/imageVisualAnalysisApi');

beforeEach(() => {
  global.URL.createObjectURL = vi.fn(() => 'blob:mock-preview-url');
  global.URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.clearAllMocks();
});

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

function renderImageTools(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ImageTools />
    </MemoryRouter>,
  );
}

describe('ImageTools', () => {
  it('shows the welcome screen before any image is analyzed', () => {
    renderImageTools();

    expect(screen.getByText(/lets you inspect an image file/i)).toBeInTheDocument();
  });

  it('shows reverse-search links as soon as a URL is typed, with no file uploaded', async () => {
    const user = userEvent.setup();
    renderImageTools();

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
    renderImageTools();

    const input = document.querySelector('input[type="file"]');
    await user.upload(input, makeFile());

    await waitFor(() => expect(screen.getByRole('button', { name: /analyze/i })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    await waitFor(() => expect(screen.getByText('photo.jpg')).toBeInTheDocument());

    expect(imageAnalyzerApi.analyzeImage).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/lets you inspect an image file/i)).not.toBeInTheDocument();

    // No GPS in this result - the GPS Location chapter shouldn't appear at all.
    expect(screen.queryByText('GPS Location')).not.toBeInTheDocument();

    // EXIF & Tags is a stacked section on the same scrollable document, not a
    // hidden tab - its content is already visible without clicking anything.
    expect(screen.getByText('Software')).toBeInTheDocument();
    expect(screen.getByText('TestSoftware 1.0')).toBeInTheDocument();
  });

  it('shows an error message when analysis fails', async () => {
    imageAnalyzerApi.analyzeImage.mockRejectedValue({
      response: { data: { detail: 'Image analysis failed' } },
    });

    const user = userEvent.setup();
    renderImageTools();

    const input = document.querySelector('input[type="file"]');
    await user.upload(input, makeFile());
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    await waitFor(() => expect(screen.getByText('Image analysis failed')).toBeInTheDocument());
    expect(screen.getByText(/lets you inspect an image file/i)).toBeInTheDocument();
  });

  it('auto-analyzes a file handed off via router state (command palette image paste)', async () => {
    imageAnalyzerApi.analyzeImage.mockResolvedValue({
      file_info: {
        filename: 'handoff.jpg', format: 'JPEG', mime_type: 'image/jpeg',
        width: 10, height: 10, mode: 'RGB', dpi_x: 72, dpi_y: 72, file_size: 100,
      },
      hashes: { md5: 'a'.repeat(32), sha1: 'b'.repeat(40), sha256: 'c'.repeat(64) },
      exif: {}, gps: null, has_thumbnail: false, thumbnail_base64: null,
    });

    const handoffFile = makeFile();
    renderImageTools([{ pathname: '/image-tools', state: { file: handoffFile } }]);

    await waitFor(() => expect(imageAnalyzerApi.analyzeImage).toHaveBeenCalledTimes(1));
    expect(imageAnalyzerApi.analyzeImage).toHaveBeenCalledWith(handoffFile);
  });
});
