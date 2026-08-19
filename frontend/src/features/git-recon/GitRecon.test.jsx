import { screen } from '@testing-library/react';
import GitRecon from './GitRecon';
import { useGitRecon } from './hooks/useGitRecon';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useGitRecon');

function renderGitRecon(initialEntries) {
  return renderFeatureRoute(GitRecon, 'git-recon', initialEntries);
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
