"""Parse KiriKiri flowchart records without executing game logic."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    target: int
    route: int
    text: str


@dataclass(frozen=True)
class Node:
    id: int
    kind: str
    title: str
    choices: tuple[Choice, ...] = ()
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Edge:
    id: int
    source: int
    target: int


@dataclass(frozen=True)
class Flowchart:
    nodes: dict[int, Node]
    edges: dict[int, Edge]


def parse_flowchart(text: str) -> Flowchart:
    nodes = {}
    edges = {}
    for line_number, raw in enumerate(text.splitlines(), 1):
        if ";" not in raw:
            continue
        head, *fields = raw.split("'")
        identifier, sep, kind = head.partition(";")
        if not sep or not identifier.isdecimal() or kind not in {"SELECTER", "SCENE", "OUTERLABEL", "ROUTE"}:
            raise ValueError(f"Invalid flowchart record on line {line_number}")
        node_id = int(identifier)
        try:
            if int(fields[0]) != node_id:
                raise ValueError("record identifiers disagree")
            if kind == "ROUTE":
                edge = Edge(node_id, int(fields[-2]), int(fields[-1]))
                if node_id in edges:
                    raise ValueError("duplicate route")
                edges[node_id] = edge
                continue
            if node_id in nodes:
                raise ValueError("duplicate node")
            title = fields[9]
            choices = ()
            conditions = ()
            if kind == "SELECTER":
                total = int(fields[10])
                choices = tuple(Choice(int(fields[11 + 3*i]), int(fields[12 + 3*i]), fields[13 + 3*i]) for i in range(total))
            elif kind == "SCENE":
                total = int(fields[10])
                conditions = tuple(fields[11:11 + total])
                if len(conditions) != total:
                    raise ValueError("missing condition")
            nodes[node_id] = Node(node_id, kind, title, choices, conditions)
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Malformed flowchart record on line {line_number}: {exc}") from exc
    if not nodes:
        raise ValueError("Flowchart contains no nodes")
    for edge in edges.values():
        if edge.source not in nodes or edge.target not in nodes:
            raise ValueError(f"Route {edge.id} refers to an unknown node")
    for node in nodes.values():
        for choice in node.choices:
            edge = edges.get(choice.route)
            if edge is None or edge.source != node.id or edge.target != choice.target:
                raise ValueError(f"Choice route {choice.route} does not match its edge")
    return Flowchart(nodes, edges)
