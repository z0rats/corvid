import { entityColor } from '../constants/entityTypes';

const MIN_SIZE = 18;
const MAX_SIZE = 54;

/** Node diameter grows with degree (sqrt, so a hub doesn't swamp the canvas). */
export function nodeSize(degree) {
  return Math.min(MAX_SIZE, MIN_SIZE + Math.sqrt(degree) * 8);
}

/** The backend's graph response as cytoscape elements. */
export function toElements(graph) {
  const nodes = graph.nodes.map((node) => ({
    group: 'nodes',
    data: {
      id: node.id,
      label: node.label,
      type: node.type,
      color: entityColor(node.type),
      size: nodeSize(node.degree),
      root: node.is_root ? 1 : 0,
    },
  }));
  const edges = graph.edges.map((edge) => ({
    group: 'edges',
    data: {
      id: `${edge.source}|${edge.relation}|${edge.target}`,
      source: edge.source,
      target: edge.target,
      label: edge.relation,
    },
  }));
  return [...nodes, ...edges];
}

/** The backend's `type_counts` as [type, count] pairs, most frequent first - the filter's chips. */
export function typeCounts(counts = {}) {
  return Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

/** An account/url node opens as the source gave it (`raw_value`; `value` is normalized and
 * lowercases account URLs) when that is an http(s) URL. */
export function externalUrl(node) {
  const url = node.raw_value ?? node.value;
  return /^https?:\/\//i.test(url) ? url : null;
}

/** Nodes linked to `nodeId`, in either direction. */
export function neighborsOf(graph, nodeId) {
  const ids = new Set();
  for (const edge of graph.edges) {
    if (edge.source === nodeId) ids.add(edge.target);
    if (edge.target === nodeId) ids.add(edge.source);
  }
  return graph.nodes.filter((node) => ids.has(node.id));
}
