import React from 'react';
import { render, screen } from '@testing-library/react';
import PixelAnalysisPanel from './PixelAnalysisPanel';
import { useImageVisualAnalysis } from '../../hooks/api/useImageVisualAnalysis';

vi.mock('../../hooks/api/useImageVisualAnalysis');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

function makeVisualResult() {
  const zeros = new Array(256).fill(0);
  return {
    histograms: { red: zeros, green: zeros, blue: zeros, luminance: zeros, cb: zeros, cr: zeros },
    vectorscope: { bin_count: 64, counts: new Array(64 * 64).fill(0), max_count: 0 },
  };
}

describe('PixelAnalysisPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('automatically runs visual analysis on mount, with no button click required', () => {
    const analyzeVisuals = vi.fn();
    useImageVisualAnalysis.mockReturnValue({ result: null, loading: false, error: null, analyzeVisuals });
    const file = makeFile();

    render(<PixelAnalysisPanel file={file} />);

    expect(analyzeVisuals).toHaveBeenCalledWith(file);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('shows the error message on failure', () => {
    useImageVisualAnalysis.mockReturnValue({
      result: null, loading: false, error: 'File is not a recognized image format', analyzeVisuals: vi.fn(),
    });

    render(<PixelAnalysisPanel file={makeFile()} />);

    expect(screen.getByText('File is not a recognized image format')).toBeInTheDocument();
  });

  it('renders histogram labels and the vectorscope from a successful result', () => {
    useImageVisualAnalysis.mockReturnValue({
      result: makeVisualResult(), loading: false, error: null, analyzeVisuals: vi.fn(),
    });

    render(<PixelAnalysisPanel file={makeFile()} />);

    expect(screen.getByText('Pixel Analysis')).toBeInTheDocument();
    expect(screen.getByText('Red')).toBeInTheDocument();
    expect(screen.getByText('Luminance (Y)')).toBeInTheDocument();
    expect(screen.getByText('CbCr vectorscope')).toBeInTheDocument();
  });

  it('renders nothing extra before a result arrives', () => {
    useImageVisualAnalysis.mockReturnValue({ result: null, loading: false, error: null, analyzeVisuals: vi.fn() });

    render(<PixelAnalysisPanel file={makeFile()} />);

    expect(screen.queryByText('Pixel Analysis')).not.toBeInTheDocument();
  });
});
