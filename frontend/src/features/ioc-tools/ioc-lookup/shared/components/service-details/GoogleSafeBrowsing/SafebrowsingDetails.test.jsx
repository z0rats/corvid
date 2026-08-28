import React from 'react';
import { render, screen } from '@testing-library/react';
import SafebrowsingDetails from './SafebrowsingDetails';

describe('SafebrowsingDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<SafebrowsingDetails result={null} ioc="evil.example" />);
    expect(screen.getByText('Loading Google Safe Browse details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<SafebrowsingDetails result={{ error: true, message: 'timeout' }} ioc="evil.example" />);
    expect(
      screen.getByText('Error fetching Google Safe Browse details: timeout')
    ).toBeInTheDocument();
  });

  it('shows a clean result when there are no matches', () => {
    render(<SafebrowsingDetails result={{ matches: [] }} ioc="evil.example" />);
    expect(
      screen.getByText('No threats found by Google Safe Browse. The IOC appears to be safe according to this check.')
    ).toBeInTheDocument();
  });

  it('lists each reported threat match', () => {
    render(
      <SafebrowsingDetails
        result={{
          matches: [
            {
              threatType: 'SOCIAL_ENGINEERING',
              platformType: 'ANY_PLATFORM',
              threatEntryType: 'URL',
              threat: { url: 'http://evil.example/phish' },
              cacheDuration: '300s',
            },
          ],
        }}
        ioc="evil.example"
      />
    );

    expect(
      screen.getByText('The following threats were reported for the queried IOC:')
    ).toBeInTheDocument();
    expect(screen.getByText('Match 1: SOCIAL_ENGINEERING')).toBeInTheDocument();
    expect(screen.getByText('ANY_PLATFORM')).toBeInTheDocument();
    expect(screen.getByText('http://evil.example/phish')).toBeInTheDocument();
    expect(screen.getByText('300s')).toBeInTheDocument();
  });

  it('falls back to N/A for missing optional match fields', () => {
    render(
      <SafebrowsingDetails
        result={{ matches: [{ threatType: 'MALWARE' }] }}
        ioc="evil.example"
      />
    );

    expect(screen.getAllByText('N/A').length).toBeGreaterThanOrEqual(2);
  });
});
