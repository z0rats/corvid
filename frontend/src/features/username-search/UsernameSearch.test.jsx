import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import UsernameSearch from './UsernameSearch';
import { useUsernameSearchScan } from './hooks/useUsernameSearchScan';
import { usernameSearchApi } from './services/api/usernameSearchApi';

vi.mock('./hooks/useUsernameSearchScan');
vi.mock('./services/api/usernameSearchApi');

// UsernameSearch owns its own nested <Routes> (index/new/history/settings), same as it's mounted
// in the real app (routes.jsx's `path="username-search/*"`) — mounting it bare under MemoryRouter
// without this wrapping route fails to match anything, since its own `index` route only matches
// an empty relative path once nested under a `/*` parent.
function renderUsernameSearch(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="username-search/*" element={<UsernameSearch />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('UsernameSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    useUsernameSearchScan.mockReturnValue({ phase: 'idle', startScan, cancelScan: vi.fn(), reset: vi.fn() });
    usernameSearchApi.getTags = vi.fn().mockResolvedValue([]);
    usernameSearchApi.getInfo = vi.fn().mockResolvedValue([]);
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderUsernameSearch(['/username-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderUsernameSearch(['/username-search?q=john_doe']);

    expect(startScan).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderUsernameSearch(['/username-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
