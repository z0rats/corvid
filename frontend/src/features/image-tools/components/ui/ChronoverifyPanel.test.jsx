import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ChronoverifyPanel from './ChronoverifyPanel';
import { useChronoverify } from '../../hooks/api/useChronoverify';

vi.mock('../../hooks/api/useChronoverify');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('ChronoverifyPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('does not run automatically on mount, unlike the local anomaly checks', () => {
    const checkProvenance = vi.fn();
    useChronoverify.mockReturnValue({
      result: null, loading: false, error: null, checkProvenance, reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={makeFile()} />);

    expect(checkProvenance).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Check with ChronoVerify' })).toBeInTheDocument();
  });

  it('calls checkProvenance with the file when the button is clicked', () => {
    const checkProvenance = vi.fn();
    const file = makeFile();
    useChronoverify.mockReturnValue({
      result: null, loading: false, error: null, checkProvenance, reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={file} />);
    fireEvent.click(screen.getByRole('button', { name: 'Check with ChronoVerify' }));

    expect(checkProvenance).toHaveBeenCalledWith(file);
  });

  it('renders the verdict, confidence, and summary', () => {
    useChronoverify.mockReturnValue({
      result: {
        verdict: 'consistent',
        confidence: 72,
        summary: 'Metadata layers agree and no editing signals fired.',
        capture_time: null,
        capture_device: null,
        location: null,
        c2pa: null,
        signals: [],
        sha256: null,
      },
      loading: false,
      error: null,
      checkProvenance: vi.fn(),
      reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={makeFile()} />);

    expect(screen.getByText('Consistent')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 72/100')).toBeInTheDocument();
    expect(screen.getByText('Metadata layers agree and no editing signals fired.')).toBeInTheDocument();
  });

  it('renders recovered device, location, and C2PA status', () => {
    useChronoverify.mockReturnValue({
      result: {
        verdict: 'provenance_confirmed',
        confidence: 95,
        summary: 'Validated Content Credentials found.',
        capture_time: '2026-03-14T09:21:30',
        capture_device: { make: 'Canon', model: 'EOS R6' },
        location: { present: true, place: 'near Sedona, Arizona', city: null, region: null, country: null, latitude: null, longitude: null },
        c2pa: { present: true, validated: true },
        signals: [],
        sha256: 'abc123',
      },
      loading: false,
      error: null,
      checkProvenance: vi.fn(),
      reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={makeFile()} />);

    expect(screen.getByText('Canon EOS R6')).toBeInTheDocument();
    expect(screen.getByText('near Sedona, Arizona')).toBeInTheDocument();
    expect(screen.getByText('Validated (C2PA)')).toBeInTheDocument();
    expect(screen.getByText('abc123')).toBeInTheDocument();
  });

  it('lists signal details', () => {
    useChronoverify.mockReturnValue({
      result: {
        verdict: 'manipulation_indicated',
        confidence: 60,
        summary: 'Multiple signals are consistent with possible editing',
        capture_time: null,
        capture_device: null,
        location: null,
        c2pa: null,
        signals: [
          { name: 'ela_localized_anomaly', layer: 'pixel', direction: 'anomalous', detail: 'A local region has re-save error far above the rest of the frame.' },
        ],
        sha256: null,
      },
      loading: false,
      error: null,
      checkProvenance: vi.fn(),
      reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={makeFile()} />);

    expect(screen.getByText(/A local region has re-save error/)).toBeInTheDocument();
  });

  it('shows the error message on failure', () => {
    useChronoverify.mockReturnValue({
      result: null, loading: false, error: 'ChronoVerify rate limit reached', checkProvenance: vi.fn(), reset: vi.fn(),
    });

    render(<ChronoverifyPanel file={makeFile()} />);

    expect(screen.getByText('ChronoVerify rate limit reached')).toBeInTheDocument();
  });
});
