from __future__ import annotations

import functools
import itertools
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class NotAChild(Exception):
    ...


def children_required(method):
    @functools.wraps(method)
    def wrapper(self: Node, *args, **kwargs):
        if self.has_children is True:
            return method(self, *args, **kwargs)

    return wrapper


def child_existence_required(method):
    @functools.wraps(method)
    def wrapper(self: Node, child: Node, *args, **kwargs):
        if self.has_as_child(child.name):
            return method(self, child, *args, **kwargs)

        msg = f"The node {child.name!r} is not a child of the parent node {self.name!r}"
        raise NotAChild(msg)

    return wrapper


class NodeType(Enum):
    DOCUMENT = 1
    ELEMENT = 2
    ATTRIBUTE = 3
    PI = 4
    COMMENT = 5
    TEXT = 6


@dataclass
class _childrenlist:
    head: Node | None = None
    tail: Node | None = None

    def __post_init__(self):
        self._temp_head = self.head

    def isempty(self) -> bool:
        return self.head is None and self.tail is None

    def __iter__(self):
        self._tmp_head = self.head
        return self

    def __next__(self) -> Node:
        if self._tmp_head is not None:
            node = self._tmp_head
            self._tmp_head = self._tmp_head.next
            return node
        raise StopIteration()

    def append(self, node: Node):
        node.prev = self.tail

        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node

        self.tail = node
        node.next = None

    def insert_before(self, ref: Node, new: Node):
        new.next = ref
        new.prev = ref.prev
        ref.prev = new

        if new.prev is not None:
            new.prev.next = new

        if ref is self.head:
            self.head = new

    def delete(self, node: Node):
        if node is not self.head:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node is not self.tail:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        del node


class Node:
    _count: ClassVar = itertools.count()

    def __init__(
        self,
        node_type: NodeType = NodeType.ELEMENT,
        parent: Node | None = None,
    ) -> None:
        self.node_type = node_type
        self.parent = parent
        self.prev: Node | None = None
        self.next: Node | None = None
        self.name = self.make_name()
        self.children = _childrenlist()
        self._cmap: dict[str, Node] = {}

    def __repr__(self) -> str:
        attrs = f"node_type={self.node_type}, name={self.name}"
        return f"{self.__class__.__name__}({attrs})"

    def make_name(self) -> str:
        count = next(Node._count)
        cls = self.__class__.__name__.lower()
        return f"{cls}_{count}"

    @property
    def has_children(self) -> bool:
        return not self.children.isempty()

    @property
    @children_required
    def first_child(self) -> Node | None:
        children = iter(self.children)
        return next(children)

    @property
    def previous_sibling(self) -> Node | None:
        return None or self.prev

    @property
    def next_sibling(self) -> Node | None:
        return None or self.next

    def has_as_child(self, node: str | Node) -> bool:
        if isinstance(node, Node):
            node = node.name
        return node in self._cmap

    def fetch_child_by_name(self, name: str) -> Node | None:
        return self._cmap.get(name)

    def insert_before(self, new: Node, ref: Node | None = None) -> Node:
        inserted = False

        if ref is None:
            self.children.append(new)
            inserted = True
        elif self.has_as_child(ref.name):
            self.children.insert_before(ref, new)
            inserted = True

        if inserted is True:
            self._cmap[new.name] = new
            return new

        msg = f"The node {ref.name!r} is not a child of the parent node {self.name!r}."
        raise NotAChild(msg)

    @child_existence_required
    def replace_child(self, old: Node, new: Node) -> Node:
        self.children.insert_before(old, new)
        self._cmap[new.name] = new

        self.children.delete(old)
        self._cmap.pop(old.name)

        return old

    @child_existence_required
    def remove_child(self, child: Node) -> Node:
        self.children.delete(child)
        self._cmap.pop(child.name)
        return child
