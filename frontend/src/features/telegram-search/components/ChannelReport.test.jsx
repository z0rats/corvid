import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import ChannelReport from './ChannelReport';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function renderReport(result, props = {}) {
  return render(
    <MemoryRouter initialEntries={['/telegram-search/new']}>
      <Routes>
        <Route path="*" element={<><ChannelReport result={result} {...props} /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

const PROFILE = {
  username: 'tginfo',
  url: 'https://t.me/tginfo',
  title: 'Telegram Info',
  kind: 'channel',
  member_count: 83253,
  online_count: null,
  description: 'News about Telegram',
  verified: true,
  photo_url: 'https://cdn4.telesco.pe/file/x.jpg',
  created_at: '2015-10-04T18:24:36+00:00',
  preview_available: true,
  media_counters: { photos: 1380 },
};

const RESULT = {
  profile: PROFILE,
  metrics: {
    posts_sampled: 2,
    first_sampled_at: '2026-10-01T00:00:00+00:00',
    last_post_at: '2026-10-02T00:00:00+00:00',
    posts_per_day: 2,
    avg_views: 32100,
    median_views: 32100,
    max_views: 43000,
    views_to_members: 0.3856,
    forwarded_count: 1,
    forwarded_ratio: 0.5,
    media_ratio: 0,
    top_forward_sources: [
      { name: 'Подборки каналов', username: 'podborki', count: 1 },
      { name: null, username: null, count: 1 },
    ],
    top_mentions: [{ username: 'betainfo', count: 2 }],
  },
  top_posts: [{ id: 102, url: 'https://t.me/tginfo/102', views: 43000, text: 'Top post', has_media: false, link_count: 0 }],
  posts: [
    { id: 102, url: 'https://t.me/tginfo/102', views: 43000, text: 'Top post', has_media: false, link_count: 0 },
    {
      id: 101,
      url: 'https://t.me/tginfo/101',
      views: 21200,
      text: 'A repost',
      has_media: false,
      link_count: 0,
      forwarded_from: { name: 'Подборки каналов', username: 'podborki', count: 1 },
    },
  ],
  indicators: { domains: ['evil-c2.net'], ips: ['203.0.113.7'], md5: ['d41d8cd98f00b204e9800998ecf8427e'] },
};

describe('ChannelReport', () => {
  it('renders nothing without a profile', () => {
    const { container } = renderReport(null);
    expect(container.querySelector('h2')).toBeNull();
  });

  it('shows the channel card, activity and both post tables', () => {
    renderReport(RESULT);

    expect(screen.getByRole('heading', { name: 'Telegram Info' })).toBeInTheDocument();
    expect(screen.getByText('83,253')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /@tginfo/ })).toHaveAttribute('href', 'https://t.me/tginfo');
    expect(screen.getByText('39%')).toBeInTheDocument(); // views / subscribers
    expect(screen.getByText('50%')).toBeInTheDocument(); // forwarded
    expect(screen.getByRole('heading', { name: /most viewed posts/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /sampled posts \(2\)/i })).toBeInTheDocument();
    expect(screen.getByText(/forwarded from подборки каналов/i)).toBeInTheDocument();
  });

  it('links the photo instead of embedding it', () => {
    const { container } = renderReport(RESULT);

    expect(container.querySelector('img')).toBeNull();
    expect(screen.getByRole('link', { name: 'Open' })).toHaveAttribute('href', PROFILE.photo_url);
  });

  it('a linked forward source opens a scan of that channel', () => {
    renderReport(RESULT);

    fireEvent.click(screen.getByText('Подборки каналов (1) @podborki'));

    expect(screen.getByTestId('location')).toHaveTextContent('/telegram-search/new?q=podborki');
  });

  it('a hidden sender is shown but not clickable', () => {
    renderReport(RESULT);

    const hidden = screen.getByText('Hidden sender (1)');
    fireEvent.click(hidden);
    expect(screen.getByTestId('location')).toHaveTextContent('/telegram-search/new');
    expect(screen.getByTestId('location')).not.toHaveTextContent('?q=');
  });

  it('channel chips do nothing while another scan runs', () => {
    renderReport(RESULT, { disabled: true });

    fireEvent.click(screen.getByText('@betainfo (2)'));

    expect(screen.getByTestId('location')).not.toHaveTextContent('?q=');
  });

  it('a mention opens a scan of the mentioned channel', () => {
    renderReport(RESULT);

    fireEvent.click(screen.getByText('@betainfo (2)'));

    expect(screen.getByTestId('location')).toHaveTextContent('/telegram-search/new?q=betainfo');
  });

  it.each([
    ['evil-c2.net', '/ioc-tools/domain-finder?q=evil-c2.net'],
    ['203.0.113.7', '/ioc-tools/lookup?q=203.0.113.7'],
    ['d41d8cd98f00b204e9800998ecf8427e', '/ioc-tools/bulk?q=d41d8cd98f00b204e9800998ecf8427e'],
  ])('indicator %s pivots to %s', (value, target) => {
    renderReport(RESULT);

    fireEvent.click(screen.getByText(value));

    expect(screen.getByTestId('location')).toHaveTextContent(target);
  });

  it('a channel without a web preview shows only the card and an explanation', () => {
    renderReport({
      profile: { ...PROFILE, preview_available: false, media_counters: {} },
      metrics: null,
      top_posts: [],
      posts: [],
      indicators: {},
    });

    expect(screen.getByText(/web preview turned off/i)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /activity/i })).toBeNull();
    expect(screen.queryByRole('heading', { name: /sampled posts/i })).toBeNull();
  });

  it('a group gets the group-specific explanation and a members label', () => {
    renderReport({
      profile: { ...PROFILE, kind: 'group', online_count: 4780, preview_available: false },
      metrics: null,
      posts: [],
      top_posts: [],
      indicators: {},
    });

    expect(screen.getByText(/groups have no public web preview/i)).toBeInTheDocument();
    expect(screen.getByText('Members')).toBeInTheDocument();
    expect(screen.getByText('4,780')).toBeInTheDocument();
  });
});
