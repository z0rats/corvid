import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import TelegramSettings from './TelegramSettings';
import { settingsApi } from '../services/api/settingsApi';

vi.mock('../services/api/settingsApi');

const DEFAULT_SETTINGS = {
  id: 1,
  bot_token: '',
  chat_id: '',
  enabled: false,
  notify_scan_events: true,
  notify_job_failures: true,
  notify_newsfeed_matches: true,
  bot_commands_enabled: false,
  web_base_url: '',
};

beforeEach(() => {
  settingsApi.getTelegramSettings.mockResolvedValue(DEFAULT_SETTINGS);
});

afterEach(() => vi.clearAllMocks());

function renderTelegramSettings() {
  return render(
    <MemoryRouter>
      <TelegramSettings />
    </MemoryRouter>
  );
}

describe('TelegramSettings — connection', () => {
  it('renders defaults and disables the test button until configured', async () => {
    renderTelegramSettings();

    expect(await screen.findByText('Bot connection')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send test message/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^save$/i })).toBeDisabled();
  });

  it('saves the bot token and chat ID', async () => {
    const user = userEvent.setup();
    settingsApi.updateTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      bot_token: '123:abc',
      chat_id: '42',
    });
    renderTelegramSettings();
    await screen.findByText('Bot connection');

    await user.type(screen.getByLabelText(/bot token/i), '123:abc');
    await user.type(screen.getByLabelText(/chat id/i), '42');
    await user.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(settingsApi.updateTelegramSettings).toHaveBeenCalledWith({
        bot_token: '123:abc',
        chat_id: '42',
        web_base_url: '',
      });
    });
    expect(await screen.findByText(/telegram connection settings saved/i)).toBeInTheDocument();
  });

  it('saves the web base URL alongside the connection fields', async () => {
    const user = userEvent.setup();
    settingsApi.updateTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      web_base_url: 'https://corvid.example.com',
    });
    renderTelegramSettings();
    await screen.findByText('Bot connection');

    await user.type(screen.getByLabelText(/web base url/i), 'https://corvid.example.com');
    await user.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(settingsApi.updateTelegramSettings).toHaveBeenCalledWith({
        bot_token: '',
        chat_id: '',
        web_base_url: 'https://corvid.example.com',
      });
    });
  });

  it('sends a test message once configured', async () => {
    const user = userEvent.setup();
    settingsApi.getTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      bot_token: '123:abc',
      chat_id: '42',
    });
    settingsApi.sendTelegramTestMessage.mockResolvedValue({
      sent: true,
      message: 'Test message delivered.',
    });
    renderTelegramSettings();
    await screen.findByText('Bot connection');

    await user.click(screen.getByRole('button', { name: /send test message/i }));

    await waitFor(() => expect(settingsApi.sendTelegramTestMessage).toHaveBeenCalled());
    expect(await screen.findByText('Test message delivered.')).toBeInTheDocument();
  });

  it('shows an error notification when the test message fails', async () => {
    const user = userEvent.setup();
    settingsApi.getTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      bot_token: '123:abc',
      chat_id: '42',
    });
    settingsApi.sendTelegramTestMessage.mockRejectedValue(new Error('boom'));
    renderTelegramSettings();
    await screen.findByText('Bot connection');

    await user.click(screen.getByRole('button', { name: /send test message/i }));

    expect(await screen.findByText('boom')).toBeInTheDocument();
  });
});

describe('TelegramSettings — preferences', () => {
  it('toggles a preference immediately', async () => {
    const user = userEvent.setup();
    settingsApi.updateTelegramSettings.mockResolvedValue({ ...DEFAULT_SETTINGS, enabled: true });
    renderTelegramSettings();
    await screen.findByText('Notification preferences');

    await user.click(screen.getByLabelText(/enable telegram notifications/i));

    await waitFor(() => {
      expect(settingsApi.updateTelegramSettings).toHaveBeenCalledWith({ enabled: true });
    });
  });

  it('toggles the newsfeed-match preference', async () => {
    const user = userEvent.setup();
    settingsApi.getTelegramSettings.mockResolvedValue({ ...DEFAULT_SETTINGS, enabled: true });
    settingsApi.updateTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      enabled: true,
      notify_newsfeed_matches: false,
    });
    renderTelegramSettings();
    await screen.findByText('Notification preferences');

    await user.click(
      screen.getByLabelText(/notify when a newsfeed article matches/i)
    );

    await waitFor(() => {
      expect(settingsApi.updateTelegramSettings).toHaveBeenCalledWith({
        notify_newsfeed_matches: false,
      });
    });
  });

  it('disables preference toggles other than the master switch while disabled', async () => {
    renderTelegramSettings();
    await screen.findByText('Notification preferences');

    expect(screen.getByLabelText(/notify on scan completed/i)).toBeDisabled();
    expect(screen.getByLabelText(/notify when a recurring job/i)).toBeDisabled();
    expect(screen.getByLabelText(/notify when a newsfeed article matches/i)).toBeDisabled();
  });
});

describe('TelegramSettings — bot commands', () => {
  it('disables the bot commands switch while the master switch is off', async () => {
    renderTelegramSettings();
    await screen.findByText('Bot commands');

    expect(screen.getByLabelText(/enable inbound bot commands/i)).toBeDisabled();
  });

  it('toggles bot commands once enabled', async () => {
    const user = userEvent.setup();
    settingsApi.getTelegramSettings.mockResolvedValue({ ...DEFAULT_SETTINGS, enabled: true });
    settingsApi.updateTelegramSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS,
      enabled: true,
      bot_commands_enabled: true,
    });
    renderTelegramSettings();
    await screen.findByText('Bot commands');

    await user.click(screen.getByLabelText(/enable inbound bot commands/i));

    await waitFor(() => {
      expect(settingsApi.updateTelegramSettings).toHaveBeenCalledWith({
        bot_commands_enabled: true,
      });
    });
  });
});
