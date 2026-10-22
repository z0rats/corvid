import { fireEvent, render, screen } from '@testing-library/react';
import ScanForm from './ScanForm';

describe('ScanForm', () => {
  it('submits the trimmed target with the default sample size', () => {
    const onSubmit = vi.fn();
    render(<ScanForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText(/channel or group/i), { target: { value: '  @durov ' } });
    fireEvent.click(screen.getByRole('button', { name: /analyze/i }));

    expect(onSubmit).toHaveBeenCalledWith('@durov', { maxPosts: 100 });
  });

  it('keeps the submit button disabled for a blank target', () => {
    render(<ScanForm onSubmit={vi.fn()} />);
    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled();
  });

  it('treats a null prefill as empty', () => {
    render(<ScanForm onSubmit={vi.fn()} initialTarget={null} />);
    expect(screen.getByLabelText(/channel or group/i).value).toBe('');
  });

  it('shows the request estimate for the chosen sample size', () => {
    render(<ScanForm onSubmit={vi.fn()} />);
    expect(screen.getByText(/about 7 requests/i)).toBeInTheDocument();
  });

  it('disables everything while a scan runs', () => {
    render(<ScanForm onSubmit={vi.fn()} disabled initialTarget="durov" />);
    expect(screen.getByLabelText(/channel or group/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled();
  });
});
