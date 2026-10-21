import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RuSettings from './Settings';
import EmailSettings from '../../email-search/settings/Settings';
import PhoneSettings from '../../phone-search/settings/Settings';
import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';
import { emailSearchApi } from '../../email-search/services/api/emailSearchApi';
import { phoneSearchApi } from '../../phone-search/services/api/phoneSearchApi';

vi.mock('../services/api/ruBusinessCheckApi', () => ({ ruBusinessCheckApi: { getConfig: vi.fn(), updateConfig: vi.fn() } }));
vi.mock('../../email-search/services/api/emailSearchApi', () => ({
  emailSearchApi: { getConfig: vi.fn(), updateConfig: vi.fn(), checkUpdate: vi.fn() },
}));
vi.mock('../../phone-search/services/api/phoneSearchApi', () => ({ phoneSearchApi: { getConfig: vi.fn(), updateConfig: vi.fn() } }));

function commit(input, value) {
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value } });
  fireEvent.blur(input);
}

afterEach(() => vi.clearAllMocks());

describe('ru-business-check Settings', () => {
  const CONFIG = {
    fresh_registration_threshold_days: 365, history_retention_days: 90,
    small_claim_amount_threshold: 100000, large_claim_amount_threshold: 1000000,
    multiple_claims_defendant_threshold: 3, mass_address_threshold: 10,
    equity_ratio_threshold: 0.1, current_ratio_threshold: 1.0, revenue_drop_threshold: 0.5,
    domain_age_gap_days: 365,
  };

  async function setup() {
    ruBusinessCheckApi.getConfig.mockResolvedValue(CONFIG);
    ruBusinessCheckApi.updateConfig.mockImplementation(async (c) => c);
    render(<RuSettings />);
    await waitFor(() => expect(screen.getByLabelText('Порог автономии (капитал / баланс)')).toHaveValue(0.1));
  }

  it('saves a decimal threshold (typing "0." no longer collapses to 0)', async () => {
    await setup();
    const equity = screen.getByLabelText('Порог автономии (капитал / баланс)');
    fireEvent.focus(equity);
    fireEvent.change(equity, { target: { value: '0.' } });
    fireEvent.change(equity, { target: { value: '0.25' } });
    expect(ruBusinessCheckApi.updateConfig).not.toHaveBeenCalled();
    fireEvent.blur(equity);
    await waitFor(() => expect(ruBusinessCheckApi.updateConfig).toHaveBeenCalledTimes(1));
    expect(ruBusinessCheckApi.updateConfig).toHaveBeenCalledWith(expect.objectContaining({ equity_ratio_threshold: 0.25 }));
  });

  it('saves integer thresholds as numbers', async () => {
    await setup();
    commit(screen.getByLabelText('Хранение истории, дней'), '0');
    await waitFor(() => expect(ruBusinessCheckApi.updateConfig).toHaveBeenCalledWith(expect.objectContaining({ history_retention_days: 0 })));
  });

  it('an emptied field is not saved as 0', async () => {
    await setup();
    commit(screen.getByLabelText('Порог «массового адреса», компаний'), '');
    expect(ruBusinessCheckApi.updateConfig).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Порог «массового адреса», компаний')).toHaveValue(10);
  });
});

describe('email-search Settings', () => {
  const CONFIG = {
    timeout_seconds: 10, max_concurrency: 20, proxy_url: '', use_tor: false,
    enable_smtp_checks: false, enable_headless_checks: false,
  };

  async function setup() {
    emailSearchApi.getConfig.mockResolvedValue(CONFIG);
    emailSearchApi.updateConfig.mockImplementation(async (c) => c);
    render(<EmailSettings />);
    await screen.findByText('Email Search Settings');
  }

  it('saves fields and toggles optional checkers', async () => {
    await setup();
    commit(screen.getByLabelText('Max concurrency'), '5');
    expect(await screen.findByText('Settings updated successfully')).toBeInTheDocument();
    expect(emailSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ max_concurrency: 5 }));

    const [tor] = screen.getAllByRole('switch');
    fireEvent.click(tor);
    await waitFor(() => expect(emailSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ use_tor: true })));
  });

  it('checks PyPI for a newer mailcat', async () => {
    emailSearchApi.checkUpdate.mockResolvedValue({ latest_version: '0.9.1' });
    await setup();
    fireEvent.click(screen.getByRole('button', { name: /Check PyPI/ }));
    expect(await screen.findByText(/v0\.9\.1/)).toBeInTheDocument();
  });

  it('shows the backend validation error on a rejected save', async () => {
    await setup();
    emailSearchApi.updateConfig.mockRejectedValue({ response: { data: { detail: 'proxy_url: invalid scheme' } } });
    commit(screen.getByLabelText('Proxy URL'), 'ftp://x');
    expect(await screen.findByText('proxy_url: invalid scheme')).toBeInTheDocument();
  });
});

describe('phone-search Settings', () => {
  it('saves timeout and proxy', async () => {
    phoneSearchApi.getConfig.mockResolvedValue({ timeout_seconds: 10, proxy_url: '' });
    phoneSearchApi.updateConfig.mockImplementation(async (c) => c);
    render(<PhoneSettings />);
    await screen.findByText('Phone Search Settings');
    commit(screen.getByLabelText('Timeout (seconds)'), '20');
    await waitFor(() => expect(phoneSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ timeout_seconds: 20 })));
    commit(screen.getByLabelText('Proxy URL'), 'http://127.0.0.1:8080');
    await waitFor(() => expect(phoneSearchApi.updateConfig).toHaveBeenLastCalledWith(expect.objectContaining({ proxy_url: 'http://127.0.0.1:8080' })));
  });
});
