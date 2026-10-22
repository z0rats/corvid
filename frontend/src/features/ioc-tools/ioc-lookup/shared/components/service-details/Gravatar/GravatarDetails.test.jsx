import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import GravatarDetails from './GravatarDetails';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

const renderDetails = (result) =>
  render(
    <MemoryRouter initialEntries={['/ioc-tools/lookup']}>
      <Routes>
        <Route path="*" element={<><GravatarDetails result={result} /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );

const PROFILE = {
  found: true,
  display_name: 'Beau Lebens',
  profile_url: 'https://gravatar.com/beau',
  avatar_url: 'https://0.gravatar.com/avatar/abc',
  location: 'Golden, CO',
  description: 'Builds the web.',
  job_title: 'Lead',
  company: 'Automattic',
  verified_accounts: [
    { service: 'github', label: 'GitHub', url: 'https://github.com/beaulebens', username: 'beaulebens' },
    { service: 'twitter', label: 'X', url: 'https://x.com/beaulebens', username: 'beaulebens' },
  ],
};

describe('GravatarDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderDetails(null);
    expect(screen.getByText('Gravatar details are unavailable or still loading.')).toBeInTheDocument();
  });

  it('shows "no public profile" when there is none', () => {
    renderDetails({ found: false, verified_accounts: [] });
    expect(screen.getByText('No public Gravatar profile')).toBeInTheDocument();
  });

  it('shows the profile and links the avatar without loading it', () => {
    const { container } = renderDetails(PROFILE);
    expect(screen.getByText('Beau Lebens')).toBeInTheDocument();
    expect(screen.getByText('Automattic')).toBeInTheDocument();
    expect(screen.getByText('Verified linked accounts (2)')).toBeInTheDocument();
    expect(screen.getByText('Open avatar image').closest('a')).toHaveAttribute('href', PROFILE.avatar_url);
    expect(container.querySelector('img')).toBeNull();
  });

  it('says there is no custom avatar instead of linking the default image', () => {
    renderDetails({ ...PROFILE, has_avatar: false });
    expect(screen.getByText("None (Gravatar's default image)")).toBeInTheDocument();
    expect(screen.queryByText('Open avatar image')).not.toBeInTheDocument();
  });

  it('offers no username search for an account without a username', () => {
    renderDetails({
      ...PROFILE,
      verified_accounts: [{ service: 'facebook', label: 'Facebook', url: 'https://facebook.com/profile.php?id=1', username: null }],
    });
    expect(screen.queryByText('Username search')).not.toBeInTheDocument();
    expect(screen.getByText('https://facebook.com/profile.php?id=1').closest('a')).toHaveAttribute('href', 'https://facebook.com/profile.php?id=1');
  });

  it('pivots a GitHub account into git recon', () => {
    renderDetails(PROFILE);
    fireEvent.click(screen.getByText('Git recon'));
    expect(screen.getByTestId('location')).toHaveTextContent('/git-recon?q=beaulebens');
  });

  it('offers a username search for every account with a username', () => {
    renderDetails(PROFILE);
    const searches = screen.getAllByText('Username search');
    expect(searches).toHaveLength(2);
    fireEvent.click(searches[1]);
    expect(screen.getByTestId('location')).toHaveTextContent('/username-search?q=beaulebens');
  });
});
