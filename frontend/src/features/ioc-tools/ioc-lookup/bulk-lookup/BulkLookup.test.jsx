import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BulkLookup from './BulkLookup';
import { useServiceDefinitions } from '../shared/hooks/useServiceDefinitions';
import { useBulkLookupSettings } from './hooks/api/useBulkLookupSettings';

vi.mock('../shared/hooks/useServiceDefinitions');
vi.mock('./hooks/api/useBulkLookupSettings');

beforeEach(() => {
  useServiceDefinitions.mockReturnValue({ serviceDefinitions: [], loading: false });
  useBulkLookupSettings.mockReturnValue({
    loadingSettings: false,
    serviceSettings: [],
    settingsError: null,
    hasEnabledServices: true,
    enabledServiceNames: [],
    refreshSettings: vi.fn(),
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

function renderBulkLookup(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <BulkLookup />
    </MemoryRouter>,
  );
}

describe('BulkLookup — cross-feature prefill (command palette ⌘⇧B / send-to)', () => {
  it('appends a ?q= prefill value into the IOC input on mount', () => {
    renderBulkLookup(['/ioc-tools/bulk?q=185.220.101.7']);

    const input = screen.getByLabelText(/enter iocs/i);
    expect(input.value).toBe('185.220.101.7');
  });

  it('appends to, rather than replaces, any existing input', () => {
    renderBulkLookup(['/ioc-tools/bulk?q=185.220.101.7']);
    const input = screen.getByLabelText(/enter iocs/i);
    expect(input.value.trim().split('\n')).toEqual(['185.220.101.7']);
  });

  it('leaves the input empty with no prefill value', () => {
    renderBulkLookup(['/ioc-tools/bulk']);
    const input = screen.getByLabelText(/enter iocs/i);
    expect(input.value).toBe('');
  });
});
