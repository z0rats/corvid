import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../../core/config/theme';
import LastAnalysisResults from './LastAnalysisResults';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('LastAnalysisResults', () => {
  it('renders a table row for each engine result', () => {
    renderWithTheme(
      <LastAnalysisResults
        result={{
          data: {
            attributes: {
              last_analysis_results: {
                'Engine A': { category: 'malicious', result: 'Trojan.Generic', method: 'blacklist' },
                'Engine B': { category: 'harmless', result: null, method: 'blacklist' },
              },
            },
          },
        }}
      />
    );

    expect(screen.getByText('Last analysis results')).toBeInTheDocument();
    expect(screen.getByText('Engine A')).toBeInTheDocument();
    expect(screen.getByText('malicious')).toBeInTheDocument();
    expect(screen.getByText('Trojan.Generic')).toBeInTheDocument();
    expect(screen.getByText('Engine B')).toBeInTheDocument();
    expect(screen.getByText('harmless')).toBeInTheDocument();
  });
});
