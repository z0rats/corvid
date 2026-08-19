import { screen } from '@testing-library/react';
import RedditSearch from './RedditSearch';
import { useRedditSearch } from './hooks/useRedditSearch';
import { renderFeatureRoute } from '../../core/testUtils/renderFeatureRoute';

vi.mock('./hooks/useRedditSearch');

const emptyTab = () => ({ items: [], sources: [], page: 1, hasMore: false, loading: false, error: null });

function renderRedditSearch(initialEntries) {
  return renderFeatureRoute(RedditSearch, 'reddit-search', initialEntries);
}

describe('RedditSearch — cross-feature prefill (command palette pivot)', () => {
  let search;

  beforeEach(() => {
    search = vi.fn();
    useRedditSearch.mockReturnValue({
      username: '', searchId: null, posts: emptyTab(), comments: emptyTab(),
      search, goNext: vi.fn(), goPrev: vi.fn(),
    });
  });

  afterEach(() => vi.clearAllMocks());

  it('preserves ?q= through the index -> new redirect and prefills the username field', () => {
    renderRedditSearch(['/reddit-search?q=john_doe']);

    expect(screen.getByLabelText(/username/i).value).toBe('john_doe');
  });

  it('auto-runs the search with the prefilled value', () => {
    renderRedditSearch(['/reddit-search?q=john_doe']);

    expect(search).toHaveBeenCalledWith('john_doe');
  });

  it('leaves the field empty and does not search with no prefill value', () => {
    renderRedditSearch(['/reddit-search']);

    expect(screen.getByLabelText(/username/i).value).toBe('');
    expect(search).not.toHaveBeenCalled();
  });
});
