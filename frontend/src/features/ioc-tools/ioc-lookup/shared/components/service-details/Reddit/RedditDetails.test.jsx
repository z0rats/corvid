import React from 'react';
import { render, screen } from '@testing-library/react';
import RedditDetails from './RedditDetails';

describe('RedditDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<RedditDetails result={null} ioc="alice" />);
    expect(screen.getByText('Loading Reddit mentions...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<RedditDetails result={{ error: true, message: 'timeout' }} ioc="alice" />);
    expect(screen.getByText('Error fetching Reddit mentions: timeout')).toBeInTheDocument();
  });

  it('shows a no-mentions message when there are no posts', () => {
    render(<RedditDetails result={{ posts: [] }} ioc="alice" />);
    expect(screen.getByText('No Reddit mentions found for "alice".')).toBeInTheDocument();
  });

  it('renders each post with its metadata', () => {
    render(
      <RedditDetails
        result={{
          posts: [
            {
              id: 'p1',
              title: 'Suspicious activity report',
              subreddit: 'r/netsec',
              author: 'alice',
              score: 42,
              num_comments: 7,
              created_utc: 1700000000,
              url: 'https://reddit.com/r/netsec/p1',
              message: 'short body',
            },
          ],
        }}
        ioc="alice"
      />
    );

    expect(screen.getByText('Reddit Mentions (1)')).toBeInTheDocument();
    expect(screen.getByText('Suspicious activity report')).toBeInTheDocument();
    expect(screen.getByText('r/netsec')).toBeInTheDocument();
    expect(screen.getByText('alice')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('short body')).toBeInTheDocument();
  });

  it('truncates a long message body behind a Read more toggle', () => {
    const longMessage = 'x'.repeat(250);
    render(
      <RedditDetails
        result={{ posts: [{ id: 'p1', message: longMessage, title: 't' }] }}
        ioc="alice"
      />
    );

    expect(screen.getByText(/x{200}\.\.\./)).toBeInTheDocument();
    expect(screen.getByText('Read more')).toBeInTheDocument();
  });

  it('paginates when there are more than 5 posts', () => {
    const posts = Array.from({ length: 7 }, (_, i) => ({ id: `p${i}`, title: `Post ${i}` }));
    render(<RedditDetails result={{ posts }} ioc="alice" />);

    expect(screen.getByText('Post 0')).toBeInTheDocument();
    expect(screen.queryByText('Post 5')).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('falls back to a placeholder title when the post has none', () => {
    render(<RedditDetails result={{ posts: [{ id: 'p1' }] }} ioc="alice" />);
    expect(screen.getByText('No Title')).toBeInTheDocument();
  });
});
