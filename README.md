# About

[![PyPI](https://img.shields.io/pypi/v/tcod-ec)](https://pypi.org/project/tcod-ec/)
[![PyPI - License](https://img.shields.io/pypi/l/tcod-ec)](https://github.com/HexDecimal/python-tcod-ec/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/python-tcod-ec/badge/?version=latest)](https://python-tcod-ec.readthedocs.io)
[![codecov](https://codecov.io/gh/HexDecimal/python-tcod-ec/branch/main/graph/badge.svg?token=UP161WEo0s)](https://codecov.io/gh/HexDecimal/python-tcod-ec)

Entity/Component containers for implementing composition over inheritance.

# Installation

Use pip to install this library:
```
pip install tcod-ec
```

If `tcod` is installed and the version is less than `14.0.0` then `import tcod.ec` will fail.
Remove or update `tcod` to fix this issue.

# Examples

`tcod.ec.ComponentDict` is a container for anonymous components all with a unique class.
The key is the class of the component and can only be assigned one instance of that class.

```py
>>> import attrs
>>> import tcod.ec

# Anonymous components don't need special treatment.
>>> @attrs.define
... class Position:
...     x: int = 0
...     y: int = 0
>>> @attrs.define
... class Graphic:
...     ch: str = "@"

# ComponentDict stores a single instance for every unique class, in this case: [str, Position, Graphic]
>>> entity = tcod.ec.ComponentDict(["Hello world", Position(1, 2), Graphic("!")])
>>> {Position, Graphic} in entity  # Check if an entity has a set of components.
True
>>> entity[str]  # Access components using the class as the key.
'Hello world'
>>> entity[Position].y = 10
>>> entity[Position]
Position(x=1, y=10)
>>> entity[Graphic] = Graphic("?")  # Explicit setting of the component.
>>> entity
ComponentDict(['Hello world', Position(x=1, y=10), Graphic(ch='?')])
>>> entity.set(Graphic("#"))  # Implicit setting.
ComponentDict(['Hello world', Position(x=1, y=10), Graphic(ch='#')])
>>> del entity[Graphic]  # Components can be deleted.
>>> entity
ComponentDict(['Hello world', Position(x=1, y=10)])

# Abstract components can be registered with tcod.ec.abstract_component.
>>> @tcod.ec.abstract_component
... @attrs.define
... class Base:
...     pass
>>> @attrs.define
... class Derived(Base):
...     pass
>>> entity.set(Derived())  # Derived classes may be set implicitly.
ComponentDict(['Hello world', Position(x=1, y=10), Derived()])
>>> entity[Base] = Derived()  # Or explicitly assigned to the abstract key.
>>> Base in entity
True
>>> entity[Base]  # Any derived classes use the base class as the key.
Derived()
>>> entity
ComponentDict(['Hello world', Position(x=1, y=10), Derived()])

```

`tcod.ec.Composite` is a collection of anonymous components.
Unlike `ComponentDict` this can store multiple components with the same class.
Components can also be accessed using the parent class.
This works with multiple inheritance.

While this class looks like an all around upgrade to `ComponentDict` it's far more complex to work with.
The ways it mixes class inheritance with composition can lead to anti-patterns if used carelessly.
Any class used as a key will return zero, one, or more instances which must be accounted for.
If in doubt then the simpler `ComponentDict` should be used instead.

```py

>>> @attrs.define
... class Body:
...     name: str
...     hp: int
>>> entity = tcod.ec.Composite([Position(1, 2), Graphic("!"), Body("torso", 10), Body("head", 5)])
>>> {Position, Graphic, Body} in entity
True
>>> (pos,) = entity[Position]  # Use unpacking logic to verify the number of elements.
>>> pos.y = 10
>>> entity[Position]
[Position(x=1, y=10)]
>>> entity[Graphic] = [Graphic("?")]  # New sequences can be assigned, this deletes all previous instances of that key.
>>> entity[Graphic]
[Graphic(ch='?')]
>>> del entity[Graphic]
>>> entity[Graphic]  # Missing keys return an empty sequence instead of KeyError.
()

>>> entity[Body]
[Body(name='torso', hp=10), Body(name='head', hp=5)]
>>> entity.extend([Body("legs", 10), Body("arms", 10)])  # Use append or extend to add new instances.
>>> for body in list(entity[Body]):  # Make a copy of the sequence if you intend to remove values during iteration.
...     body.hp -= 2
...     if body.name == "torso":
...         entity.remove(body)
>>> entity[Body]
[Body(name='head', hp=3), Body(name='legs', hp=8), Body(name='arms', hp=8)]

# All objects can be accessed at once using `object`.
>>> entity[object]
[Position(x=1, y=10), Body(name='head', hp=3), Body(name='legs', hp=8), Body(name='arms', hp=8)]
>>> entity[object] = ("Hello", "world")
>>> entity
Composite(['Hello', 'world'])

```
