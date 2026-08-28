import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import AbuseIpdbDetails from './AbuseIpdbDetails';

// The confidence-score pie chart reads theme.palette.chart, a custom token this
// app's theme adds on top of MUI's defaults - render through the real theme
// rather than MUI's bare default (which lacks it).
function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('AbuseIpdbDetails', () => {
  it('shows the unavailable message when result is missing', () => {
    renderWithTheme(<AbuseIpdbDetails result={null} ioc="1.2.3.4" />);
    expect(
      screen.getByText('AbuseIPDB details are unavailable or still loading.')
    ).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    renderWithTheme(
      <AbuseIpdbDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />
    );
    expect(screen.getByText('Error fetching AbuseIPDB details: timeout')).toBeInTheDocument();
  });

  it('shows the unavailable message when result.data is missing', () => {
    renderWithTheme(<AbuseIpdbDetails result={{}} ioc="1.2.3.4" />);
    expect(
      screen.getByText('AbuseIPDB details are unavailable or still loading.')
    ).toBeInTheDocument();
  });

  it('renders the confidence score and stats', () => {
    renderWithTheme(
      <AbuseIpdbDetails
        result={{
          data: {
            ipAddress: '1.2.3.4',
            abuseConfidenceScore: 87,
            totalReports: 42,
            numDistinctUsers: 10,
            isWhitelisted: false,
            countryName: 'United States',
            countryCode: 'US',
          },
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Confidence Score & Stats')).toBeInTheDocument();
    expect(screen.getByText('87')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });
});
