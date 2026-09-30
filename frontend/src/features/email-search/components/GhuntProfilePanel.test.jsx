import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import GhuntProfilePanel from './GhuntProfilePanel';
import { useGhuntProfile } from '../hooks/api/useGhuntProfile';

vi.mock('../hooks/api/useGhuntProfile');

describe('GhuntProfilePanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('always shows the risk banner, even before health has loaded', () => {
    useGhuntProfile.mockReturnValue({
      health: null, result: null, loading: false, error: null, lookup: vi.fn(), reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    expect(screen.getByText(/Google's Terms of Service/i)).toBeInTheDocument();
  });

  it('disables the lookup button until a session is configured', () => {
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: false },
      result: null, loading: false, error: null, lookup: vi.fn(), reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    expect(screen.getByRole('button', { name: 'Look up Google profile' })).toBeDisabled();
    expect(screen.getByText('No GHunt session configured - add one under Settings > API Keys')).toBeInTheDocument();
  });

  it('does not run automatically when a session is configured', () => {
    const lookup = vi.fn();
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: true },
      result: null, loading: false, error: null, lookup, reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    expect(lookup).not.toHaveBeenCalled();
  });

  it('submits the entered email when the button is clicked', () => {
    const lookup = vi.fn();
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: true },
      result: null, loading: false, error: null, lookup, reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'target@gmail.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Look up Google profile' }));

    expect(lookup).toHaveBeenCalledWith('target@gmail.com');
  });

  it('renders the profile result', () => {
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: true },
      result: {
        gaia_id: '123456789',
        email: 'target@gmail.com',
        profile_photo: { url: 'https://example.com/photo.jpg', is_default: false },
        cover_photo: null,
        last_profile_edit: '2024-03-15T10:30:00Z',
        user_types: ['GOOGLE_USER'],
        activated_services: ['Gmail'],
        entity_type: null,
        is_enterprise_user: false,
        play_games: null,
        maps: null,
        calendar: null,
      },
      loading: false,
      error: null,
      lookup: vi.fn(),
      reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    expect(screen.getByText('target@gmail.com')).toBeInTheDocument();
    expect(screen.getByText(/123456789/)).toBeInTheDocument();
    expect(screen.getByText('GOOGLE_USER')).toBeInTheDocument();
    expect(screen.getByText('Gmail')).toBeInTheDocument();
  });

  it('maps a known error code to a localized message', () => {
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: true },
      result: null,
      loading: false,
      error: { code: 'GHUNT_NOT_FOUND', message: 'No public Google account found for this email' },
      lookup: vi.fn(),
      reset: vi.fn(),
    });

    render(<GhuntProfilePanel />);

    expect(screen.getByText('No public Google account found for this email')).toBeInTheDocument();
  });
});

describe('GhuntProfilePanel prefill', () => {
  it('fills the email field from a found-provider action without running the lookup', () => {
    const lookup = vi.fn();
    useGhuntProfile.mockReturnValue({
      health: { installed: true, session_configured: true },
      result: null, loading: false, error: null, lookup, reset: vi.fn(),
    });

    const { rerender } = render(<GhuntProfilePanel prefill={null} />);
    rerender(<GhuntProfilePanel prefill={{ email: 'target@gmail.com', seq: 1 }} />);

    expect(screen.getByLabelText('Email address').value).toBe('target@gmail.com');
    expect(lookup).not.toHaveBeenCalled();
  });
});
