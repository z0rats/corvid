import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ImageGeolocationPanel from './ImageGeolocationPanel';
import { useImageGeolocation } from '../../hooks/api/useImageGeolocation';
import { geolocationHistoryApi } from '../../services/api/geolocationHistoryApi';

vi.mock('../../hooks/api/useImageGeolocation');
vi.mock('../../services/api/geolocationHistoryApi');
vi.mock('./GeolocationHistoryList', () => ({
  default: ({ onSelect }) => (
    <button onClick={() => onSelect({ id: 7 })}>select-history-row</button>
  ),
}));

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
    fireEvent.click(screen.getByRole('button', { name: 'Guess location with AI' }));

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
        history_id: 3,
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

  it('shows report download buttons once a result has a history_id', () => {
    useImageGeolocation.mockReturnValue({
      result: {
        candidates: [{ location: 'Serbia', confidence: 0.6, reasoning: 'clues' }],
        clues: [],
        caveats: null,
        model_used: 'claude-sonnet-4-6',
        history_id: 42,
      },
      loading: false,
      error: null,
      hasLlmKey: true,
      geolocateImage: vi.fn(),
    });
    geolocationHistoryApi.reportUrl.mockReturnValue('https://corvid.test/report');

    render(<ImageGeolocationPanel file={makeFile()} />);

    expect(screen.getByRole('link', { name: 'HTML' })).toHaveAttribute(
      'href',
      'https://corvid.test/report'
    );
    expect(screen.getByRole('link', { name: 'PDF' })).toBeInTheDocument();
  });

  it('does not show report download buttons without a history_id', () => {
    useImageGeolocation.mockReturnValue({
      result: {
        candidates: [{ location: 'Serbia', confidence: 0.6, reasoning: 'clues' }],
        clues: [],
        caveats: null,
        model_used: 'claude-sonnet-4-6',
        history_id: null,
      },
      loading: false,
      error: null,
      hasLlmKey: true,
      geolocateImage: vi.fn(),
    });

    render(<ImageGeolocationPanel file={makeFile()} />);

    expect(screen.queryByRole('link', { name: 'HTML' })).not.toBeInTheDocument();
  });

  it('toggles the history list and loads a selected past analysis', async () => {
    useImageGeolocation.mockReturnValue({
      result: null, loading: false, error: null, hasLlmKey: true, geolocateImage: vi.fn(),
    });
    geolocationHistoryApi.getSearch.mockResolvedValue({
      id: 7,
      model_used: 'claude-sonnet-4-6',
      result: {
        candidates: [{ location: 'Chile', confidence: 0.4, reasoning: 'clues' }],
        clues: [],
        caveats: null,
      },
    });

    render(<ImageGeolocationPanel file={makeFile()} />);
    fireEvent.click(screen.getByRole('button', { name: 'History' }));
    expect(screen.getByText('select-history-row')).toBeInTheDocument();

    fireEvent.click(screen.getByText('select-history-row'));

    await waitFor(() => expect(screen.getByText('Chile')).toBeInTheDocument());
    expect(geolocationHistoryApi.getSearch).toHaveBeenCalledWith(7);
    expect(screen.queryByText('select-history-row')).not.toBeInTheDocument();
  });
});
