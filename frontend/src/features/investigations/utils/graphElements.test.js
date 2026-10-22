import { externalUrl, neighborsOf, nodeSize, toElements, typeCounts } from './graphElements';
import { FALLBACK_COLOR, ENTITY_TYPES } from '../constants/entityTypes';

const GRAPH = {
  nodes: [
    { id: 'username:jdoe', type: 'username', value: 'jdoe', label: 'jdoe', degree: 2, is_root: true, sources: [] },
    { id: 'subreddit:a', type: 'subreddit', value: 'a', label: 'r/a', degree: 1, is_root: false, sources: [] },
    { id: 'subreddit:b', type: 'subreddit', value: 'b', label: 'r/b', degree: 1, is_root: false, sources: [] },
    { id: 'thing:x', type: 'thing', value: 'x', label: 'x', degree: 0, is_root: false, sources: [] },
  ],
  edges: [
    { source: 'username:jdoe', target: 'subreddit:a', relation: 'active in', sources: [] },
  ],
};

describe('toElements', () => {
  it('maps nodes and edges with colour, size and root flag', () => {
    const [user, , , unknown, edge] = toElements(GRAPH);
    expect(user.data).toMatchObject({ id: 'username:jdoe', color: ENTITY_TYPES.username.color, root: 1 });
    expect(unknown.data.color).toBe(FALLBACK_COLOR);
    expect(edge).toEqual({
      group: 'edges',
      data: {
        id: 'username:jdoe|active in|subreddit:a',
        source: 'username:jdoe',
        target: 'subreddit:a',
        label: 'active in',
      },
    });
  });
});

describe('nodeSize', () => {
  it('grows with degree up to a cap', () => {
    expect(nodeSize(0)).toBeLessThan(nodeSize(4));
    expect(nodeSize(10_000)).toBe(54);
  });
});

describe('typeCounts', () => {
  it('orders the backend counts most frequent first, ties by name', () => {
    expect(typeCounts({ username: 1, thing: 1, subreddit: 2 })).toEqual([['subreddit', 2], ['thing', 1], ['username', 1]]);
    expect(typeCounts(undefined)).toEqual([]);
  });
});

describe('neighborsOf', () => {
  it('finds linked nodes in either direction', () => {
    expect(neighborsOf(GRAPH, 'subreddit:a').map((n) => n.id)).toEqual(['username:jdoe']);
    expect(neighborsOf(GRAPH, 'username:jdoe').map((n) => n.id)).toEqual(['subreddit:a']);
  });
});

describe('externalUrl', () => {
  it('only returns http(s) values', () => {
    expect(externalUrl({ value: 'https://github.com/jdoe' })).toBe('https://github.com/jdoe');
    expect(externalUrl({ value: 'https://github.com/jdoe', raw_value: 'https://github.com/JDoe' })).toBe('https://github.com/JDoe');
    expect(externalUrl({ value: 'spotify/jdoe@x.com' })).toBeNull();
    expect(externalUrl({ value: 'javascript:alert(1)' })).toBeNull();
  });
});
