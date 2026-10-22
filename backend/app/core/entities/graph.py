"""Merge per-run extractions into one graph: dedupe entities by id, dedupe links by
(source, target, relation), and keep which runs produced each."""

from collections import Counter
from collections.abc import Collection, Iterable
from dataclasses import dataclass, field

from app.core.entities.model import Entity, Extraction

# Past this many nodes the graph keeps the most connected ones - see ADR 0028.
MAX_GRAPH_NODES = 300


@dataclass(frozen=True)
class RunRef:
    feature: str
    run_id: int


@dataclass
class GraphNode:
    entity: Entity
    sources: set[RunRef] = field(default_factory=set)
    degree: int = 0
    is_root: bool = False


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    sources: set[RunRef] = field(default_factory=set)


@dataclass
class Graph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[tuple[str, str, str], GraphEdge] = field(default_factory=dict)
    total_nodes: int = 0
    truncated: bool = False
    # Entities per type in the whole merged graph - before any type filter or cap, so a filter
    # can offer (and count) a type the cap left out entirely.
    type_counts: dict[str, int] = field(default_factory=dict)


def _add_node(graph: Graph, entity: Entity, ref: RunRef) -> GraphNode:
    node = graph.nodes.get(entity.id)
    if node is None:
        node = graph.nodes[entity.id] = GraphNode(entity)
    node.sources.add(ref)
    return node


def merge(extractions: Iterable[tuple[RunRef, Extraction]]) -> Graph:
    graph = Graph()
    for ref, extraction in extractions:
        if extraction.root is not None:
            _add_node(graph, extraction.root, ref).is_root = True
        for item in extraction.entities:
            _add_node(graph, item, ref)
        for link in extraction.links:
            key = (link.source.id, link.target.id, link.relation)
            edge = graph.edges.get(key)
            if edge is None:
                edge = graph.edges[key] = GraphEdge(*key)
            edge.sources.add(ref)
    _recount_degrees(graph)
    graph.total_nodes = len(graph.nodes)
    graph.type_counts = dict(Counter(node.entity.type for node in graph.nodes.values()))
    return graph


def _recount_degrees(graph: Graph) -> None:
    for node in graph.nodes.values():
        node.degree = 0
    for edge in graph.edges.values():
        graph.nodes[edge.source].degree += 1
        graph.nodes[edge.target].degree += 1


def _keep(graph: Graph, node_ids: Collection[str]) -> None:
    graph.nodes = {id_: node for id_, node in graph.nodes.items() if id_ in node_ids}
    graph.edges = {
        key: edge
        for key, edge in graph.edges.items()
        if edge.source in graph.nodes and edge.target in graph.nodes
    }
    _recount_degrees(graph)


def filter_types(graph: Graph, types: Collection[str] | None) -> Graph:
    """Drop entities whose type isn't in `types` (and their links). `None` keeps everything."""
    if types is not None:
        _keep(graph, {id_ for id_, node in graph.nodes.items() if node.entity.type in types})
    graph.total_nodes = len(graph.nodes)
    return graph


def cap(graph: Graph, max_nodes: int | None = None) -> Graph:
    """Keep at most `max_nodes` (default `MAX_GRAPH_NODES`): roots first, then by degree (ties
    by id, so it's stable)."""
    if max_nodes is None:
        max_nodes = MAX_GRAPH_NODES
    if len(graph.nodes) <= max_nodes:
        return graph
    ranked = sorted(
        graph.nodes.values(), key=lambda node: (not node.is_root, -node.degree, node.entity.id)
    )
    _keep(graph, {node.entity.id for node in ranked[:max_nodes]})
    graph.truncated = True
    return graph


def top_connected(graph: Graph, limit: int = 10) -> list[GraphNode]:
    """The most linked entities, for the report's summary. Unlinked ones never qualify."""
    linked = [node for node in graph.nodes.values() if node.degree > 0]
    return sorted(linked, key=lambda node: (-node.degree, node.entity.id))[:limit]
