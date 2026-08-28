import React from 'react';
import { render, screen } from '@testing-library/react';
import OpenPhishDetails from './OpenPhishDetails';

describe('OpenPhishDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    render(<OpenPhishDetails result={null} />);
    expect(screen.getByText('OpenPhish details are unavailable.')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<OpenPhishDetails result={{ error: true, message: 'timeout' }} />);
    expect(screen.getByText('Error fetching OpenPhish details: timeout')).toBeInTheDocument();
  });

  it('shows the not-listed message when the IOC is not in the feed', () => {
    render(<OpenPhishDetails result={{ listed: false }} />);
    expect(
      screen.getByText("Not listed in OpenPhish's community phishing feed.")
    ).toBeInTheDocument();
  });

  it('lists matched URLs when the IOC is listed', () => {
    render(
      <OpenPhishDetails
        result={{ listed: true, matched_urls: ['http://evil.example/phish1', 'http://evil.example/phish2'] }}
      />
    );

    expect(screen.getByText('Listed in OpenPhish feed')).toBeInTheDocument();
    expect(screen.getByText('http://evil.example/phish1')).toBeInTheDocument();
    expect(screen.getByText('http://evil.example/phish2')).toBeInTheDocument();
  });

  it('renders an empty list without crashing when matched_urls is missing', () => {
    render(<OpenPhishDetails result={{ listed: true }} />);
    expect(screen.getByText('Listed in OpenPhish feed')).toBeInTheDocument();
  });
});
