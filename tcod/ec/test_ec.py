from __future__ import annotations

import pickle

import attrs
import pytest

import tcod.ec


@tcod.ec.abstract_component
@attrs.define
class Base:
    pass


@attrs.define
class Derived(Base):
    pass


@attrs.define
class Foo:
    pass


@attrs.define
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


def test_ComponentDict_recursive() -> None:
    entity = tcod.ec.ComponentDict()
    entity.set(Recursive(entity))
    repr(entity)


def test_ComponentDict_pickle() -> None:
    entity = tcod.ec.ComponentDict([derived, foo])
    clone = pickle.loads(pickle.dumps(entity))
    assert repr(clone) == "ComponentDict([Derived(), Foo()])"


def test_ComponentDict_unpickle_v1_1() -> None:
    # Makes sure v1.1 ComponentDict is unpicklable.
    ComponentDict_v1_1 = b"\x80\x04\x95r\x00\x00\x00\x00\x00\x00\x00\x8c\x07tcod.ec\x94\x8c\rComponentDict\x94\x93\x94)\x81\x94}\x94\x8c\x0b_components\x94}\x94(\x8c\nec.test_ec\x94\x8c\x04Base\x94\x93\x94h\x07\x8c\x07Derived\x94\x93\x94)\x81\x94}\x94bh\x07\x8c\x03Foo\x94\x93\x94h\x0f)\x81\x94}\x94busb."
    clone = pickle.loads(ComponentDict_v1_1)
    assert repr(clone) == "ComponentDict([Derived(), Foo()])"
