import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LiveScanView from './LiveScanView';

const BASE = {
  phase: 'running',
  stage: 'resolving',
  friendsTotal: 0,
  analyzed: 0,
  candidatesSelected: 0,
  error: '',
};

describe('LiveScanView', () => {
  it('shows an indeterminate bar and the resolving label before counts are known', () => {
    render(<LiveScanView scan={BASE} cancelScan={vi.fn()} />);
    expect(screen.getByText(/resolving target/i)).toBeInTheDocument();
  });

  it('shows the friend count once fetched', () => {
    render(<LiveScanView scan={{ ...BASE, stage: 'friends', friendsTotal: 42 }} cancelScan={vi.fn()} />);
    expect(screen.getByText(/fetched 42 friends/i)).toBeInTheDocument();
  });

  it('shows analyzed/total progress during the mutual-connections stage', () => {
    render(
      <LiveScanView
        scan={{ ...BASE, stage: 'mutual', analyzed: 3, candidatesSelected: 10 }}
        cancelScan={vi.fn()}
      />,
    );
    expect(screen.getByText(/analyzing mutual connections \(3\/10\)/i)).toBeInTheDocument();
  });

  it('calls cancelScan when the cancel button is clicked', async () => {
    const cancelScan = vi.fn();
    render(<LiveScanView scan={BASE} cancelScan={cancelScan} />);

    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

    expect(cancelScan).toHaveBeenCalled();
  });

  it('shows a failed message with the error text', () => {
    render(<LiveScanView scan={{ ...BASE, phase: 'failed', error: 'Steam rejected the key' }} cancelScan={vi.fn()} />);
    expect(screen.getByText(/scan failed: steam rejected the key/i)).toBeInTheDocument();
  });

  it('shows a cancelled chip', () => {
    render(<LiveScanView scan={{ ...BASE, phase: 'cancelled' }} cancelScan={vi.fn()} />);
    expect(screen.getByText(/scan cancelled/i)).toBeInTheDocument();
  });

  it('shows a completed chip', () => {
    render(<LiveScanView scan={{ ...BASE, phase: 'completed' }} cancelScan={vi.fn()} />);
    expect(screen.getByText(/scan completed/i)).toBeInTheDocument();
  });

  it('renders nothing but the stage line once idle-adjacent phases are left', () => {
    render(<LiveScanView scan={{ ...BASE, phase: 'completed' }} cancelScan={vi.fn()} />);
    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
  });
});
