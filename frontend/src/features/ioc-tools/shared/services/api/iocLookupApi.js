import api, { baseURL } from '../../../../../core/services/baseApi';
import { getAccessToken } from '../../../../../core/utils/accessToken';

/**
 * IOC Lookup API Service
 * Pure functions for IOC lookup operations - no React dependencies
 */
export const iocLookupApi = {
  async fetchServiceDefinitions() {
    const response = await api.get('/api/ioc/service-definitions');
    return response.data.serviceDefinitions || {};
  },

  async lookupSingleService(serviceKey, ioc, iocType, { signal } = {}) {
    const url = `/api/ioc/lookup/${serviceKey}?ioc=${encodeURIComponent(ioc)}&ioc_type=${encodeURIComponent(iocType)}`;
    const response = await api.get(url, { signal });
    return response.data;
  },

  async bulkLookup(iocs, services) {
    const response = await fetch(`${baseURL}/api/ioc-lookup/bulk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({ iocs, services })
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    return response.body;
  },

  async fetchBulkLookupSettings() {
    const response = await api.get('/api/apikeys/bulk_ioc_lookup');
    return response.data || {};
  },

  async updateBulkLookupSetting(keyName, enabled) {
    const response = await api.patch(`/api/apikeys/${keyName}/bulk_ioc_lookup`, { bulk_ioc_lookup: enabled });
    return response.data;
  },
};
