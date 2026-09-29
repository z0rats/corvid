import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InstagramSearch from './InstagramSearch';
import { instagramSearchApi } from './services/api/instagramSearchApi';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./services/api/instagramSearchApi');

function renderInstagramSearch(initialEntries = ['/instagram-search']) {
  return renderFeatureRoute(InstagramSearch, 'instagram-search', initialEntries);
}

afterEach(() => vi.clearAllMocks());

describe('InstagramSearch — form validation', () => {
  it('shows the welcome screen and a disabled lookup button before any search', () => {
    renderInstagramSearch();

    expect(screen.getByRole('button', { name: /look up/i })).toBeDisabled();
    expect(screen.getByText(/instagram profile lookup/i)).toBeInTheDocument();
  });

  it('enables the lookup button once a username is typed', async () => {
    renderInstagramSearch();

    await userEvent.type(screen.getByLabelText(/instagram username/i), 'someuser');

    expect(screen.getByRole('button', { name: /look up/i })).toBeEnabled();
  });

  it('links to the feature\'s documentation page', () => {
    renderInstagramSearch();

    expect(screen.getByRole('link', { name: /view documentation/i })).toHaveAttribute(
      'href',
      'https://z0rats.github.io/corvid/features/instagram-search/',
    );
  });
});

describe('InstagramSearch — successful lookup', () => {
  it('renders the profile overview card with the returned metadata', async () => {
    instagramSearchApi.lookupProfile.mockResolvedValue({
      username: 'someuser',
      full_name: 'Some User',
      biography: 'bio text',
      biography_hashtags: [],
      biography_mentions: [],
      external_url: null,
      followers: 1234,
      followees: 56,
      mediacount: 7,
      igtvcount: 0,
      is_private: false,
      is_verified: true,
      is_business_account: false,
      business_category_name: null,
      has_public_story: false,
      has_highlight_reels: false,
      profile_pic_url: 'https://example.com/pic.jpg',
      mode: 'anonymous',
      timestamp: '2026-01-01T00:00:00Z',
    });

    renderInstagramSearch();
    await userEvent.type(screen.getByLabelText(/instagram username/i), 'someuser');
    await userEvent.click(screen.getByRole('button', { name: /look up/i }));

    await waitFor(() => expect(screen.getByText('Some User')).toBeInTheDocument());
    expect(screen.getByText(/@someuser/)).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
    expect(instagramSearchApi.lookupProfile).toHaveBeenCalledWith('someuser');
  });
});

describe('InstagramSearch — error states', () => {
  it('renders the service error message', async () => {
    instagramSearchApi.lookupProfile.mockRejectedValue({
      response: { data: { detail: "Instagram profile 'ghost' does not exist" } },
    });

    renderInstagramSearch();
    await userEvent.type(screen.getByLabelText(/instagram username/i), 'ghost');
    await userEvent.click(screen.getByRole('button', { name: /look up/i }));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/does not exist/i));
  });
});

describe('InstagramSearch — cross-feature prefill (command palette pivot)', () => {
  it('prefills the username field from ?q= and auto-runs the lookup', async () => {
    instagramSearchApi.lookupProfile.mockResolvedValue({ username: 'john_doe', mode: 'anonymous' });

    renderInstagramSearch(['/instagram-search?q=john_doe']);

    expect(screen.getByLabelText(/instagram username/i).value).toBe('john_doe');
    await waitFor(() => expect(instagramSearchApi.lookupProfile).toHaveBeenCalledWith('john_doe'));
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderInstagramSearch();

    expect(screen.getByLabelText(/instagram username/i).value).toBe('');
    expect(instagramSearchApi.lookupProfile).not.toHaveBeenCalled();
  });
});
