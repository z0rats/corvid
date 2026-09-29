// Pure radial-layout computation for FriendGraphSvg.jsx, kept separate from the component so the
// geometry is unit-testable with no rendering involved.
//
// The target sits at the center; each friend sits on a circle around it, evenly spaced by angle,
// ordered and capped by mutual-connection weight (the closer the friend, the sooner it's placed
// and the bigger it's drawn) - only a star topology (target <-> friend), since a friend's mutual
// weight with the *target* is all the data collect_friend_graph produces; there's no pairwise
// friend-to-friend edge to draw.

export const MAX_GRAPH_NODES = 15;
export const LABEL_MAX_CHARS = 10;

// Extra headroom beyond FRIEND_RADIUS_FROM_CENTER + a node's own radius, reserved for that
// node's label sitting just outside it - sized so LABEL_MAX_CHARS' worth of text at the label
// font size fits before the viewBox edge (see FriendGraphSvg.jsx's fontSize).
const LABEL_MARGIN = 60;

const VIEWBOX_SIZE = 400 + 2 * LABEL_MARGIN;
const CENTER = VIEWBOX_SIZE / 2;
const FRIEND_RADIUS_FROM_CENTER = 160;
const TARGET_NODE_RADIUS = 26;
const MIN_FRIEND_NODE_RADIUS = 10;
const MAX_FRIEND_NODE_RADIUS = 22;
const LABEL_OFFSET_FROM_NODE = 12;

/** Truncates a friend's label the same way the target's own label already was. */
function truncateLabel(label) {
  const text = label || '';
  return text.length > LABEL_MAX_CHARS ? `${text.slice(0, LABEL_MAX_CHARS - 1)}…` : text;
}

export function layoutFriendGraph(closeFriends, targetLabel) {
  const friends = [...closeFriends]
    .sort((a, b) => b.mutual_count - a.mutual_count)
    .slice(0, MAX_GRAPH_NODES);

  const maxMutual = Math.max(1, ...friends.map((f) => f.mutual_count));

  const nodes = friends.map((friend, i) => {
    const angle = (2 * Math.PI * i) / friends.length - Math.PI / 2;
    const weightRatio = friend.mutual_count / maxMutual;
    const radius = MIN_FRIEND_NODE_RADIUS + weightRatio * (MAX_FRIEND_NODE_RADIUS - MIN_FRIEND_NODE_RADIUS);
    const labelDistance = FRIEND_RADIUS_FROM_CENTER + radius + LABEL_OFFSET_FROM_NODE;
    // Label sits further out along the same spoke as the node itself (radiating outward from
    // the target), rather than a fixed "below" offset - that keeps it clear of both the center
    // hub and neighboring spokes regardless of which side of the circle the node falls on.
    const label = truncateLabel(friend.persona_name || friend.steamid64);
    return {
      id: friend.steamid64,
      label,
      x: CENTER + FRIEND_RADIUS_FROM_CENTER * Math.cos(angle),
      y: CENTER + FRIEND_RADIUS_FROM_CENTER * Math.sin(angle),
      labelX: CENTER + labelDistance * Math.cos(angle),
      labelY: CENTER + labelDistance * Math.sin(angle),
      // A label past the 3/9 o'clock spokes needs to grow away from the node (start/end anchor)
      // rather than centering on its anchor point, or it overlaps the node/hub on that side.
      labelAnchor: Math.cos(angle) > 0.3 ? 'start' : Math.cos(angle) < -0.3 ? 'end' : 'middle',
      radius,
      mutualCount: friend.mutual_count,
      banned: Boolean(friend.vac_banned || friend.game_banned),
      avatarUrl: friend.avatar_url,
    };
  });

  return {
    viewBoxSize: VIEWBOX_SIZE,
    target: { id: 'target', label: targetLabel, x: CENTER, y: CENTER, radius: TARGET_NODE_RADIUS },
    nodes,
    edges: nodes.map((n) => ({ id: n.id, x1: CENTER, y1: CENTER, x2: n.x, y2: n.y, weightRatio: n.mutualCount / maxMutual })),
  };
}
