import React from 'react';
import { render, screen } from '@testing-library/react';
import PostingActivityChart from './PostingActivityChart';

function itemAt(isoString) {
  return { created_utc: Math.floor(new Date(isoString).getTime() / 1000) };
}

describe('PostingActivityChart', () => {
  it('renders nothing when there are no items', () => {
    const { container } = render(<PostingActivityChart items={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when items is null/undefined', () => {
    const { container } = render(<PostingActivityChart items={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders both the hour-of-day and by-month charts when items are present', () => {
    render(<PostingActivityChart items={[itemAt('2024-01-05T09:00:00'), itemAt('2024-03-01T14:00:00')]} />);

    expect(screen.getByText('Posting Activity')).toBeInTheDocument();
    expect(screen.getByText('By hour of day')).toBeInTheDocument();
    expect(screen.getByText('By month')).toBeInTheDocument();
  });
});
