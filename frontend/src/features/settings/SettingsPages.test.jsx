import React from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider, createStore } from 'jotai';
import { MemoryRouter, useLocation } from 'react-router';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../core/config/theme';
import { aiSettingsState, availableLlmModelsState, modulesState } from '../../core/state/atoms';
import { LLM_MODELS_REPROBE_EVENT } from '../../core/utils/llmModelsReprobe';
import { settingsApi } from './services/api/settingsApi';
import ApiKeys from './api-keys/ApiKeys';
import AiSettings from './ai-settings/AiSettings';
import Modules from './modules/Modules';

vi.mock('./services/api/settingsApi', () => ({
  settingsApi: {
    getServicesConfig: vi.fn(),
    getConfiguredApiKeys: vi.fn(),
    getActiveApiKeys: vi.fn(),
    testApiKey: vi.fn(),
    testAllApiKeys: vi.fn(),
    createApiKey: vi.fn(),
    updateAiSettings: vi.fn(),
    updateModuleStatus: vi.fn(),
  },
}));

const SERVICES = {
  virustotal: {
    name: 'VirusTotal',
    tier: 'freemium',
    description: 'File and URL reputation',
    supported_ioc_types: ['IPv4', 'Domain', 'MD5'],
    required_keys: ['virustotal'],
    documentation_url: 'https://docs.example/vt',
    available: true,
  },
  shodan: {
    name: 'Shodan',
    tier: 'paid',
    description: 'Internet-wide scan data',
    supported_ioc_types: ['IPv4'],
    required_keys: ['shodan'],
    documentation_url: 'https://docs.example/shodan',
    available: false,
    key_test_exempt_reason: 'Every call spends one request of the daily allowance.',
  },
  urlhaus: {
    name: 'URLhaus',
    tier: 'free',
    description: 'Malware URL feed',
    supported_ioc_types: ['URL'],
    required_keys: [],
    documentation_url: null,
    available: true,
  },
};

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.search}</div>;
}

function renderWithProviders(ui, { store = createStore(), route = '/' } = {}) {
  return render(
    <Provider store={store}>
      <ThemeProvider theme={lightTheme}>
        <MemoryRouter initialEntries={[route]}>
          {ui}
          <LocationProbe />
        </MemoryRouter>
      </ThemeProvider>
    </Provider>,
  );
}

const serviceNames = () => screen.getAllByRole('heading', { level: 6 }).map((h) => h.textContent)
  .filter((name) => Object.values(SERVICES).some((s) => s.name === name));

beforeEach(() => {
  vi.clearAllMocks();
  settingsApi.getServicesConfig.mockResolvedValue(SERVICES);
  settingsApi.getConfiguredApiKeys.mockResolvedValue({ virustotal: true });
  settingsApi.getActiveApiKeys.mockResolvedValue({ virustotal: true });
});

describe('ApiKeys', () => {
  it('lists every service alphabetically with its tier, IoC types and key status', async () => {
    renderWithProviders(<ApiKeys />);

    expect(await screen.findByText('VirusTotal')).toBeInTheDocument();
    expect(serviceNames()).toEqual(['Shodan', 'URLhaus', 'VirusTotal']);
    expect(screen.getByText('Freemium')).toBeInTheDocument();
    expect(screen.getByText('Paid')).toBeInTheDocument();
    expect(screen.getByText('MD5')).toBeInTheDocument();
    expect(screen.getByText('No API key required - Ready to use')).toBeInTheDocument();
    expect(screen.getByText(/2\/3 services configured/)).toBeInTheDocument();
    await waitFor(() => expect(settingsApi.getConfiguredApiKeys).toHaveBeenCalled());
  });

  it('filters services by name and by configured state', async () => {
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.change(screen.getByPlaceholderText('Search services...'), { target: { value: 'sho' } });
    expect(serviceNames()).toEqual(['Shodan']);

    fireEvent.click(screen.getByRole('switch', { name: 'Show only configured' }));
    expect(serviceNames()).toEqual([]);
    expect(screen.getByText('No services found')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('Search services...'), { target: { value: '' } });
    expect(serviceNames()).toEqual(['URLhaus', 'VirusTotal']);
  });

  it('narrows to the service named in ?service= and can return to the full list', async () => {
    renderWithProviders(<ApiKeys />, { route: '/settings/apikeys?service=shodan' });

    expect(await screen.findByText('Showing only Shodan.')).toBeInTheDocument();
    expect(serviceNames()).toEqual(['Shodan']);
    expect(screen.queryByPlaceholderText('Search services...')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Show all services' }));
    expect(screen.getByTestId('location')).toHaveTextContent('');
    expect(serviceNames()).toEqual(['Shodan', 'URLhaus', 'VirusTotal']);
  });

  it('ignores an unknown ?service= and shows everything', async () => {
    renderWithProviders(<ApiKeys />, { route: '/settings/apikeys?service=nope' });
    await screen.findByText('VirusTotal');
    expect(screen.queryByText(/Showing only/)).not.toBeInTheDocument();
    expect(serviceNames()).toHaveLength(3);
  });

  it('shows the backend error when the service configuration cannot be loaded', async () => {
    settingsApi.getServicesConfig.mockRejectedValue({ response: { data: { detail: 'Database locked' } } });
    renderWithProviders(<ApiKeys />);
    expect(await screen.findByText('Configuration Error')).toBeInTheDocument();
    expect(screen.getByText('Database locked')).toBeInTheDocument();
  });
});

describe('API key test', () => {
  it('tests one service and shows the status with its detail and quota', async () => {
    settingsApi.testApiKey.mockResolvedValue({
      service: 'virustotal', status: 'ok', http_status: 200, detail: 'The provider accepted the key.',
      quota: { used: 250, limit: 500, remaining: 250, period: 'daily' },
    });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test' }));

    expect(await screen.findByText('OK')).toBeInTheDocument();
    expect(settingsApi.testApiKey).toHaveBeenCalledWith('virustotal');
    expect(screen.getByText('250 / 500 used (daily)')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Quota used' })).toHaveAttribute('aria-valuenow', '50');
  });

  it('shows what to do when a key is rejected', async () => {
    settingsApi.testApiKey.mockResolvedValue({
      service: 'virustotal', status: 'rejected', http_status: 401, detail: 'The provider rejected the key.', quota: null,
    });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test' }));

    expect(await screen.findByText('Rejected')).toBeInTheDocument();
    expect(screen.getByText('The provider rejected the key.')).toBeInTheDocument();
  });

  it('says why a service cannot be tested instead of offering a button', async () => {
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    expect(screen.getByText('Can\'t be tested: Every call spends one request of the daily allowance.')).toBeInTheDocument();
    // Only VirusTotal (testable) has a button; URLhaus needs no key.
    expect(screen.getAllByRole('button', { name: 'Test' })).toHaveLength(1);
  });

  it('checks a key right after it is saved', async () => {
    settingsApi.getConfiguredApiKeys.mockResolvedValue({});
    settingsApi.createApiKey.mockResolvedValue({});
    settingsApi.testApiKey.mockResolvedValue({ service: 'virustotal', status: 'ok', detail: 'ok', quota: null });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.change(screen.getByLabelText('Virustotal'), { target: { value: 'new-key' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Save API key' })[1]);

    await waitFor(() => expect(settingsApi.testApiKey).toHaveBeenCalledWith('virustotal'));
    expect(await screen.findByText('OK')).toBeInTheDocument();
  });

  it('does not auto-check a service that cannot be tested', async () => {
    settingsApi.getConfiguredApiKeys.mockResolvedValue({});
    settingsApi.createApiKey.mockResolvedValue({});
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.change(screen.getByLabelText('Shodan'), { target: { value: 'new-key' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Save API key' })[0]);

    await waitFor(() => expect(settingsApi.createApiKey).toHaveBeenCalled());
    expect(settingsApi.testApiKey).not.toHaveBeenCalled();
  });

  it('keeps quiet when an after-save check finds the other keys of the service missing', async () => {
    settingsApi.getConfiguredApiKeys.mockResolvedValue({});
    settingsApi.createApiKey.mockResolvedValue({});
    settingsApi.testApiKey.mockResolvedValue({ service: 'virustotal', status: 'not_configured', detail: 'No key is saved.' });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.change(screen.getByLabelText('Virustotal'), { target: { value: 'new-key' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Save API key' })[1]);

    await waitFor(() => expect(settingsApi.testApiKey).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByRole('button', { name: 'Test' })).not.toBeDisabled());
    expect(screen.queryByText('Not configured')).not.toBeInTheDocument();
  });

  it('does not let an older Test all result overwrite a newer single test', async () => {
    let finishAll;
    settingsApi.testAllApiKeys.mockReturnValue(new Promise((resolve) => { finishAll = resolve; }));
    settingsApi.testApiKey.mockResolvedValue({ service: 'virustotal', status: 'ok', detail: 'ok', quota: null });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test all' }));
    fireEvent.click(screen.getByRole('button', { name: 'Test' }));
    expect(await screen.findByText('OK')).toBeInTheDocument();

    finishAll([{ service: 'virustotal', status: 'rejected', detail: 'stale', quota: null }]);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Test all' })).not.toBeDisabled());
    expect(screen.getByText('OK')).toBeInTheDocument();
    expect(screen.queryByText('Rejected')).not.toBeInTheDocument();
  });

  it('never renders a structured error detail as text', async () => {
    settingsApi.testAllApiKeys.mockRejectedValue({ response: { data: { detail: [{ msg: 'bad', loc: ['path'] }] } } });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test all' }));

    expect(await screen.findByText('Couldn\'t run the key check.')).toBeInTheDocument();
  });

  it('tests all keys at once and puts each result on its card', async () => {
    settingsApi.testAllApiKeys.mockResolvedValue([
      { service: 'virustotal', status: 'rate_limited', http_status: 429, detail: 'Out of quota.', quota: null },
    ]);
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test all' }));

    expect(await screen.findByText('Rate limited')).toBeInTheDocument();
  });

  it('shows an error when the test-all request itself fails', async () => {
    settingsApi.testAllApiKeys.mockRejectedValue({ response: { data: { detail: 'Too many requests' } } });
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test all' }));

    expect(await screen.findByText('Too many requests')).toBeInTheDocument();
  });

  it('marks a single test that could not be sent as an error', async () => {
    settingsApi.testApiKey.mockRejectedValue({});
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');

    fireEvent.click(screen.getByRole('button', { name: 'Test' }));

    expect(await screen.findByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Couldn\'t run the key check.')).toBeInTheDocument();
  });
});

describe('AiSettings', () => {
  const MODELS = [
    { id: 'claude-x', name: 'Claude X', provider: 'anthropic' },
    { id: 'gpt-y', name: 'GPT Y', provider: 'openai' },
  ];

  function renderAi({ models = MODELS, settings = { default_model: 'gpt-y' } } = {}) {
    const store = createStore();
    store.set(availableLlmModelsState, models);
    store.set(aiSettingsState, settings);
    renderWithProviders(<AiSettings />, { store });
    return store;
  }

  async function pick(label, option) {
    fireEvent.mouseDown(screen.getByRole('combobox', { name: label }));
    fireEvent.click(await screen.findByRole('option', { name: option }));
  }

  it('asks the app to re-probe the model registry on open', () => {
    const listener = vi.fn();
    window.addEventListener(LLM_MODELS_REPROBE_EVENT, listener);
    renderAi();
    window.removeEventListener(LLM_MODELS_REPROBE_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('lists models grouped by provider and saves the chosen global default', async () => {
    const store = renderAi();
    settingsApi.updateAiSettings.mockResolvedValue({ default_model: 'claude-x' });

    expect(screen.getByRole('combobox', { name: 'Default Model' })).toHaveTextContent('GPT Y');
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Default Model' }));
    const listbox = await screen.findByRole('listbox');
    expect(within(listbox).getByText('anthropic')).toBeInTheDocument();
    expect(within(listbox).getByText('openai')).toBeInTheDocument();
    expect(within(listbox).queryByText('Use global default')).not.toBeInTheDocument();
    fireEvent.click(within(listbox).getByRole('option', { name: 'Claude X' }));

    await waitFor(() => expect(settingsApi.updateAiSettings).toHaveBeenCalledWith({ default_model: 'claude-x' }));
    expect(await screen.findByText('AI settings updated successfully.')).toBeInTheDocument();
    expect(store.get(aiSettingsState)).toEqual({ default_model: 'claude-x' });
  });

  it('clears a per-module override back to the global default by sending an empty string', async () => {
    renderAi({ settings: { default_model: 'gpt-y', email_analyzer_model: 'claude-x' } });
    settingsApi.updateAiSettings.mockResolvedValue({ default_model: 'gpt-y', email_analyzer_model: null });

    await pick('Email Analyzer', 'Use global default');

    await waitFor(() => expect(settingsApi.updateAiSettings).toHaveBeenCalledWith({ email_analyzer_model: '' }));
  });

  it('reports a failed save', async () => {
    renderAi();
    settingsApi.updateAiSettings.mockRejectedValue({ response: { data: { detail: 'Unknown model' } } });

    await pick('Image Geolocation', 'Claude X');

    expect(await screen.findByText('Unknown model')).toBeInTheDocument();
  });

  it('disables every selector when no model is available', () => {
    renderAi({ models: [] });
    for (const box of screen.getAllByRole('combobox')) {
      expect(box).toHaveAttribute('aria-disabled', 'true');
    }
  });
});

describe('Modules', () => {
  function renderModules(modules) {
    const store = createStore();
    store.set(modulesState, modules);
    renderWithProviders(<Modules />, { store });
    return store;
  }

  it('shows a loading notice until modules arrive', () => {
    renderModules({});
    expect(screen.getByText('Loading modules...')).toBeInTheDocument();
  });

  it('lists only known modules with their descriptions and state', () => {
    renderModules({
      ioc_tools: { enabled: true },
      cvss_calculator: { enabled: false },
      legacy_thing: { enabled: true },
    });

    expect(screen.getByRole('switch', { name: 'IOC Tools' })).toBeChecked();
    expect(screen.getByRole('switch', { name: 'CVSS Calculator' })).not.toBeChecked();
    expect(screen.getByText('Look up, extract, and analyze indicators of compromise.')).toBeInTheDocument();
    expect(screen.getAllByRole('switch')).toHaveLength(2);
  });

  it('toggles a module and confirms', async () => {
    settingsApi.updateModuleStatus.mockResolvedValue({});
    const store = renderModules({ ioc_tools: { enabled: true }, newsfeed: { enabled: false } });

    fireEvent.click(screen.getByRole('switch', { name: 'Newsfeed' }));

    await waitFor(() => expect(settingsApi.updateModuleStatus).toHaveBeenCalledWith('newsfeed', true));
    expect(await screen.findByText('Module enabled successfully.')).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: 'Newsfeed' })).toBeChecked();
    expect(store.get(modulesState).newsfeed.enabled).toBe(true);
  });

  it('keeps the module state and reports the error when the toggle fails', async () => {
    settingsApi.updateModuleStatus.mockRejectedValue({ response: { data: { detail: 'Module locked' } } });
    renderModules({ ioc_tools: { enabled: true } });

    fireEvent.click(screen.getByRole('switch', { name: 'IOC Tools' }));

    expect(await screen.findByText('Module locked')).toBeInTheDocument();
    expect(settingsApi.updateModuleStatus).toHaveBeenCalledWith('ioc_tools', false);
    expect(screen.getByRole('switch', { name: 'IOC Tools' })).toBeChecked();
  });
});
