import { useState, useMemo } from 'react';

export function useTemplateSearch(templates) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return templates;
    const term = search.toLowerCase().trim();
    return templates.filter(t =>
      t.title.toLowerCase().includes(term) ||
      (t.description && t.description.toLowerCase().includes(term))
    );
  }, [templates, search]);

  const isSearching = search.trim().length > 0;

  return { search, setSearch, filtered, isSearching };
}
