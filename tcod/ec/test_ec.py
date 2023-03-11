from __future__ import annotations

import copy
import pickle
from typing import Dict, Iterable, Type, TypeVar

import attrs
import pytest

import tcod.ec

T = TypeVar("T")


class ComponentDictNode(tcod.ec.ComponentDict):
    """Complex subclass for testing pickle."""

    __slots__ = ("children", "__dict__", "unset")

    def __init__(self, components: Iterable[object] = (), children: Iterable[ComponentDictNode] = ()) -> None:
        super().__init__(components)
        self.children = list(children)
        self.name = "Name"


class CompositeNode(tcod.ec.Composite):
    """Complex subclass for testing pickle."""

    __slots__ = ("__dict__", "unset")
    name: str


@tcod.ec.abstract_component
@attrs.define(frozen=True)
class Base:
    pass


@attrs.define(frozen=True)
class Derived(Base):
    pass


@attrs.define
class Abstract:
    value: Base


@attrs.define(frozen=True)
class Foo:
    pass


@attrs.define(frozen=True)
class Missing:
    pass


@attrs.define
class Recursive:
    entity: tcod.ec.ComponentDict | None = None


base = Base()
derived = Derived()
foo = Foo()


def test_ComponentDict() -> None:
    entity = tcod.ec.ComponentDict([derived, foo])
    assert Base in entity
    assert Foo in entity
    assert set(entity) == {Base, Foo}
    assert repr(entity) == "ComponentDict([Derived(), Foo()])"
    assert entity[Base] is derived
    assert entity[Foo] is foo
    assert len(entity) == 2
    with pytest.raises(KeyError):
        entity[Missing]
    with pytest.raises(TypeError):
        entity[Derived] = derived

    assert set(entity) == entity.keys() == {Base, Foo}
    assert set(entity.values()) == {derived, foo}
    assert set(zip(entity.keys(), entity.values())) == set(entity.items())

    entity = tcod.ec.ComponentDict()
    assert Base not in entity
    entity[Base] = derived
    assert entity[Base] is derived
    entity[Base] = base
    assert entity[Base] is base

    entity = tcod.ec.ComponentDict()
    entity.set(derived)
    assert entity[Base] is derived
    entity.set(base)
    assert entity[Base] is base
    del entity[Base]
    assert Base not in entity

    entity = tcod.ec.ComponentDict()
    assert entity.get(Base) is None
    entity[Base] = base
    assert entity.get(Base) is base

    assert entity.set() is entity

    entity = tcod.ec.ComponentDict([base])
    entity.clear()
    assert list(entity) == []


def test_ComponentDict_recursive() -> None:
    entity = tcod.ec.ComponentDict()
    entity.set(Recursive(entity))
    repr(entity)


def test_ComponentDict_pickle() -> None:
    entity = tcod.ec.ComponentDict([derived, foo])
    clone = pickle.loads(pickle.dumps(entity))
    assert repr(clone) == "ComponentDict([Derived(), Foo()])"


def test_ComponentDict_pickle_subclass() -> None:
    entity = ComponentDictNode([derived, foo], [ComponentDictNode([foo])])
    entity.name = "Top"
    clone: ComponentDictNode = pickle.loads(pickle.dumps(entity))
    assert clone.name == "Top"
    assert clone.children[0].name == "Name"
    assert repr(clone) == "ComponentDictNode([Derived(), Foo()])"

    clone = copy.copy(entity)
    clone.name = "Copy"
    assert entity.name != clone.name


def test_ComponentDict_unpickle_v1_1() -> None:
    # Makes sure v1.1 ComponentDict is unpicklable.
    ComponentDict_v1_1 = b"\x80\x04\x95r\x00\x00\x00\x00\x00\x00\x00\x8c\x07tcod.ec\x94\x8c\rComponentDict\x94\x93\x94)\x81\x94}\x94\x8c\x0b_components\x94}\x94(\x8c\nec.test_ec\x94\x8c\x04Base\x94\x93\x94h\x07\x8c\x07Derived\x94\x93\x94)\x81\x94}\x94bh\x07\x8c\x03Foo\x94\x93\x94h\x0f)\x81\x94}\x94busb."  # cspell: disable-line
    clone = pickle.loads(ComponentDict_v1_1)
    assert repr(clone) == "ComponentDict([Derived(), Foo()])"


def test_ComponentDict_unpickle_v2() -> None:
    ComponentDict_v2 = b"\x80\x04\x95h\x00\x00\x00\x00\x00\x00\x00\x8c\x07tcod.ec\x94\x8c\rComponentDict\x94\x93\x94)\x81\x94}\x94\x8c\x0b_components\x94\x8c\x0ftcod.ec.test_ec\x94\x8c\x07Derived\x94\x93\x94)\x81\x94}\x94bh\x06\x8c\x03Foo\x94\x93\x94)\x81\x94}\x94b\x86\x94sb."  # cspell: disable-line
    clone = pickle.loads(ComponentDict_v2)
    assert repr(clone) == "ComponentDict([Derived(), Foo()])"


def test_ComponentDict_copy() -> None:
    caught: Dict[tcod.ec.ComponentDict, Dict[Type[object], object]] = {}

    def _catch_components(entity: tcod.ec.ComponentDict, kind: Type[T], value: T | None, old_value: T | None) -> None:
        caught.setdefault(entity, {})
        caught[entity][kind] = value

    tcod.ec.ComponentDict.global_observers.append(_catch_components)
    try:
        original = tcod.ec.ComponentDict([Foo()])
        shallow = copy.copy(original)
        assert original[Foo] == shallow[Foo]
        assert original[Foo] is shallow[Foo]
        deep = copy.deepcopy(original)
        assert original[Foo] == deep[Foo]
        assert original[Foo] is not deep[Foo]

        # Copying triggers observable side-effects.
        assert Foo in caught[original]
        assert Foo in caught[shallow]
        assert Foo in caught[deep]
    finally:
        tcod.ec.ComponentDict.global_observers.remove(_catch_components)


def _migrate_derived(entity: tcod.ec.ComponentDict, key: Type[T], value: T | None, old_value: T | None) -> None:
    """Convert Base and Derived to being held by Abstract."""
    if isinstance(value, Base):
        entity.set(Abstract(value))
        del entity[key]


def test_abstract_migrate() -> None:
    tcod.ec.ComponentDict.global_observers.append(_migrate_derived)
    try:
        entity = tcod.ec.ComponentDict([derived])
        assert repr(entity) == "ComponentDict([Abstract(value=Derived())])"
    finally:
        tcod.ec.ComponentDict.global_observers.remove(_migrate_derived)


def test_Composite() -> None:
    entity = tcod.ec.Composite([base, derived])
    assert Base in entity
    assert {Base, Derived} in entity
    assert list(entity[Base]) == [base, derived]
    del entity[Base]
    assert not entity[Base]
    del entity[Base]
    entity.extend((base, derived, foo))
    assert tuple(entity[object]) == (base, derived, foo)
    entity.clear()
    assert tuple(entity[object]) == ()


def test_Composite_pickle() -> None:
    entity = tcod.ec.Composite([base, derived, foo])
    clone = pickle.loads(pickle.dumps(entity))
    assert repr(clone) == "Composite([Base(), Derived(), Foo()])"


def test_Composite_pickle_subclass() -> None:
    entity = CompositeNode([derived, foo])
    entity.name = "Top"
    clone: CompositeNode = pickle.loads(pickle.dumps(entity))
    assert clone.name == entity.name
    assert repr(clone) == "CompositeNode([Derived(), Foo()])"

    clone = copy.copy(entity)
    clone.name = "Copy"
    assert entity.name != clone.name


def test_Composite_unpickle_v2() -> None:
    Composite_v2 = b"\x80\x04\x95f\x00\x00\x00\x00\x00\x00\x00\x8c\x07tcod.ec\x94\x8c\tComposite\x94\x93\x94)\x81\x94}\x94\x8c\x0b_components\x94]\x94(\x8c\x0ftcod.ec.test_ec\x94\x8c\x07Derived\x94\x93\x94)\x81\x94}\x94bh\x07\x8c\x03Foo\x94\x93\x94)\x81\x94}\x94besb."  # cspell: disable-line
    clone = pickle.loads(Composite_v2)
    assert repr(clone) == "Composite([Derived(), Foo()])"
