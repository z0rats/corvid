import { render, screen } from '@testing-library/react';
import ReliabilityChip from './ReliabilityChip';

describe('ReliabilityChip', () => {
  it('shows the grade with its meaning for assistive tech', () => {
    render(<ReliabilityChip grade="B" />);

    expect(screen.getByText('B')).toBeTruthy();
    expect(screen.getByLabelText('Source reliability B: Usually reliable')).toBeTruthy();
  });

  it('renders nothing for an unrated feed', () => {
    const { container } = render(<ReliabilityChip grade={undefined} />);

    expect(container.firstChild).toBeNull();
  });
});
