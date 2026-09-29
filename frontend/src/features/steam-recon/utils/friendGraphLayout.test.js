import { LABEL_MAX_CHARS, MAX_GRAPH_NODES, layoutFriendGraph } from './friendGraphLayout';

function friend(steamid64, mutualCount, overrides = {}) {
  return { steamid64, mutual_count: mutualCount, persona_name: steamid64, ...overrides };
}

describe('layoutFriendGraph', () => {
  it('returns an empty node/edge list for no friends', () => {
    const result = layoutFriendGraph([], 'target');

    expect(result.nodes).toEqual([]);
    expect(result.edges).toEqual([]);
    expect(result.target.label).toBe('target');
  });

  it('caps the number of nodes drawn', () => {
    const friends = Array.from({ length: 30 }, (_, i) => friend(`f${i}`, i));

    const result = layoutFriendGraph(friends, 'target');

    expect(result.nodes).toHaveLength(MAX_GRAPH_NODES);
  });

  it('keeps the highest-mutual-count friends when capping', () => {
    const friends = Array.from({ length: 30 }, (_, i) => friend(`f${i}`, i));

    const result = layoutFriendGraph(friends, 'target');

    const keptIds = result.nodes.map((n) => n.id);
    expect(keptIds).toContain('f29');
    expect(keptIds).not.toContain('f0');
  });

  it('gives every node a distinct position on a circle around the center', () => {
    const friends = [friend('a', 1), friend('b', 1), friend('c', 1)];

    const result = layoutFriendGraph(friends, 'target');

    const positions = result.nodes.map((n) => `${n.x.toFixed(2)},${n.y.toFixed(2)}`);
    expect(new Set(positions).size).toBe(3);
    for (const n of result.nodes) {
      const dx = n.x - result.target.x;
      const dy = n.y - result.target.y;
      expect(Math.hypot(dx, dy)).toBeCloseTo(160, 1);
    }
  });

  it('scales node radius by relative mutual-connection weight', () => {
    const friends = [friend('weak', 1), friend('strong', 10)];

    const result = layoutFriendGraph(friends, 'target');

    const weak = result.nodes.find((n) => n.id === 'weak');
    const strong = result.nodes.find((n) => n.id === 'strong');
    expect(strong.radius).toBeGreaterThan(weak.radius);
  });

  it('creates one edge per node, from the target to that friend', () => {
    const friends = [friend('a', 5)];

    const result = layoutFriendGraph(friends, 'target');

    expect(result.edges).toHaveLength(1);
    expect(result.edges[0]).toMatchObject({ x1: result.target.x, y1: result.target.y, x2: result.nodes[0].x, y2: result.nodes[0].y });
  });

  it('flags banned friends on their node', () => {
    const friends = [friend('a', 1, { vac_banned: true }), friend('b', 1, { game_banned: true }), friend('c', 1)];

    const result = layoutFriendGraph(friends, 'target');

    expect(result.nodes.find((n) => n.id === 'a').banned).toBe(true);
    expect(result.nodes.find((n) => n.id === 'b').banned).toBe(true);
    expect(result.nodes.find((n) => n.id === 'c').banned).toBe(false);
  });

  it('does not divide by zero when every friend has zero mutual count', () => {
    const friends = [friend('a', 0), friend('b', 0)];

    const result = layoutFriendGraph(friends, 'target');

    for (const n of result.nodes) {
      expect(Number.isFinite(n.radius)).toBe(true);
    }
  });

  it('keeps a friend persona name as-is when it fits', () => {
    const result = layoutFriendGraph([friend('a', 1, { persona_name: 'Robin' })], 'target');
    expect(result.nodes[0].label).toBe('Robin');
  });

  it('truncates a long persona name with an ellipsis', () => {
    const result = layoutFriendGraph(
      [friend('a', 1, { persona_name: 'a-very-long-steam-display-name' })],
      'target',
    );
    expect(result.nodes[0].label).toHaveLength(LABEL_MAX_CHARS);
    expect(result.nodes[0].label.endsWith('…')).toBe(true);
  });

  it('falls back to the steamid64 when there is no persona name', () => {
    const result = layoutFriendGraph([friend('76561197960435530', 1, { persona_name: null })], 'target');
    expect(result.nodes[0].label.startsWith('7656119')).toBe(true);
  });

  it('places every label further from the center than its own node', () => {
    const friends = [friend('a', 1), friend('b', 1), friend('c', 1), friend('d', 1)];

    const result = layoutFriendGraph(friends, 'target');

    for (const n of result.nodes) {
      const nodeDist = Math.hypot(n.x - result.target.x, n.y - result.target.y);
      const labelDist = Math.hypot(n.labelX - result.target.x, n.labelY - result.target.y);
      expect(labelDist).toBeGreaterThan(nodeDist + n.radius);
    }
  });

  it('picks a label anchor that grows text away from the hub on either side', () => {
    // 4 evenly-spaced spokes starting at -90deg (top): index 1 lands on the right (angle 0),
    // index 3 on the left (angle 180) - see the angle formula in layoutFriendGraph.
    const friends = [friend('top', 1), friend('right', 1), friend('bottom', 1), friend('left', 1)];

    const result = layoutFriendGraph(friends, 'target');

    const byId = Object.fromEntries(result.nodes.map((n) => [n.id, n]));
    expect(byId.right.labelAnchor).toBe('start');
    expect(byId.left.labelAnchor).toBe('end');
  });

  it('keeps every label position within the viewBox for a full ring of friends', () => {
    const friends = Array.from({ length: MAX_GRAPH_NODES }, (_, i) => friend(`f${i}`, i + 1));

    const result = layoutFriendGraph(friends, 'target');

    for (const n of result.nodes) {
      expect(n.labelX).toBeGreaterThanOrEqual(0);
      expect(n.labelX).toBeLessThanOrEqual(result.viewBoxSize);
      expect(n.labelY).toBeGreaterThanOrEqual(0);
      expect(n.labelY).toBeLessThanOrEqual(result.viewBoxSize);
    }
  });
});
