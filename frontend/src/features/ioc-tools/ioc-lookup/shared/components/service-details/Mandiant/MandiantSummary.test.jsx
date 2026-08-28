import React from 'react';
import { render, screen } from '@testing-library/react';
import MandiantSummary from './MandiantSummary';

describe('MandiantSummary', () => {
  it('shows empty-state placeholders when there is no category or timeline data', () => {
    render(
      <MandiantSummary
        categoryStats={{}}
        pieData={[{ id: 'No Data', label: 'No Data', value: 1 }]}
        lineChartData={[]}
        riskScore={0}
        indicatorCount={0}
        reportCount={0}
      />
    );

    expect(screen.getByText('No threat categories available')).toBeInTheDocument();
    expect(screen.getByText('No timeline data available')).toBeInTheDocument();
    expect(screen.getByText('Average Risk Score')).toBeInTheDocument();
  });

  it('renders the summary stat cards with the given counts', () => {
    render(
      <MandiantSummary
        categoryStats={{ malware: 3 }}
        pieData={[{ id: 'malware', label: 'malware', value: 3 }]}
        lineChartData={[{ date: 'Jan 2024', count: 2 }]}
        riskScore={65}
        indicatorCount={5}
        reportCount={2}
      />
    );

    expect(screen.getByText('65')).toBeInTheDocument();
    expect(screen.getByText('Indicators Found')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Related Reports')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.queryByText('No threat categories available')).not.toBeInTheDocument();
    expect(screen.queryByText('No timeline data available')).not.toBeInTheDocument();
  });

  it('shows N/A when riskScore is null', () => {
    render(
      <MandiantSummary
        categoryStats={{}}
        pieData={[]}
        lineChartData={[]}
        riskScore={null}
        indicatorCount={0}
        reportCount={0}
      />
    );

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });
});
