import api from '../../../../../core/services/baseApi';
import { openSseStream } from '../../../../../core/services/sseStream';

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

  async fetchNewsfeedMentions(ioc, { signal } = {}) {
    const response = await api.get('/api/ioc/newsfeed-mentions', { params: { ioc }, signal });
    return response.data;
  },

  bulkLookup(iocs, services, { signal } = {}) {
    return openSseStream('/api/ioc-lookup/bulk', { body: { iocs, services }, signal });
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
