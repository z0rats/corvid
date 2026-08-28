import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import VirustotalDetails from './VirustotalDetails';

// This covers the orchestrator's own branching (loading/not-found/error/no-attributes,
// and which of the 11 optional sub-sections get mounted) - each sub-component under
// ./Virustotal/ has its own rendering logic and deserves its own dedicated test.
//
// AnalysisStatistics (always mounted once attributes exist) reads theme.palette.chart,
// a custom token this app's theme adds on top of MUI's defaults - rendering without the
// real theme throws, so every render here goes through the app's actual ThemeProvider
// instead of MUI's bare default theme.
function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('VirustotalDetails', () => {
  it('shows a loading message when result is missing', () => {
    renderWithTheme(<VirustotalDetails result={null} ioc="evil.example" />);
    expect(screen.getByText('Loading VirusTotal details...')).toBeInTheDocument();
  });

  it('shows a not-found message when the IOC was not found', () => {
    renderWithTheme(<VirustotalDetails result={{ notFound: true }} ioc="evil.example" />);
    expect(screen.getByText('IOC "evil.example" was not found on VirusTotal')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    renderWithTheme(<VirustotalDetails result={{ error: 'rate limited' }} ioc="evil.example" />);
    expect(screen.getByText('Error fetching VirusTotal details: rate limited')).toBeInTheDocument();
  });

  it('shows a no-attributes message when the response has no attributes', () => {
    renderWithTheme(<VirustotalDetails result={{ data: {} }} ioc="evil.example" />);
    expect(
      screen.getByText('No detailed VirusTotal attributes found for "evil.example". The API response might be incomplete or the IOC was not found.')
    ).toBeInTheDocument();
  });

  it('renders Details and AnalysisStatistics for a minimal valid response', () => {
    renderWithTheme(
      <VirustotalDetails
        result={{ data: { attributes: { last_analysis_stats: { malicious: 2, harmless: 60 } } } }}
        ioc="evil.example"
      />
    );

    expect(screen.getByText('General Information')).toBeInTheDocument();
    expect(screen.getByText('Detected as malicious by 2 engine(s)')).toBeInTheDocument();
    expect(screen.getByText('Analysis Statistics')).toBeInTheDocument();
    expect(screen.queryByText('Tags')).not.toBeInTheDocument();
  });

  it('mounts the Tags section only when tags are present', () => {
    renderWithTheme(
      <VirustotalDetails
        result={{
          data: {
            attributes: {
              last_analysis_stats: { malicious: 0 },
              tags: ['peexe', 'signed'],
            },
          },
        }}
        ioc="evil.example"
      />
    );

    expect(screen.getByText('Tags')).toBeInTheDocument();
    expect(screen.getByText('peexe')).toBeInTheDocument();
    expect(screen.getByText('signed')).toBeInTheDocument();
  });
});
