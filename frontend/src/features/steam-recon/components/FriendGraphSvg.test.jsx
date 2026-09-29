import { render, screen } from '@testing-library/react';
import FriendGraphSvg from './FriendGraphSvg';

const FRIENDS = [
  { steamid64: '1', persona_name: 'Alice', mutual_count: 5, vac_banned: false, game_banned: false },
  { steamid64: '2', persona_name: 'Bob', mutual_count: 2, vac_banned: true, game_banned: false },
];

describe('FriendGraphSvg', () => {
  it('shows an empty state with no close friends', () => {
    render(<FriendGraphSvg closeFriends={[]} targetLabel="Target" />);
    expect(screen.getByText(/no connected friends to draw/i)).toBeInTheDocument();
  });

  it('draws the target and one link per friend', () => {
    const { container } = render(<FriendGraphSvg closeFriends={FRIENDS} targetLabel="Target" />);

    expect(container.querySelectorAll('svg line')).toHaveLength(FRIENDS.length);
    // one circle for the target, one per friend
    expect(container.querySelectorAll('svg circle')).toHaveLength(FRIENDS.length + 1);
  });

  it('links each friend node to their Steam profile', () => {
    const { container } = render(<FriendGraphSvg closeFriends={FRIENDS} targetLabel="Target" />);

    const hrefs = [...container.querySelectorAll('svg a')].map((a) => a.getAttribute('href'));
    expect(hrefs).toEqual(
      expect.arrayContaining([
        'https://steamcommunity.com/profiles/1',
        'https://steamcommunity.com/profiles/2',
      ]),
    );
  });

  it('labels every friend node with their persona name, not just the target', () => {
    render(<FriendGraphSvg closeFriends={FRIENDS} targetLabel="Target" />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });
});
