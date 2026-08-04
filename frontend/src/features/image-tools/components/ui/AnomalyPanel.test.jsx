import React from 'react';
import { render, screen } from '@testing-library/react';
import AnomalyPanel from './AnomalyPanel';
import { useImageAnomalies } from '../../hooks/api/useImageAnomalies';

vi.mock('../../hooks/api/useImageAnomalies');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('AnomalyPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('automatically runs anomaly detection on mount, with no button click required', () => {
    const analyzeAnomalies = vi.fn();
    useImageAnomalies.mockReturnValue({ result: null, loading: false, error: null, analyzeAnomalies });
    const file = makeFile();

    render(<AnomalyPanel file={file} />);

    expect(analyzeAnomalies).toHaveBeenCalledWith(file);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('shows a clean verdict when there are no findings', () => {
    useImageAnomalies.mockReturnValue({
      result: { filename: 'photo.jpg', findings: [], checks_run: 3 },
      loading: false,
      error: null,
      analyzeAnomalies: vi.fn(),
    });

    render(<AnomalyPanel file={makeFile()} />);

    expect(screen.getByText('No anomalies detected')).toBeInTheDocument();
    expect(screen.getByText('3 forensic checks run')).toBeInTheDocument();
  });

  it('lists findings with their check label and message', () => {
    useImageAnomalies.mockReturnValue({
      result: {
        filename: 'photo.jpg',
        findings: [
          { check: 'trailing_data', severity: 'warning', message: '24 bytes found after the JPEG end marker (EOI)' },
        ],
        checks_run: 5,
      },
      loading: false,
      error: null,
      analyzeAnomalies: vi.fn(),
    });

    render(<AnomalyPanel file={makeFile()} />);

    expect(screen.getByText('Trailing data')).toBeInTheDocument();
    expect(screen.getByText('24 bytes found after the JPEG end marker (EOI)')).toBeInTheDocument();
    expect(screen.queryByText('No anomalies detected')).not.toBeInTheDocument();
  });

  it('shows the error message on failure', () => {
    useImageAnomalies.mockReturnValue({
      result: null, loading: false, error: 'File is not a recognized image format', analyzeAnomalies: vi.fn(),
    });

    render(<AnomalyPanel file={makeFile()} />);

    expect(screen.getByText('File is not a recognized image format')).toBeInTheDocument();
  });
});
