import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import FfraudIpDetails from './FfraudIpDetails';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('FfraudIpDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderWithTheme(<FfraudIpDetails result={null} ioc="1.2.3.4" />);
    expect(
      screen.getByText('FFraud details are unavailable or the data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    renderWithTheme(<FfraudIpDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching FFraud details: timeout')).toBeInTheDocument();
  });

  it('renders the fraud score, reason, threat tags, and indicators', () => {
    renderWithTheme(
      <FfraudIpDetails
        result={{
          fraud_score: 90,
          reason: 'Known Tor exit node',
          threat_tags: ['tor', 'anonymizer'],
          geo: { country: 'US', city: 'Ashburn' },
          ISP: 'Example ISP',
          organization: 'Example Org',
          ASN: 'AS1234',
          proxy: true,
          vpn: false,
          vpn_provider: 'ExampleVPN',
          tor: true,
          relay: false,
          hosting: false,
          cloud_provider: null,
          mobile: false,
          recent_abuse: true,
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Fraud Score & Indicators')).toBeInTheDocument();
    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getByText('Known Tor exit node')).toBeInTheDocument();
    expect(screen.getByText('tor')).toBeInTheDocument();
    expect(screen.getByText('anonymizer')).toBeInTheDocument();
    expect(screen.getByText('ExampleVPN')).toBeInTheDocument();
  });

  it('falls back to N/A for a missing fraud score', () => {
    renderWithTheme(<FfraudIpDetails result={{}} ioc="1.2.3.4" />);
    expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
  });
});
