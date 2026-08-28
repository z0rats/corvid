import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import CvssMetrics from './CvssMetrics';

// Renders Circle internally, which reads the app's custom theme.palette.chart token.
function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('CvssMetrics', () => {
  it('renders the vector string, scores, and severity', () => {
    renderWithTheme(
      <CvssMetrics
        metrics={{
          source: 'nvd@nist.gov',
          type: 'Primary',
          exploitabilityScore: 3.9,
          impactScore: 5.9,
          cvssData: {
            vectorString: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
            attackVector: 'NETWORK',
            attackComplexity: 'LOW',
            privilegesRequired: 'NONE',
            userInteraction: 'NONE',
            scope: 'UNCHANGED',
            confidentialityImpact: 'HIGH',
            integrityImpact: 'HIGH',
            availabilityImpact: 'HIGH',
            baseScore: 9.8,
            baseSeverity: 'CRITICAL',
          },
        }}
      />
    );

    expect(screen.getByText('CVSS 3.1 metrics')).toBeInTheDocument();
    expect(screen.getByText('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H')).toBeInTheDocument();
    expect(screen.getByText('nvd@nist.gov')).toBeInTheDocument();
    expect(screen.getByText('Exploitability (Score: 3.9)')).toBeInTheDocument();
    expect(screen.getByText('Impact (Score: 5.9)')).toBeInTheDocument();
    // The base score itself renders inside Circle's recharts ResponsiveContainer,
    // which jsdom always measures as 0x0 (see Circle.test.jsx) - only the severity
    // label sibling to it is reachable here.
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });
});
