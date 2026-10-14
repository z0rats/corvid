import { render, screen } from '@testing-library/react';
import ScanQueuedNotice from './ScanQueuedNotice';

describe('ScanQueuedNotice', () => {
  it('tells the user the scan is waiting for a free slot', () => {
    render(<ScanQueuedNotice />);
    expect(screen.getByRole('alert')).toHaveTextContent(/queued/i);
  });
});
