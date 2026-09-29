import { render, screen } from '@testing-library/react';
import CloseFriendsTable from './CloseFriendsTable';

const FRIENDS = [
  {
    steamid64: '1',
    persona_name: 'Alice',
    avatar_url: null,
    mutual_count: 5,
    friend_since: 1063324800,
    location: { country_code: 'US', country: 'United States' },
    vac_banned: true,
    game_banned: false,
    friends_private: false,
  },
  {
    steamid64: '2',
    persona_name: 'Bob',
    avatar_url: null,
    mutual_count: 0,
    friend_since: null,
    location: null,
    vac_banned: false,
    game_banned: false,
    friends_private: true,
  },
];

describe('CloseFriendsTable', () => {
  it('shows an empty state when there are no close friends', () => {
    render(<CloseFriendsTable closeFriends={[]} />);
    expect(screen.getByText(/no connected friends found/i)).toBeInTheDocument();
  });

  it('renders each friend as a linked row with their mutual count', () => {
    render(<CloseFriendsTable closeFriends={FRIENDS} />);

    expect(screen.getByRole('link', { name: 'Alice' })).toHaveAttribute(
      'href',
      'https://steamcommunity.com/profiles/1',
    );
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('United States')).toBeInTheDocument();
  });

  it('shows a VAC ban chip for a banned friend', () => {
    render(<CloseFriendsTable closeFriends={FRIENDS} />);
    expect(screen.getByText('VAC')).toBeInTheDocument();
  });

  it('shows a friends-private chip when the friends list could not be analyzed', () => {
    render(<CloseFriendsTable closeFriends={FRIENDS} />);
    expect(screen.getByText(/friends list private/i)).toBeInTheDocument();
  });

  it('falls back to a dash for missing friend-since and location', () => {
    render(<CloseFriendsTable closeFriends={[FRIENDS[1]]} />);
    const dashes = screen.getAllByText('-');
    expect(dashes.length).toBeGreaterThanOrEqual(2);
  });
});
