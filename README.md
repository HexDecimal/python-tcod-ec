# About

[![PyPI](https://img.shields.io/pypi/v/tcod-ec)](https://pypi.org/project/tcod-ec/)
[![PyPI - License](https://img.shields.io/pypi/l/tcod-ec)](https://github.com/HexDecimal/python-tcod-ec/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/python-tcod-ec/badge/?version=latest)](https://python-tcod-ec.readthedocs.io)
[![codecov](https://codecov.io/gh/HexDecimal/python-tcod-ec/branch/main/graph/badge.svg?token=UP161WEo0s)](https://codecov.io/gh/HexDecimal/python-tcod-ec)

Basic Entity/Component containers for implementing composition over inheritance.

`tcod.ec.ComponentDict` is a container of anonymous and abstract components.
The key is the class of the component and can only be assigned one instance of that class.

```py
>>> from attrs import define
>>> from tcod.ec import ComponentDict, abstract_component

# Anonymous components don't need special treatment.
>>> @define
... class Position:
...     x: int = 0
...     y: int = 0
>>> @define
... class Graphic:
...     ch: str = "@"
>>> entity = ComponentDict([Position(1, 2), Graphic("!")])
>>> (Position, Graphic) in entity  # Check if an entity has a set of components.
True
>>> entity[Position].y = 10  # Access components using the class as the key.
>>> entity[Position]
Position(x=1, y=10)
>>> entity[Graphic] = Graphic("?")  # Explicit setting of the component.
>>> entity
ComponentDict([Position(x=1, y=10), Graphic(ch='?')])
>>> entity.set(Graphic("#"))  # Implicit setting.
ComponentDict([Position(x=1, y=10), Graphic(ch='#')])
>>> del entity[Graphic]  # Components can be deleted.
>>> entity
ComponentDict([Position(x=1, y=10)])

# Abstract components can be registered with tcod.ec.abstract_component.
>>> @abstract_component
... @define
... class Base:
...     pass
>>> @define
... class Derived(Base):
...     pass
>>> entity.set(Derived())  # Derived classes may be set implicitly.
ComponentDict([Position(x=1, y=10), Derived()])
>>> entity[Base] = Derived()  # Or explicitly assigned to the abstract key.
>>> Base in entity
True
>>> entity[Base]  # Any derived classes use the base class as the key.
Derived()
>>> entity
ComponentDict([Position(x=1, y=10), Derived()])

```
