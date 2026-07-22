import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import EmailSearch from './EmailSearch';
import { useEmailSearchScan } from './hooks/useEmailSearchScan';
import { emailSearchApi } from './services/api/emailSearchApi';

vi.mock('./hooks/useEmailSearchScan');
vi.mock('./services/api/emailSearchApi');

// EmailSearch owns its own nested <Routes> (index/new/history/settings), same as it's mounted in
// the real app (routes.jsx's `path="email-search/*"`) — mounting it bare under MemoryRouter
// without this wrapping route fails to match anything, since its own `index` route only matches
// an empty relative path once nested under a `/*` parent.
function renderEmailSearch(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="email-search/*" element={<EmailSearch />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('EmailSearch — cross-feature prefill (command palette pivot)', () => {
  let startScan;

  beforeEach(() => {
    startScan = vi.fn();
    useEmailSearchScan.mockReturnValue({ phase: 'idle', startScan, cancelScan: vi.fn(), reset: vi.fn() });
    emailSearchApi.getInfo = vi.fn().mockResolvedValue(null);
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderEmailSearch(['/email-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderEmailSearch(['/email-search?q=john_doe']);

    expect(startScan).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderEmailSearch(['/email-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(startScan).not.toHaveBeenCalled();
  });
});
