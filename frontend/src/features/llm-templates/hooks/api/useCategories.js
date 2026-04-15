import { useState, useCallback, useEffect } from 'react';

import { categoriesApi } from '../../services/api/categoriesApi';
import { extractErrorMessage } from '../../../../core/utils/errorUtils';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('TemplateCategories');

export function useCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await categoriesApi.getCategories();
      setCategories(Array.isArray(data) ? data : []);
    } catch (err) {
      logger.error('Failed to fetch categories:', err);
      setError(extractErrorMessage(err));
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const createCategory = useCallback(async (name) => {
    const created = await categoriesApi.createCategory(name);
    setCategories(prev => [...prev, created]);
    return created;
  }, []);

  const updateCategory = useCallback(async (categoryId, name) => {
    const updated = await categoriesApi.updateCategory(categoryId, name);
    setCategories(prev => prev.map(c => c.id === categoryId ? updated : c));
    return updated;
  }, []);

  const deleteCategory = useCallback(async (categoryId, action) => {
    await categoriesApi.deleteCategory(categoryId, action);
    setCategories(prev => prev.filter(c => c.id !== categoryId));
  }, []);

  const reorderCategories = useCallback(async (sourceIndex, destinationIndex) => {
    const items = Array.from(categories);
    const [moved] = items.splice(sourceIndex, 1);
    items.splice(destinationIndex, 0, moved);
    setCategories(items);

    try {
      await categoriesApi.reorderCategories(items.map(c => c.id));
    } catch (err) {
      logger.error('Failed to reorder categories:', err);
      fetchCategories();
    }
  }, [categories, fetchCategories]);

  const moveTemplates = useCallback(async (templateIds, categoryId) => {
    await categoriesApi.moveTemplates(templateIds, categoryId);
  }, []);

  return {
    categories,
    setCategories,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    reorderCategories,
    moveTemplates,
  };
}
