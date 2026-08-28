import React from 'react';
import { render, screen } from '@testing-library/react';
import LibraryOfLeaksDetails from './LibraryOfLeaksDetails';

describe('LibraryOfLeaksDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<LibraryOfLeaksDetails result={null} />);
    expect(
      screen.getByText('Library of Leaks details are unavailable or still loading.')
    ).toBeInTheDocument();
  });

  it('shows a clean-result card when there are no hits', () => {
    render(<LibraryOfLeaksDetails result={{ total_hits: 0, collections: [] }} />);
    expect(screen.getByText('No breach/leak mentions found')).toBeInTheDocument();
  });

  it('lists collections and the source link when there are hits', () => {
    render(
      <LibraryOfLeaksDetails
        result={{
          total_hits: 5,
          collections: [
            { url: 'https://loll.example/c1', label: 'Leak Collection A', category: 'breach', count: 3 },
            { url: 'https://loll.example/c2', label: 'Leak Collection B', category: 'forum', count: 2 },
          ],
          search_url: 'https://libraryofleaks.example/search?q=evil.example',
        }}
      />
    );

    expect(screen.getByText('5 mention(s) found across 2 collection(s)')).toBeInTheDocument();
    expect(screen.getByText('Leak Collection A')).toBeInTheDocument();
    expect(screen.getByText('Leak Collection B')).toBeInTheDocument();
    expect(screen.getByText('breach')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /open in library of leaks/i });
    expect(link).toHaveAttribute('href', 'https://libraryofleaks.example/search?q=evil.example');
  });

  it('omits the source link when search_url is unavailable', () => {
    render(
      <LibraryOfLeaksDetails
        result={{
          total_hits: 1,
          collections: [{ url: 'https://loll.example/c1', label: 'Leak', category: 'breach', count: 1 }],
        }}
      />
    );
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
