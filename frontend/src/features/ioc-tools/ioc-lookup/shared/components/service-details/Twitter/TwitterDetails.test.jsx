import React from 'react';
import { render, screen } from '@testing-library/react';
import TwitterDetails from './TwitterDetails';

describe('TwitterDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<TwitterDetails result={null} ioc="evil.example" />);
    expect(screen.getByText('Loading Twitter mentions...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<TwitterDetails result={{ error: true, message: 'timeout' }} ioc="evil.example" />);
    expect(screen.getByText('Error fetching Twitter mentions: timeout')).toBeInTheDocument();
  });

  it('shows a no-tweets message when meta.result_count is zero', () => {
    render(<TwitterDetails result={{ meta: { result_count: 0 }, data: [] }} ioc="evil.example" />);
    expect(screen.getByText('No recent tweets found mentioning "evil.example".')).toBeInTheDocument();
  });

  it('renders tweets from the {meta, data} response shape', () => {
    render(
      <TwitterDetails
        result={{
          meta: { result_count: 1 },
          data: [
            {
              id: '123',
              author_id: '456',
              author: 'Alice',
              user: { username: 'alice_sec' },
              created_at: '2024-01-15T12:00:00Z',
              text: 'Watch out for evil.example',
              entities: { hashtags: [{ tag: 'infosec' }] },
            },
          ],
        }}
        ioc="evil.example"
      />
    );

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('@alice_sec')).toBeInTheDocument();
    expect(screen.getByText('Watch out for evil.example')).toBeInTheDocument();
    expect(screen.getByText('#infosec')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /view on twitter/i });
    expect(link).toHaveAttribute('href', 'https://twitter.com/alice_sec/status/123');
  });

  it('renders tweets from the [{count}, ...tweets] response shape', () => {
    render(
      <TwitterDetails
        result={[{ count: 1 }, { id: '1', text: 'tweet body' }]}
        ioc="evil.example"
      />
    );

    expect(screen.getByText('tweet body')).toBeInTheDocument();
    expect(screen.getByText('Unknown Author')).toBeInTheDocument();
  });
});
