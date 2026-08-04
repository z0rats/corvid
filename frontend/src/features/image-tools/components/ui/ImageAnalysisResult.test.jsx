import React from 'react';
import { createElement } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import ImageAnalysisResult from './ImageAnalysisResult';
import { apiKeysState } from '../../../../core/state/atoms';
import { imageAnomalyApi } from '../../services/api/imageAnomalyApi';
import { imageStructureApi } from '../../services/api/imageStructureApi';
import { imageVisualAnalysisApi } from '../../services/api/imageVisualAnalysisApi';
import useMediaQuery from '@mui/material/useMediaQuery';

vi.mock('@mui/material/useMediaQuery');
// Every chapter mounts at once now (scroll-spy, not a tab switcher) - the
// Structure chapter (and its nested Pixel Analysis section) auto-analyzes on
// mount just like Anomalies, so its API calls need stubbing here too.
vi.mock('../../services/api/imageAnomalyApi');
vi.mock('../../services/api/imageStructureApi');
vi.mock('../../services/api/imageVisualAnalysisApi');

const BASE_RESULT = {
  file_info: { filename: 'photo.jpg', format: 'JPEG', width: 100, height: 80, file_size: 1024 },
  hashes: { md5: 'a'.repeat(32), sha1: 'b'.repeat(40), sha256: 'c'.repeat(64) },
  exif: { 'Image Software': 'TestSoftware 1.0' },
  gps: null,
};

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

function renderResult(result, { apiKeys = {} } = {}) {
  const store = createStore();
  store.set(apiKeysState, apiKeys);
  return render(
    createElement(
      Provider,
      { store },
      <ImageAnalysisResult result={result} previewUrl="blob:mock" file={makeFile()} />
    )
  );
}

describe('ImageAnalysisResult', () => {
  beforeEach(() => {
    useMediaQuery.mockReturnValue(false); // desktop sidebar by default
    imageAnomalyApi.analyzeAnomalies.mockResolvedValue({ filename: 'photo.jpg', findings: [], checks_run: 3 });
    imageStructureApi.analyzeStructure.mockResolvedValue({
      markers: [], quantization_tables: [], huffman_tables: [], frame: null,
      overall_quality_estimate: null, compression_ratio: null, bits_per_pixel: null,
    });
    imageVisualAnalysisApi.analyzeVisuals.mockResolvedValue({
      histograms: { red: [], green: [], blue: [], luminance: [], cb: [], cr: [] },
      vectorscope: { bin_count: 64, counts: [], max_count: 0 },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when there is no result', () => {
    const { container } = renderResult(null);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders every chapter\'s content simultaneously, as one scrollable document rather than a tab switcher', async () => {
    renderResult(BASE_RESULT);

    // General chapter content...
    expect(screen.getByText('1 KB')).toBeInTheDocument();
    // ...and EXIF chapter content, both visible without clicking anything
    expect(screen.getByText('TestSoftware 1.0')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('No anomalies detected')).toBeInTheDocument());
  });

  it('hides the GPS Location chapter (nav + section) when the result has no GPS data', () => {
    renderResult(BASE_RESULT);

    expect(screen.queryByText('GPS Location')).not.toBeInTheDocument();
  });

  it('shows the GPS Location chapter when GPS data is present', () => {
    renderResult({ ...BASE_RESULT, gps: { latitude: 40.44, longitude: -79.94, altitude: null, map_url: 'https://maps.example/?q=40.44,-79.94' } });

    // Appears twice: once in the nav list, once as the section heading.
    expect(screen.getAllByText('GPS Location').length).toBe(2);
  });

  it('scrolls to a chapter and marks its nav item selected when clicked', () => {
    const scrollIntoViewSpy = vi.spyOn(Element.prototype, 'scrollIntoView').mockImplementation(() => {});
    renderResult(BASE_RESULT);

    const [exifNavItem] = screen.getAllByText('EXIF & Tags');
    fireEvent.click(exifNavItem);

    expect(scrollIntoViewSpy).toHaveBeenCalled();
    expect(exifNavItem.closest('.MuiListItemButton-root')).toHaveClass('Mui-selected');

    scrollIntoViewSpy.mockRestore();
  });

  it('forces the last chapter active once the page is scrolled to the bottom (the last chapter can never scroll into the "active" band on its own)', () => {
    renderResult(BASE_RESULT);

    Object.defineProperty(document.documentElement, 'scrollHeight', { value: 2000, configurable: true });
    Object.defineProperty(window, 'innerHeight', { value: 800, configurable: true });
    Object.defineProperty(window, 'scrollY', { value: 1200, configurable: true }); // 800 + 1200 >= 2000

    fireEvent.scroll(window);

    const [removeMetadataNavItem] = screen.getAllByText('Remove Metadata');
    expect(removeMetadataNavItem.closest('.MuiListItemButton-root')).toHaveClass('Mui-selected');
  });

  it('auto-runs anomaly detection on mount, with no click required to see it', async () => {
    renderResult(BASE_RESULT);

    expect(imageAnomalyApi.analyzeAnomalies).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByText('No anomalies detected')).toBeInTheDocument());
  });

  it('hides the AI Geolocation chapter when no LLM API key is configured', () => {
    renderResult(BASE_RESULT, { apiKeys: {} });

    expect(screen.queryByText('AI Geolocation')).not.toBeInTheDocument();
  });

  it('shows the AI Geolocation chapter when an LLM API key is configured', () => {
    renderResult(BASE_RESULT, { apiKeys: { openai: 'sk-test' } });

    expect(screen.getAllByText('AI Geolocation').length).toBe(2);
  });

  it('renders a scrollable tab bar instead of the sidebar on narrow viewports', () => {
    useMediaQuery.mockReturnValue(true);
    renderResult(BASE_RESULT);

    expect(screen.getByRole('tablist')).toBeInTheDocument();
  });
});
