import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router';
import RuBusinessCheck from './RuBusinessCheck';
import { useRuBusinessCheck } from './hooks/useRuBusinessCheck';

vi.mock('./hooks/useRuBusinessCheck');

// RuBusinessCheck owns its own nested <Routes> (index/new/history/settings), same as it's
// mounted in the real app (routes.jsx's `path="ru-business-check/*"`) — mounting it bare under
// MemoryRouter without this wrapping route fails to match anything, since its own `index` route
// only matches an empty relative path once nested under a `/*` parent.
function renderRuBusinessCheck(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="ru-business-check/*" element={<RuBusinessCheck />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RuBusinessCheck — cross-feature prefill (command palette pivot)', () => {
  let scan;

  beforeEach(() => {
    scan = vi.fn();
    useRuBusinessCheck.mockReturnValue({ result: null, loading: false, error: null, scan });
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the query field', () => {
    renderRuBusinessCheck(['/ru-business-check?q=7712345678']);

    expect(screen.getByLabelText(/ИНН или название/i).value).toBe('7712345678');
  });

  it('auto-runs the scan with the prefilled value', () => {
    renderRuBusinessCheck(['/ru-business-check?q=7712345678']);

    expect(scan).toHaveBeenCalledWith({ query: '7712345678', force_refresh: false });
  });

  it('leaves the field empty and does not scan with no prefill value', () => {
    renderRuBusinessCheck(['/ru-business-check']);

    expect(scan).not.toHaveBeenCalled();
  });
});
