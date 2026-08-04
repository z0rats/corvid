import React from 'react';
import { render, screen } from '@testing-library/react';
import ImageStructurePanel from './ImageStructurePanel';
import { useImageStructure } from '../../hooks/api/useImageStructure';
import { useImageVisualAnalysis } from '../../hooks/api/useImageVisualAnalysis';

vi.mock('../../hooks/api/useImageStructure');
vi.mock('../../hooks/api/useImageVisualAnalysis');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('ImageStructurePanel', () => {
  beforeEach(() => {
    useImageVisualAnalysis.mockReturnValue({ result: null, loading: false, error: null, analyzeVisuals: vi.fn() });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('shows a JPEG-only notice for non-JPEG formats and never calls analyzeStructure', () => {
    const analyzeStructure = vi.fn();
    useImageStructure.mockReturnValue({ result: null, loading: false, error: null, analyzeStructure });

    render(<ImageStructurePanel file={makeFile()} format="PNG" />);

    expect(screen.getByText(/only available for jpeg/i)).toBeInTheDocument();
    expect(analyzeStructure).not.toHaveBeenCalled();
  });

  it('automatically analyzes the uploaded JPEG on mount, with no button click required', () => {
    const analyzeStructure = vi.fn();
    useImageStructure.mockReturnValue({ result: null, loading: false, error: null, analyzeStructure });
    const file = makeFile();

    render(<ImageStructurePanel file={file} format="JPEG" />);

    expect(analyzeStructure).toHaveBeenCalledWith(file);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('shows the error message on failure', () => {
    useImageStructure.mockReturnValue({ result: null, loading: false, error: 'Not a valid JPEG file', analyzeStructure: vi.fn() });

    render(<ImageStructurePanel file={makeFile()} format="JPEG" />);

    expect(screen.getByText('Not a valid JPEG file')).toBeInTheDocument();
  });

  it('renders frame info, quantization tables, and the marker map from a successful result', () => {
    useImageStructure.mockReturnValue({
      result: {
        frame: { width: 100, height: 80, is_progressive: false, chroma_subsampling: '4:2:0' },
        overall_quality_estimate: 80,
        compression_ratio: 12.5,
        bits_per_pixel: 1.9,
        quantization_tables: [{ table_id: 0, precision: 8, values: Array(64).fill(10), quality_estimate: 80 }],
        huffman_tables: [{ table_class: 'DC', table_id: 0, code_lengths: Array(16).fill(1), total_codes: 12 }],
        markers: [
          { marker_type: 'SOI', marker_code: '0xD8', offset: 0, length: null, raw_hex: null, truncated: false },
          { marker_type: 'DQT', marker_code: '0xDB', offset: 2, length: 67, raw_hex: '0a0a0a', truncated: false },
        ],
      },
      loading: false,
      error: null,
      analyzeStructure: vi.fn(),
    });

    render(<ImageStructurePanel file={makeFile()} format="JPEG" />);

    expect(screen.getByText('100 × 80 px')).toBeInTheDocument();
    expect(screen.getByText('4:2:0')).toBeInTheDocument();
    expect(screen.getByText(/marker map \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText('SOI')).toBeInTheDocument();
    expect(screen.getByText('DQT')).toBeInTheDocument();
  });
});
