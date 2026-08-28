import React from 'react';
import { render, screen } from '@testing-library/react';
import MandiantDetails from './MandiantDetails';

// MandiantSummary/MandiantIndicators/MandiantReports and mandiantDataUtils.js each
// have their own dedicated tests; this covers the orchestrator's own branching.
describe('MandiantDetails', () => {
  it('shows a no-info message when result is missing', () => {
    render(<MandiantDetails result={null} />);
    expect(
      screen.getByText('No detailed intelligence information found for this indicator in Mandiant.')
    ).toBeInTheDocument();
  });

  it('shows a no-info message when there are no indicators or reports', () => {
    render(<MandiantDetails result={{ indicators: [], reports: { objects: [] } }} />);
    expect(
      screen.getByText('No detailed intelligence information found for this indicator in Mandiant.')
    ).toBeInTheDocument();
  });

  it('renders only the indicators accordion when there are no reports', () => {
    render(
      <MandiantDetails
        result={{ indicators: [{ value: 'evil.example', type: 'domain', mscore: 50 }] }}
      />
    );

    expect(screen.getByText('Indicators (1)')).toBeInTheDocument();
    expect(screen.queryByText(/^Reports/)).not.toBeInTheDocument();
  });

  it('renders only the reports accordion when there are no indicators', () => {
    render(
      <MandiantDetails
        result={{
          reports: { objects: [{ report_id: 'RPT-1', title: 'Report Title', publish_date: '2024-01-01' }] },
        }}
      />
    );

    expect(screen.getByText('Reports (1)')).toBeInTheDocument();
    // MandiantSummary's "Indicators Found: 0" stat card always renders - only the
    // accordion (titled "Indicators (<count>)") is conditional on there being any.
    expect(screen.queryByText(/^Indicators \(/)).not.toBeInTheDocument();
  });

  it('computes an average risk score across indicators', () => {
    render(
      <MandiantDetails
        result={{
          indicators: [
            { value: 'a.example', type: 'domain', mscore: 20 },
            { value: 'b.example', type: 'domain', mscore: 40 },
          ],
        }}
      />
    );

    expect(screen.getByText('Average Risk Score')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });
});
