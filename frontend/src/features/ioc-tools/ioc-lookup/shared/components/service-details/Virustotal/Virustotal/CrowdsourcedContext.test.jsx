import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../../core/config/theme';
import CrowdsourcedContext from './CrowdsourcedContext';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

function makeResult(entries) {
  return { data: { attributes: { crowdsourced_context: entries } } };
}

describe('CrowdsourcedContext', () => {
  it('shows None when there are no entries', () => {
    renderWithTheme(<CrowdsourcedContext result={makeResult([])} />);
    expect(screen.getByText('None')).toBeInTheDocument();
  });

  it('renders each context entry', () => {
    renderWithTheme(
      <CrowdsourcedContext
        result={makeResult([
          {
            title: 'Known phishing kit',
            source: 'partner-feed',
            timestamp: 1700000000,
            detail: 'Matches a known phishing kit template',
            severity: 'high',
          },
        ])}
      />
    );

    expect(screen.getByText('Crowdsourced context')).toBeInTheDocument();
    expect(screen.getByText('Known phishing kit')).toBeInTheDocument();
    expect(screen.getByText('partner-feed')).toBeInTheDocument();
    expect(screen.getByText('Matches a known phishing kit template')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
  });
});
