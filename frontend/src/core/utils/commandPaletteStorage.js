/**
 * localStorage-backed state for the command palette: pinned tools, recents (one feed, capped),
 * typed-query history (separate from recents, capped), and recorded playbooks. Plain functions
 * over raw localStorage, same style as core/utils/accessToken.js — no framework dependency so
 * this stays testable without rendering anything.
 */

const PINNED_KEY = 'corvid_palette_pinned';
const RECENTS_KEY = 'corvid_palette_recents';
const HISTORY_KEY = 'corvid_palette_query_history';
const PLAYBOOKS_KEY = 'corvid_palette_playbooks';

const RECENTS_LIMIT = 8;
const HISTORY_LIMIT = 20;

// Pinned tools are read into local state by two independent component trees (LeftPanel and the
// command palette's own useCommandPalette hook) with no shared store between them — this event
// is how a pin/unpin from either side notifies the other without a page navigation in between.
export const PINNED_CHANGED_EVENT = 'corvid:pinned-changed';

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return parsed ?? fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

// --- Pinned tools ---

export function getPinnedToolIds() {
  return readJson(PINNED_KEY, []);
}

export function setPinnedToolIds(ids) {
  writeJson(PINNED_KEY, ids);
  window.dispatchEvent(new Event(PINNED_CHANGED_EVENT));
}

export function togglePinnedToolId(id) {
  const pinned = getPinnedToolIds();
  const next = pinned.includes(id) ? pinned.filter((p) => p !== id) : [...pinned, id];
  setPinnedToolIds(next);
  return next;
}

// --- Recents (one feed: tool opens + pivoted values) ---

export function getRecents() {
  return readJson(RECENTS_KEY, []);
}

/** entry: { type: 'tool' | 'value', toolId?, value?, iocType?, at } */
export function addRecent(entry) {
  const recents = getRecents();
  const withoutDuplicate = recents.filter((r) => !(r.type === entry.type
    && r.toolId === entry.toolId
    && r.value === entry.value));
  const next = [{ ...entry, at: Date.now() }, ...withoutDuplicate].slice(0, RECENTS_LIMIT);
  writeJson(RECENTS_KEY, next);
  return next;
}

export function clearRecents() {
  writeJson(RECENTS_KEY, []);
}

// --- Typed-query history (separate from recents) ---

export function getQueryHistory() {
  return readJson(HISTORY_KEY, []);
}

export function addQueryToHistory(query) {
  const trimmed = query.trim();
  if (!trimmed) return getQueryHistory();
  const history = getQueryHistory();
  const next = [trimmed, ...history.filter((q) => q !== trimmed)].slice(0, HISTORY_LIMIT);
  writeJson(HISTORY_KEY, next);
  return next;
}

export function clearQueryHistory() {
  writeJson(HISTORY_KEY, []);
}

// --- Playbooks: { name, steps: [toolId], createdAt }[] ---

export function getPlaybooks() {
  return readJson(PLAYBOOKS_KEY, []);
}

export function getPlaybook(name) {
  return getPlaybooks().find((p) => p.name === name) ?? null;
}

export function savePlaybook(name, steps) {
  const playbooks = getPlaybooks().filter((p) => p.name !== name);
  const next = [...playbooks, { name, steps, createdAt: Date.now() }];
  writeJson(PLAYBOOKS_KEY, next);
  return next;
}

export function renamePlaybook(oldName, newName) {
  const next = getPlaybooks().map((p) => (p.name === oldName ? { ...p, name: newName } : p));
  writeJson(PLAYBOOKS_KEY, next);
  return next;
}

export function deletePlaybook(name) {
  const next = getPlaybooks().filter((p) => p.name !== name);
  writeJson(PLAYBOOKS_KEY, next);
  return next;
}
