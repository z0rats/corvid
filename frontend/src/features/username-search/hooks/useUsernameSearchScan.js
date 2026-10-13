import { useCallback } from 'react';
import { useAtom } from 'jotai';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { usernameScanStateAtomFamily, buildInitialState } from '../state/scanAtoms';
import { useResumableScan, failedReduce, buildRunningSeed } from '../../../core/hooks/useResumableScan';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchScan');

// The terminal SSE event carries counts only: the found-site list (social-analyzer has no
// per-site progress events to accumulate it from) and the backend-computed pivots both come
// from the persisted run.
async function fetchRun(searchId) {
  try {
    return await usernameSearchApi.getRun(searchId);
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
      // A one-site check needs the per-site verdict: "unknown" (blocked/failed) is not "not found".
      siteStatuses: prev.source === 'site_check'
        ? { ...prev.siteStatuses, [data.site_name]: data.status }
        : prev.siteStatuses,
      foundSites: data.found
        ? [...prev.foundSites, { site_name: data.site_name, url_user: data.url_user }]
        : prev.foundSites,
    };
  }
  if (event.type === 'completed' || event.type === 'cancelled') {
    const run = await fetchRun(data.search_id);
    return {
      ...prev,
      phase: event.type,
      checked: data.total_sites_checked,
      totalSites: data.total_sites_checked,
      searchId: data.search_id,
      foundSites: run ? run.site_results || [] : prev.foundSites,
      pivots: run?.pivots ?? prev.pivots,
      siteStatuses: run?.site_statuses ?? prev.siteStatuses,
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
    username: run.username ?? prev.username,
    checked: run.total_sites_checked,
    totalSites: run.total_sites_checked,
    foundSites: run.site_results || [],
    pivots: run.pivots ?? null,
    // A site check's verdicts are persisted, so a reload still tells "blocked" from "not found".
    siteStatuses: run.site_statuses ?? prev.siteStatuses,
    siteNames: run.site_statuses ? Object.keys(run.site_statuses) : prev.siteNames,
    error: run.error_message || '',
  };
}

// `site_check` is a Maigret run restricted to named sites (confirming one pivot) - its own route
// and rate limit, and its own state so it never collides with a Maigret scan on the panel.
const SITE_CHECK_SOURCE = 'site_check';

function buildScanBody(source, username, options) {
  const provenance = { parent_search_id: options.parentSearchId, pivot_source: options.pivotSource };
  if (source === SITE_CHECK_SOURCE) {
    return { username, site_names: options.siteNames, ...provenance };
  }
  return {
    username,
    source,
    tags: options.tags?.length ? options.tags : undefined,
    excluded_tags: options.excludedTags?.length ? options.excludedTags : undefined,
    ...provenance,
  };
}

export function useUsernameSearchScan(source) {
  const [state, setState] = useAtom(usernameScanStateAtomFamily(source));

  const { startScan: resumableStartScan, cancelScan, reset } = useResumableScan({
    scopeKey: `username-search-${source}`,
    state,
    setState,
    initialState: buildInitialState(source),
    endpoint: {
      base: '/api/username-search',
      runs: 'runs',
      scanPath: source === SITE_CHECK_SOURCE ? 'scan/site-check' : 'scan',
    },
    reduce,
    reconcile,
  });

  const startScan = useCallback((username, options = {}) => resumableStartScan(
    buildScanBody(source, username, options),
    buildRunningSeed(buildInitialState(source), { username, siteNames: options.siteNames ?? [] }),
  ), [resumableStartScan, source]);

  return { ...state, startScan, cancelScan, reset };
}
