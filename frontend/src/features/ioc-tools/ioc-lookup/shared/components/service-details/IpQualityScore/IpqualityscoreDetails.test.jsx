import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import IpqualityscoreDetails from './IpqualityscoreDetails';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('IpqualityscoreDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderWithTheme(<IpqualityscoreDetails result={null} ioc="1.2.3.4" />);
    expect(
      screen.getByText('IPQualityScore details are unavailable or data is incomplete.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    renderWithTheme(
      <IpqualityscoreDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />
    );
    expect(screen.getByText('Error fetching IPQualityScore details: timeout')).toBeInTheDocument();
  });

  it('renders the fraud score and indicator list', () => {
    renderWithTheme(
      <IpqualityscoreDetails
        result={{
          fraud_score: 75,
          country_code: 'US',
          city: 'Ashburn',
          ISP: 'Amazon',
          organization: 'AWS',
          proxy: true,
          VPN: true,
          active_VPN: true,
          tor: false,
          recent_abuse: true,
          bot_status: false,
          mobile: false,
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Fraud Score & Indicators')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
    expect(screen.getByText('Yes (Active)')).toBeInTheDocument();
    expect(screen.getByText('Recent Abuse')).toBeInTheDocument();
  });

  it('falls back to N/A for a missing fraud score', () => {
    renderWithTheme(<IpqualityscoreDetails result={{}} ioc="1.2.3.4" />);
    expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
  });
});
