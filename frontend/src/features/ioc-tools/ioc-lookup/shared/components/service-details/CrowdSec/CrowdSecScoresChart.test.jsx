import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CrowdSecScoresChart from './CrowdSecScoresChart';

const scoreData = [
  { name: 'Overall', aggressiveness: 1, threat: 2, trust: 3, anomaly: 4, total: 5 },
];

describe('CrowdSecScoresChart', () => {
  it('renders the chart title', () => {
    render(<CrowdSecScoresChart scoreData={scoreData} />);
    expect(screen.getByText('CTI Scores Breakdown')).toBeInTheDocument();
  });

  it('opens the score info modal when the info button is clicked', async () => {
    const user = userEvent.setup();
    render(<CrowdSecScoresChart scoreData={scoreData} />);

    expect(screen.queryByText('CTI Score Information')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Show score info' }));

    expect(screen.getByText('CTI Score Information')).toBeInTheDocument();
  });
});
