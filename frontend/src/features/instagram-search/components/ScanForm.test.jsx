import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ScanForm from './ScanForm';

// jsdom doesn't fire a <button type="submit">'s default form-submission
// behaviour on a plain click - submitting the form directly is the reliable
// way to exercise ScanForm's own onSubmit logic in this environment.
function submitForm() {
  fireEvent.submit(screen.getByRole('button', { name: /scan/i }).closest('form'));
}

describe('ScanForm', () => {
  it('defaults to the posts scan type', () => {
    render(<ScanForm onScan={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button', { name: /posts/i, pressed: true })).toBeInTheDocument();
  });

  it('disables the scan button while the username field is empty', () => {
    render(<ScanForm onScan={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button', { name: /^scan$/i })).toBeDisabled();
  });

  it('submits the trimmed username with the default (posts) scan type', async () => {
    const onScan = vi.fn();
    render(<ScanForm onScan={onScan} disabled={false} />);

    await userEvent.type(screen.getByLabelText(/instagram username/i), '  someuser  ');
    submitForm();

    expect(onScan).toHaveBeenCalledWith({ username: 'someuser', scanType: 'posts' });
  });

  it('submits the selected scan type after switching it', async () => {
    const onScan = vi.fn();
    render(<ScanForm onScan={onScan} disabled={false} />);

    await userEvent.click(screen.getByRole('button', { name: /followers/i }));
    await userEvent.type(screen.getByLabelText(/instagram username/i), 'someuser');
    submitForm();

    expect(onScan).toHaveBeenCalledWith({ username: 'someuser', scanType: 'followers' });
  });

  it('shows the session-required note for followers/followees but not posts', async () => {
    render(<ScanForm onScan={vi.fn()} disabled={false} />);
    expect(screen.queryByText(/needs a configured instagram session/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /followees/i }));
    expect(screen.getByText(/needs a configured instagram session/i)).toBeInTheDocument();
  });

  it('prefills the username from initialUsername/initialScanType', () => {
    render(<ScanForm onScan={vi.fn()} disabled={false} initialUsername="someuser" initialScanType="followers" />);

    expect(screen.getByLabelText(/instagram username/i).value).toBe('someuser');
    expect(screen.getByRole('button', { name: /followers/i, pressed: true })).toBeInTheDocument();
  });

  it('disables every control while a scan is running', () => {
    render(<ScanForm onScan={vi.fn()} disabled initialUsername="someuser" />);

    expect(screen.getByLabelText(/instagram username/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /^scan$/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /posts/i })).toBeDisabled();
  });
});
