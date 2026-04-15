import { useState, useMemo } from 'react';
import { filterServices } from '../../utils/settingsUtils';

export function useApiKeyFilters(servicesConfig) {
  const [searchFilter, setSearchFilter] = useState('');
  const [showOnlyConfigured, setShowOnlyConfigured] = useState(false);

  const filteredServices = useMemo(() => {
    return filterServices(servicesConfig, searchFilter, showOnlyConfigured);
  }, [servicesConfig, searchFilter, showOnlyConfigured]);

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
