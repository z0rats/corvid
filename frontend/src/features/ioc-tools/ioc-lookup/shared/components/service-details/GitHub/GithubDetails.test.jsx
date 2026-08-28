import React from 'react';
import { render, screen } from '@testing-library/react';
import GithubDetails from './GithubDetails';

describe('GithubDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<GithubDetails result={null} ioc="evil.example" />);
    expect(
      screen.getByText('GitHub details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<GithubDetails result={{ error: true, message: 'timeout' }} ioc="evil.example" />);
    expect(screen.getByText('Error fetching GitHub details: timeout')).toBeInTheDocument();
  });

  it('shows a no-mentions message when there are no items', () => {
    render(<GithubDetails result={{ items: [], total_count: 0 }} ioc="evil.example" />);
    expect(
      screen.getByText('No GitHub mentions found for "evil.example". (Total reported: 0)')
    ).toBeInTheDocument();
  });

  it('renders a table row for each matching item', () => {
    render(
      <GithubDetails
        result={{
          total_count: 1,
          items: [
            {
              name: 'config.yml',
              html_url: 'https://github.com/acme/repo/blob/main/config.yml',
              repository: {
                html_url: 'https://github.com/acme/repo',
                full_name: 'acme/repo',
              },
            },
          ],
        }}
        ioc="evil.example"
      />
    );

    expect(screen.getByText('GitHub Mentions (1 total)')).toBeInTheDocument();
    expect(screen.getByText('config.yml')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'https://github.com/acme/repo/blob/main/config.yml' })).toHaveAttribute(
      'href',
      'https://github.com/acme/repo/blob/main/config.yml'
    );
    expect(screen.getByRole('link', { name: 'acme/repo' })).toHaveAttribute(
      'href',
      'https://github.com/acme/repo'
    );
  });
});
