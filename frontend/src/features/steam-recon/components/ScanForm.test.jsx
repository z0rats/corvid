import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ScanForm from './ScanForm';
import { MAX_FRIENDS_DEFAULT } from '../utils/steamReconConfig';

// jsdom doesn't implement a `<button type="submit">` click's default form-submission behaviour
// (a plain `fireEvent.submit`/`userEvent.click` on the button never fires the form's `submit`
// event here, unlike a real browser) - submitting the form directly is the reliable way to
// exercise ScanForm's own onSubmit logic in this environment.
function submitForm() {
  fireEvent.submit(screen.getByRole('button', { name: /start scan/i }).closest('form'));
}

describe('ScanForm', () => {
  it('prefills the target from initialTarget', () => {
    render(<ScanForm onSubmit={vi.fn()} disabled={false} initialTarget="robinwalker" />);
    expect(screen.getByLabelText(/steam id, profile url/i).value).toBe('robinwalker');
  });

  it('disables the submit button while the field is empty', () => {
    render(<ScanForm onSubmit={vi.fn()} disabled={false} initialTarget="" />);
    expect(screen.getByRole('button', { name: /start scan/i })).toBeDisabled();
  });

  it('submits the target with the default max friends and cheater-report settings', async () => {
    const onSubmit = vi.fn();
    render(<ScanForm onSubmit={onSubmit} disabled={false} initialTarget="" />);

    await userEvent.type(screen.getByLabelText(/steam id, profile url/i), 'robinwalker');
    submitForm();

    expect(onSubmit).toHaveBeenCalledWith('robinwalker', {
      maxFriends: MAX_FRIENDS_DEFAULT,
      includeCsReport: true,
    });
  });

  it('unchecking the CS2 report checkbox submits includeCsReport: false', async () => {
    const onSubmit = vi.fn();
    render(<ScanForm onSubmit={onSubmit} disabled={false} initialTarget="robinwalker" />);

    await userEvent.click(screen.getByRole('checkbox'));
    submitForm();

    expect(onSubmit).toHaveBeenCalledWith('robinwalker', {
      maxFriends: MAX_FRIENDS_DEFAULT,
      includeCsReport: false,
    });
  });

  it('moving the friends slider changes the submitted maxFriends', async () => {
    const onSubmit = vi.fn();
    render(<ScanForm onSubmit={onSubmit} disabled={false} initialTarget="robinwalker" />);

    const slider = screen.getByRole('slider');
    slider.focus();
    await userEvent.keyboard('{ArrowRight}');
    submitForm();

    expect(onSubmit).toHaveBeenCalledWith('robinwalker', {
      maxFriends: MAX_FRIENDS_DEFAULT + 10,
      includeCsReport: true,
    });
  });

  it('disables every control while a scan is running', () => {
    render(<ScanForm onSubmit={vi.fn()} disabled initialTarget="robinwalker" />);

    expect(screen.getByLabelText(/steam id, profile url/i)).toBeDisabled();
    expect(screen.getByRole('checkbox')).toBeDisabled();
    expect(screen.getByRole('button', { name: /start scan/i })).toBeDisabled();
  });
});
