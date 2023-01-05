from __future__ import annotations

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
