import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { usernameScanStateAtomFamily, buildInitialState } from '../state/scanAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchScan');

const TERMINAL_STATUSES = ['completed', 'cancelled', 'failed'];

const api = {
  startScan: (payload, { signal }) => usernameSearchApi.startScan(payload.username, {
    source: payload.source, tags: payload.tags, excludedTags: payload.excludedTags, signal,
  }),
  fetchPersisted: (searchId) => usernameSearchApi.getRun(searchId),
  cancelScan: (searchId) => usernameSearchApi.cancelScan(searchId),
};

// Sources whose "completed"/"cancelled" SSE events don't carry the found-site
// list inline (only counts) - social-analyzer has no per-site progress event to
// have accumulated it from, so it must be fetched from the persisted run instead.
async function fetchFoundSites(searchId) {
  try {
    const run = await usernameSearchApi.getRun(searchId);
    return run.site_results || [];
  } catch (err) {
    logger.error('Failed to fetch persisted site results:', err);
    return null;
  }
}

export async function reduce(prev, event) {
  const { data } = event;
  if (event.type === 'started') {
    return { ...prev, searchId: data.search_id, totalSites: data.total_sites };
  }
  if (event.type === 'progress') {
    return {
      ...prev,
      checked: data.checked,
      totalSites: data.total_sites,
      currentSite: data.site_name,
      foundSites: data.found
        ? [...prev.foundSites, { site_name: data.site_name, url_user: data.url_user }]
        : prev.foundSites,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const foundSites = await fetchFoundSites(data.search_id);
    return {
      ...prev,
      phase: event.type,
      checked: data.total_sites_checked,
      totalSites: data.total_sites_checked,
      searchId: data.search_id,
      foundSites: foundSites ?? prev.foundSites,
    };
  }
  if (event.type === 'failed') {
    return failedReduce(prev, event);
  }
  return prev;
}

export async function reconcile(prev, run) {
  return {
    ...prev,
    phase: run.status,
    checked: run.total_sites_checked,
    totalSites: run.total_sites_checked,
    foundSites: run.site_results || [],
    error: run.error_message || '',
  };
}

export function useUsernameSearchScan(source) {
  const [state, setState] = useAtom(usernameScanStateAtomFamily(source));

  const { startScan: resumableStartScan, cancelScan, reset } = useResumableScan({
    scopeKey: `username-search-${source}`,
    state,
    setState,
    initialState: buildInitialState(source),
    terminalStatuses: TERMINAL_STATUSES,
    api,
    reduce,
    reconcile,
  });

  const startScan = useCallback((username, options = {}) => resumableStartScan(
    { username, source, tags: options.tags, excludedTags: options.excludedTags },
    buildRunningSeed(buildInitialState(source), { username }),
  ), [resumableStartScan, source]);

  return { ...state, startScan, cancelScan, reset };
}
