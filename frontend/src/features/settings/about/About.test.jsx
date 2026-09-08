import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import About from './About';
import { settingsApi } from '../services/api/settingsApi';
import { healthService } from '../../../core/services/api/healthService';
import { getAccessToken, setAccessToken, clearAccessToken } from '../../../core/utils/accessToken';

vi.mock('../services/api/settingsApi');
vi.mock('../../../core/services/api/healthService');

beforeEach(() => {
  healthService.getLatestRelease.mockResolvedValue({ latest_version: null });
  setAccessToken('current-token-abc');
});

afterEach(() => {
  vi.clearAllMocks();
  clearAccessToken();
});

describe('About — access token card', () => {
  it('renders the current token masked by default', async () => {
    render(<About />);

    const field = await screen.findByDisplayValue('current-token-abc');
    expect(field).toHaveAttribute('type', 'password');
  });

  it('regenerates the token, updates local storage, and reveals the new value', async () => {
    const user = userEvent.setup();
    settingsApi.regenerateAccessToken.mockResolvedValue({ access_token: 'new-token-xyz' });
    render(<About />);
    await screen.findByDisplayValue('current-token-abc');

    await user.click(screen.getByRole('button', { name: 'Regenerate token' }));
    expect(await screen.findByText('Regenerate access token?')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Regenerate' }));

    await waitFor(() => {
      expect(settingsApi.regenerateAccessToken).toHaveBeenCalled();
    });
    expect(await screen.findByDisplayValue('new-token-xyz')).toHaveAttribute('type', 'text');
    expect(getAccessToken()).toBe('new-token-xyz');
    expect(
      await screen.findByText(/Copy it now and update any other browser, device/i)
    ).toBeInTheDocument();
  });

  it('shows the fixed-by-env message without changing the stored token', async () => {
    const user = userEvent.setup();
    settingsApi.regenerateAccessToken.mockRejectedValue({
      response: { data: { error_code: 'ACCESS_TOKEN_FIXED_BY_ENV', detail: 'fixed' } },
    });
    render(<About />);
    await screen.findByDisplayValue('current-token-abc');

    await user.click(screen.getByRole('button', { name: 'Regenerate token' }));
    await user.click(screen.getByRole('button', { name: 'Regenerate' }));

    expect(
      await screen.findByText(/can't be regenerated here/i)
    ).toBeInTheDocument();
    expect(getAccessToken()).toBe('current-token-abc');
  });
});
