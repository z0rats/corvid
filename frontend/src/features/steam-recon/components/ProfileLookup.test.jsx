import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProfileLookup from './ProfileLookup';
import { useSteamProfile } from '../hooks/useSteamProfile';
import { renderFeatureRoute } from '../../../core/testUtils/renderFeatureRoute';

vi.mock('../hooks/useSteamProfile');

const RESULT = {
  profile: {
    steamid64: '76561197960435530',
    persona_name: 'Robin',
    real_name: 'Robin Walker',
    profile_url: 'https://steamcommunity.com/id/robinwalker/',
    avatar_url: null,
    visibility: 'public',
    created_at: 1063324800,
    last_logoff: null,
    location: { country_code: 'US', country: 'United States', state: 'Washington', city: 'Bellevue' },
    level: 12,
    game_count: null,
    bans: {
      community_banned: false,
      vac_banned: true,
      number_of_vac_bans: 2,
      days_since_last_ban: 30,
      number_of_game_bans: 0,
      economy_ban: 'none',
    },
  },
  quick_links: [{ id: 'steamid_io', label: 'steamid.io', url: 'https://steamid.io/lookup/1' }],
};

function mockHook(overrides = {}) {
  const lookupProfile = vi.fn();
  useSteamProfile.mockReturnValue({
    target: '',
    setTarget: vi.fn(),
    result: null,
    loading: false,
    error: null,
    errorCode: null,
    lookupProfile,
    ...overrides,
  });
  return lookupProfile;
}

function renderPage() {
  return renderFeatureRoute(ProfileLookup, 'steam-recon/profile', ['/steam-recon/profile']);
}

afterEach(() => vi.clearAllMocks());

describe('ProfileLookup', () => {
  it('shows the welcome screen before any lookup', () => {
    mockHook();
    renderPage();

    expect(screen.getByRole('heading', { name: 'Steam Recon' })).toBeInTheDocument();
  });

  it('disables the lookup button while the field is empty', () => {
    mockHook({ target: '   ' });
    renderPage();

    expect(screen.getByRole('button', { name: /look up/i })).toBeDisabled();
  });

  it('runs the lookup on click and on Enter', async () => {
    const lookupProfile = mockHook({ target: 'robinwalker' });
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /look up/i }));
    await userEvent.type(screen.getByLabelText(/steam id, profile url/i), '{Enter}');

    expect(lookupProfile).toHaveBeenCalledTimes(2);
  });

  it('renders the profile, resolved location, bans and quick links', () => {
    mockHook({ result: RESULT });
    renderPage();

    expect(screen.getByText('Robin')).toBeInTheDocument();
    expect(screen.getByText('Bellevue, Washington, United States')).toBeInTheDocument();
    expect(screen.getByText('VAC ban (2)')).toBeInTheDocument();
    expect(screen.getByText(/last ban 30 days ago/i)).toBeInTheDocument();
    expect(screen.getByText('Private')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'steamid.io' })).toHaveAttribute(
      'href',
      'https://steamid.io/lookup/1',
    );
  });

  it('says so when no bans are on record', () => {
    const clean = { ...RESULT, profile: { ...RESULT.profile, bans: { ...RESULT.profile.bans, vac_banned: false, number_of_vac_bans: 0 } } };
    mockHook({ result: clean });
    renderPage();

    expect(screen.getByText('No bans on record')).toBeInTheDocument();
  });

  it('shows an API error as an alert', () => {
    mockHook({ error: 'No Steam profile uses the vanity name', errorCode: 'STEAM_PROFILE_NOT_FOUND' });
    renderPage();

    expect(screen.getByRole('alert')).toHaveTextContent('No Steam profile uses the vanity name');
  });

  it('points to Settings > API Keys when no key is configured', () => {
    mockHook({ error: 'A Steam Web API key is required.', errorCode: 'STEAM_NOT_CONFIGURED' });
    renderPage();

    expect(screen.getByRole('link', { name: /add api key/i })).toHaveAttribute('href', '/settings/apikeys');
    expect(screen.queryByText('A Steam Web API key is required.')).not.toBeInTheDocument();
  });
});
