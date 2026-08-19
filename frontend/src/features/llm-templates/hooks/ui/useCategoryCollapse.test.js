import { act, renderHook } from '@testing-library/react';
import { useCategoryCollapse } from './useCategoryCollapse';
import { SYSTEM_CATEGORY_IDS } from '../../constants/templateConstants';

const STORAGE_KEY = 'llm-templates-expanded-categories';

describe('useCategoryCollapse', () => {
  beforeEach(() => localStorage.clear());

  it('starts with only the Favorites category expanded when nothing is persisted', () => {
    const { result } = renderHook(() => useCategoryCollapse());

    expect(result.current.isCategoryExpanded(SYSTEM_CATEGORY_IDS.FAVORITES)).toBe(true);
    expect(result.current.isCategoryExpanded('some-other-category')).toBe(false);
  });

  it('restores previously-expanded categories from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(['cat-1', 'cat-2']));

    const { result } = renderHook(() => useCategoryCollapse());

    expect(result.current.isCategoryExpanded('cat-1')).toBe(true);
    expect(result.current.isCategoryExpanded('cat-2')).toBe(true);
    expect(result.current.isCategoryExpanded(SYSTEM_CATEGORY_IDS.FAVORITES)).toBe(false);
  });

  it('falls back to the default when localStorage holds unparseable JSON', () => {
    localStorage.setItem(STORAGE_KEY, '{not valid json');

    const { result } = renderHook(() => useCategoryCollapse());

    expect(result.current.isCategoryExpanded(SYSTEM_CATEGORY_IDS.FAVORITES)).toBe(true);
  });

  it('toggleCategory expands a collapsed category and persists it', () => {
    const { result } = renderHook(() => useCategoryCollapse());

    act(() => result.current.toggleCategory('cat-1'));

    expect(result.current.isCategoryExpanded('cat-1')).toBe(true);
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toContain('cat-1');
  });

  it('toggleCategory collapses an expanded category and persists it', () => {
    const { result } = renderHook(() => useCategoryCollapse());

    act(() => result.current.toggleCategory(SYSTEM_CATEGORY_IDS.FAVORITES));

    expect(result.current.isCategoryExpanded(SYSTEM_CATEGORY_IDS.FAVORITES)).toBe(false);
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).not.toContain(
      SYSTEM_CATEGORY_IDS.FAVORITES,
    );
  });
});
