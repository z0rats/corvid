import {
  getPinnedToolIds,
  togglePinnedToolId,
  getRecents,
  addRecent,
  clearRecents,
  getQueryHistory,
  addQueryToHistory,
  clearQueryHistory,
  getPlaybooks,
  getPlaybook,
  savePlaybook,
  renamePlaybook,
  deletePlaybook,
} from './commandPaletteStorage';

beforeEach(() => {
  localStorage.clear();
});

describe('pinned tools', () => {
  it('starts empty', () => {
    expect(getPinnedToolIds()).toEqual([]);
  });

  it('toggling pins and unpins a tool id', () => {
    expect(togglePinnedToolId('reddit_search')).toEqual(['reddit_search']);
    expect(getPinnedToolIds()).toEqual(['reddit_search']);
    expect(togglePinnedToolId('reddit_search')).toEqual([]);
    expect(getPinnedToolIds()).toEqual([]);
  });
});

describe('recents', () => {
  it('adds newest first', () => {
    addRecent({ type: 'tool', toolId: 'a' });
    addRecent({ type: 'tool', toolId: 'b' });
    const recents = getRecents();
    expect(recents.map((r) => r.toolId)).toEqual(['b', 'a']);
  });

  it('de-duplicates the same tool/value pair by moving it to the front', () => {
    addRecent({ type: 'tool', toolId: 'a' });
    addRecent({ type: 'tool', toolId: 'b' });
    addRecent({ type: 'tool', toolId: 'a' });
    expect(getRecents().map((r) => r.toolId)).toEqual(['a', 'b']);
    expect(getRecents()).toHaveLength(2);
  });

  it('caps at 8 entries', () => {
    for (let i = 0; i < 10; i += 1) {
      addRecent({ type: 'tool', toolId: `tool-${i}` });
    }
    expect(getRecents()).toHaveLength(8);
    expect(getRecents()[0].toolId).toBe('tool-9');
  });

  it('clearRecents empties the feed', () => {
    addRecent({ type: 'tool', toolId: 'a' });
    clearRecents();
    expect(getRecents()).toEqual([]);
  });
});

describe('query history', () => {
  it('adds newest first and trims whitespace', () => {
    addQueryToHistory('  8.8.8.8  ');
    addQueryToHistory('reddit');
    expect(getQueryHistory()).toEqual(['reddit', '8.8.8.8']);
  });

  it('ignores empty/whitespace-only queries', () => {
    addQueryToHistory('   ');
    expect(getQueryHistory()).toEqual([]);
  });

  it('de-duplicates by moving the repeated query to the front', () => {
    addQueryToHistory('reddit');
    addQueryToHistory('maigret');
    addQueryToHistory('reddit');
    expect(getQueryHistory()).toEqual(['reddit', 'maigret']);
  });

  it('caps at 20 entries', () => {
    for (let i = 0; i < 25; i += 1) {
      addQueryToHistory(`query-${i}`);
    }
    expect(getQueryHistory()).toHaveLength(20);
  });

  it('clearQueryHistory empties the list', () => {
    addQueryToHistory('reddit');
    clearQueryHistory();
    expect(getQueryHistory()).toEqual([]);
  });
});

describe('playbooks', () => {
  it('saves and retrieves a playbook by name', () => {
    savePlaybook('identity-triage', ['username_search', 'reddit_search']);
    const playbook = getPlaybook('identity-triage');
    expect(playbook.name).toBe('identity-triage');
    expect(playbook.steps).toEqual(['username_search', 'reddit_search']);
    expect(typeof playbook.createdAt).toBe('number');
  });

  it('returns null for a playbook that does not exist', () => {
    expect(getPlaybook('nope')).toBeNull();
  });

  it('saving with an existing name overwrites it', () => {
    savePlaybook('p1', ['a']);
    savePlaybook('p1', ['a', 'b']);
    expect(getPlaybooks()).toHaveLength(1);
    expect(getPlaybook('p1').steps).toEqual(['a', 'b']);
  });

  it('renames a playbook', () => {
    savePlaybook('old-name', ['a']);
    renamePlaybook('old-name', 'new-name');
    expect(getPlaybook('old-name')).toBeNull();
    expect(getPlaybook('new-name').steps).toEqual(['a']);
  });

  it('deletes a playbook', () => {
    savePlaybook('p1', ['a']);
    savePlaybook('p2', ['b']);
    deletePlaybook('p1');
    expect(getPlaybooks().map((p) => p.name)).toEqual(['p2']);
  });
});
