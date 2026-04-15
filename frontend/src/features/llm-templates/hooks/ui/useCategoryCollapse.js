import { useState, useCallback } from 'react';

import { SYSTEM_CATEGORY_IDS } from '../../constants/templateConstants';

const STORAGE_KEY = 'llm-templates-expanded-categories';

function loadExpandedCategories() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return new Set(JSON.parse(stored));
    }
  } catch {
    // ignore parse errors
  }
  return new Set([SYSTEM_CATEGORY_IDS.FAVORITES]);
}

function persistExpandedCategories(expanded) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...expanded]));
  } catch {
    // ignore storage errors
  }
}

export function useCategoryCollapse() {
  const [expandedCategories, setExpandedCategories] = useState(loadExpandedCategories);

  const toggleCategory = useCallback((categoryId) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      persistExpandedCategories(next);
      return next;
    });
  }, []);

  const isCategoryExpanded = useCallback((categoryId) => {
    return expandedCategories.has(categoryId);
  }, [expandedCategories]);

  return {
    expandedCategories,
    toggleCategory,
    isCategoryExpanded,
  };
}
