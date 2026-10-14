import { useState, useMemo } from 'react';
import { filterServices } from '../../utils/settingsUtils';

// `focusKey` (a service key, e.g. from `?service=steam`) narrows the list to that one card -
// how "add API key" prompts elsewhere in the app link straight to the key they need.
export function useApiKeyFilters(servicesConfig, focusKey = null) {
  const [searchFilter, setSearchFilter] = useState('');
  const [showOnlyConfigured, setShowOnlyConfigured] = useState(false);

  const filteredServices = useMemo(() => {
    if (focusKey && servicesConfig[focusKey]) return [[focusKey, servicesConfig[focusKey]]];
    return filterServices(servicesConfig, searchFilter, showOnlyConfigured);
  }, [servicesConfig, searchFilter, showOnlyConfigured, focusKey]);

  const toggleShowOnlyConfigured = () => setShowOnlyConfigured(prev => !prev);

  const clearFilters = () => {
    setSearchFilter('');
    setShowOnlyConfigured(false);
  };

  return {
    searchFilter,
    showOnlyConfigured,
    filteredServices,
    updateSearchFilter: setSearchFilter,
    toggleShowOnlyConfigured,
    clearFilters,
  };
}
