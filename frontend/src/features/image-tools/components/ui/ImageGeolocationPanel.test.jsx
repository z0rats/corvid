import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ImageGeolocationPanel from './ImageGeolocationPanel';
import { useImageGeolocation } from '../../hooks/api/useImageGeolocation';

vi.mock('../../hooks/api/useImageGeolocation');

function makeFile() {
  return new File(['fake image content'], 'street.jpg', { type: 'image/jpeg' });
}

describe('ImageGeolocationPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when no LLM API key is configured', () => {
    useImageGeolocation.mockReturnValue({
      result: null, loading: false, error: null, hasLlmKey: false, geolocateImage: vi.fn(),
    });

    const { container } = render(<ImageGeolocationPanel file={makeFile()} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when no file has been uploaded yet', () => {
    useImageGeolocation.mockReturnValue({
      result: null, loading: false, error: null, hasLlmKey: true, geolocateImage: vi.fn(),
    });

    const { container } = render(<ImageGeolocationPanel file={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('triggers analysis with the uploaded file when the button is clicked', () => {
    const geolocateImage = vi.fn();
    useImageGeolocation.mockReturnValue({
      result: null, loading: false, error: null, hasLlmKey: true, geolocateImage,
    });
    const file = makeFile();

    render(<ImageGeolocationPanel file={file} />);
    fireEvent.click(screen.getByRole('button'));

    expect(geolocateImage).toHaveBeenCalledWith(file);
  });

  it('shows the error message on failure', () => {
    useImageGeolocation.mockReturnValue({
      result: null, loading: false, error: 'No LLM models available', hasLlmKey: true, geolocateImage: vi.fn(),
    });

    render(<ImageGeolocationPanel file={makeFile()} />);

    expect(screen.getByText('No LLM models available')).toBeInTheDocument();
  });

  it('renders candidates, clues, and caveats from a successful result', () => {
    useImageGeolocation.mockReturnValue({
      result: {
        candidates: [{ location: 'Serbia', confidence: 0.6, reasoning: 'road markings + signage' }],
        clues: [{ category: 'signage_language', observation: 'Cyrillic text', supports: 'Serbia/Balkans' }],
        caveats: 'Hypothesis only, not confirmed.',
        model_used: 'claude-sonnet-4-6',
      },
      loading: false,
      error: null,
      hasLlmKey: true,
      geolocateImage: vi.fn(),
    });

    render(<ImageGeolocationPanel file={makeFile()} />);

    expect(screen.getByText('Serbia')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('road markings + signage')).toBeInTheDocument();
    expect(screen.getByText('signage_language')).toBeInTheDocument();
    expect(screen.getByText('Hypothesis only, not confirmed.')).toBeInTheDocument();
    expect(screen.getByText(/claude-sonnet-4-6/)).toBeInTheDocument();
  });
});
