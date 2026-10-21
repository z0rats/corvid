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
    getQuotaStatus: vi.fn(),
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
  settingsApi.getQuotaStatus.mockResolvedValue([]);
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

describe('QuotaPanel', () => {
  it('shows usage, remaining-only, unconfigured and failing providers', async () => {
    settingsApi.getQuotaStatus.mockResolvedValue([
      { provider: 'VirusTotal', configured: true, used: 250, limit: 500 },
      { provider: 'Hunter.io', configured: true, remaining: 42 },
      { provider: 'Shodan', configured: false },
      { provider: 'GreyNoise', configured: true, error: 'Invalid API key' },
    ]);
    renderWithProviders(<ApiKeys />);

    expect(await screen.findByText('250 / 500 used')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: '' })).toHaveAttribute('aria-valuenow', '50');
    expect(screen.getByText('42 remaining')).toBeInTheDocument();
    expect(screen.getByText('No API key configured')).toBeInTheDocument();
    expect(screen.getByText('Invalid API key')).toBeInTheDocument();
  });

  it('caps the bar at 100% when usage exceeds the limit', async () => {
    settingsApi.getQuotaStatus.mockResolvedValue([{ provider: 'VirusTotal', configured: true, used: 900, limit: 500 }]);
    renderWithProviders(<ApiKeys />);
    await screen.findByText('900 / 500 used');
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('loads quota once, only after the service list is ready', async () => {
    renderWithProviders(<ApiKeys />);
    expect(screen.getByText('Loading service configuration...')).toBeInTheDocument();
    expect(screen.queryByText('No services found')).not.toBeInTheDocument();
    expect(settingsApi.getQuotaStatus).not.toHaveBeenCalled();

    await screen.findByText('VirusTotal');
    await waitFor(() => expect(settingsApi.getQuotaStatus).toHaveBeenCalled());
    expect(settingsApi.getQuotaStatus).toHaveBeenCalledTimes(1);
  });

  it('re-fetches on refresh and shows a load error', async () => {
    renderWithProviders(<ApiKeys />);
    await screen.findByText('VirusTotal');
    await waitFor(() => expect(settingsApi.getQuotaStatus).toHaveBeenCalledTimes(1));

    settingsApi.getQuotaStatus.mockRejectedValue({ response: { data: { detail: 'Quota service down' } } });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));

    expect(await screen.findByText('Quota service down')).toBeInTheDocument();
    expect(settingsApi.getQuotaStatus).toHaveBeenCalledTimes(2);
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
