from app.core.entities import graph
from app.core.entities.graph import RunRef
from app.core.entities.model import Extraction, entity

A = RunRef("username_search", 1)
B = RunRef("ioc_lookup", 2)


def _extraction(root, *pairs, relation="rel"):
    out = Extraction(root=root)
    for target in pairs:
        out.link(root, target, relation)
    return out


def test_merge_dedupes_entities_and_links_and_keeps_provenance():
    user = entity("username", "jdoe")
    account = entity("account", "https://github.com/jdoe")
    merged = graph.merge(
        [
            (A, _extraction(user, account)),
            (B, _extraction(entity("username", "JDoe"), account)),
        ]
    )

    assert set(merged.nodes) == {"username:jdoe", "account:https://github.com/jdoe"}
    assert merged.nodes["username:jdoe"].sources == {A, B}
    assert merged.nodes["username:jdoe"].is_root
    assert not merged.nodes["account:https://github.com/jdoe"].is_root
    assert len(merged.edges) == 1
    assert next(iter(merged.edges.values())).sources == {A, B}
    assert merged.nodes["username:jdoe"].degree == 1


def test_root_without_links_is_still_a_node():
    merged = graph.merge([(A, Extraction(root=entity("ip", "1.2.3.4")))])
    assert list(merged.nodes) == ["ip:1.2.3.4"]
    assert merged.nodes["ip:1.2.3.4"].degree == 0


def test_filter_types_drops_nodes_and_their_edges():
    ip = entity("ip", "1.2.3.4")
    merged = graph.merge([(B, _extraction(ip, entity("asn", "AS1"), entity("domain", "x.com")))])

    filtered = graph.filter_types(merged, {"ip", "asn"})

    assert set(filtered.nodes) == {"ip:1.2.3.4", "asn:AS1"}
    assert [edge.target for edge in filtered.edges.values()] == ["asn:AS1"]
    assert filtered.total_nodes == 2
    assert filtered.nodes["ip:1.2.3.4"].degree == 1


def test_cap_keeps_roots_then_most_connected():
    hub = entity("username", "hub")
    leaves = [entity("account", f"https://site{i}.com/hub") for i in range(5)]
    lonely_root = entity("ip", "9.9.9.9")
    merged = graph.merge([(A, _extraction(hub, *leaves)), (B, Extraction(root=lonely_root))])

    capped = graph.cap(merged, max_nodes=3)

    assert capped.truncated
    assert capped.total_nodes == 7
    assert {"username:hub", "ip:9.9.9.9"} <= set(capped.nodes)
    assert len(capped.nodes) == 3
    assert all(e.source in capped.nodes and e.target in capped.nodes for e in capped.edges.values())


def test_cap_is_a_no_op_under_the_limit():
    merged = graph.merge([(A, Extraction(root=entity("ip", "1.1.1.1")))])
    assert not graph.cap(merged).truncated


def test_top_connected_orders_by_degree_and_skips_unlinked():
    hub = entity("username", "hub")
    merged = graph.merge(
        [
            (A, _extraction(hub, entity("subreddit", "a"), entity("subreddit", "b"))),
            (B, Extraction(root=entity("ip", "1.1.1.1"))),
        ]
    )

    top = graph.top_connected(merged, limit=2)

    assert [node.entity.id for node in top] == ["username:hub", "subreddit:a"]
