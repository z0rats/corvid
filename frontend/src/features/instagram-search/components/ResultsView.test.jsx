import { render, screen } from '@testing-library/react';
import ResultsView from './ResultsView';

describe('ResultsView', () => {
  it('renders nothing when there is no result yet', () => {
    const { container } = render(<ResultsView result={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the empty state when items is empty', () => {
    render(<ResultsView result={{ scan_type: 'posts', items: [], item_count: 0, truncated: false }} />);
    expect(screen.getByText(/no items collected/i)).toBeInTheDocument();
  });

  it('renders a followers/followees table with a link to each profile', () => {
    render(<ResultsView result={{
      scan_type: 'followers',
      items: [{ username: 'someuser', full_name: 'Some User' }],
      item_count: 1,
      total_count: 1,
      truncated: false,
    }} />);

    expect(screen.getByText('Some User')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /someuser/i });
    expect(link).toHaveAttribute('href', 'https://www.instagram.com/someuser/');
  });

  it('renders a posts table with a permalink and caption', () => {
    render(<ResultsView result={{
      scan_type: 'posts',
      items: [{
        shortcode: 'ABC123',
        permalink: 'https://www.instagram.com/p/ABC123/',
        date_utc: '2026-01-01T00:00:00',
        is_video: false,
        likes: 42,
        comments: 3,
        caption: 'hello world',
      }],
      item_count: 1,
      total_count: 1,
      truncated: false,
    }} />);

    const link = screen.getByRole('link', { name: /ABC123/i });
    expect(link).toHaveAttribute('href', 'https://www.instagram.com/p/ABC123/');
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('hello world')).toBeInTheDocument();
  });

  it('shows the truncated notice when the scan was cut short', () => {
    render(<ResultsView result={{
      scan_type: 'posts',
      items: [{ shortcode: 'a', permalink: 'x', likes: 1, comments: 1, caption: '' }],
      item_count: 1,
      total_count: 500,
      truncated: true,
    }} />);

    expect(screen.getByText(/stopped before the full list was exhausted/i)).toBeInTheDocument();
  });

  it('does not show the truncated notice for a fully-exhausted scan', () => {
    render(<ResultsView result={{
      scan_type: 'posts',
      items: [{ shortcode: 'a', permalink: 'x', likes: 1, comments: 1, caption: '' }],
      item_count: 1,
      total_count: 1,
      truncated: false,
    }} />);

    expect(screen.queryByText(/stopped before the full list was exhausted/i)).not.toBeInTheDocument();
  });
});
