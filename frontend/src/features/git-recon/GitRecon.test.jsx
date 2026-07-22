import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import GitRecon from './GitRecon';
import { useGitRecon } from './hooks/useGitRecon';

vi.mock('./hooks/useGitRecon');

// GitRecon owns its own nested <Routes> (index/new/history), same as it's mounted in the real app
// (routes.jsx's `path="git-recon/*"`) — mounting it bare under MemoryRouter without this wrapping
// route fails to match anything, since its own `index` route only matches an empty relative path
// once nested under a `/*` parent.
function renderGitRecon(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="git-recon/*" element={<GitRecon />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('GitRecon — cross-feature prefill (command palette pivot)', () => {
  let scan;

  beforeEach(() => {
    scan = vi.fn();
    useGitRecon.mockReturnValue({ result: null, loading: false, error: null, scan });
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect, prefills the target field, and switches to nickname mode', () => {
    renderGitRecon(['/git-recon?q=octocat']);

    expect(screen.getByLabelText(/github username/i).value).toBe('octocat');
  });

  it('auto-runs the scan in nickname mode with the prefilled value', () => {
    renderGitRecon(['/git-recon?q=octocat']);

    expect(scan).toHaveBeenCalledWith(expect.objectContaining({ mode: 'nickname', target: 'octocat' }));
  });

  it('leaves the field empty, defaults to search mode, and does not scan with no prefill value', () => {
    renderGitRecon(['/git-recon']);

    expect(scan).not.toHaveBeenCalled();
  });
});
