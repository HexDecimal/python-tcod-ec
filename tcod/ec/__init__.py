"""Basic Entity/Component containers for implementing composition over inheritance.

Unlike with ECS, these containers are standalone.
This makes them simpler to use but they have fewer features.
"""
from __future__ import annotations

__version__ = "1.0.0"

import reprlib
from typing import Any, Dict, Iterable, Iterator, Optional, Type, TypeVar

import attrs
from typing_extensions import Self

T = TypeVar("T")


def abstract_component(cls: Type[T]) -> Type[T]:
    """Register class `cls` as an abstract component and return it.

    Subclasses of this `cls` will now use `cls` as the key when being accessed in :any:`ComponentDict`.
    This means that ComponentDict can only hold one unique instance of this subclass.

    Example::

        >>> from tcod.ec import ComponentDict, abstract_component
        >>> from attrs import define
        >>> @abstract_component
        ... @define
        ... class Base:
        ...     pass
        >>> @define
        ... class Derived(Base):
        ...     pass
        >>> entity = ComponentDict([Derived()])
        >>> entity.set(Derived())
        ComponentDict([Derived()])
        >>> entity[Base] = Derived()  # Note there can only be one instance assigned to an abstract component class.
        >>> Base in entity
        True
        >>> entity[Base]  # Access Base or Derived with the abstract component class.
        Derived()
        >>> entity[Base] = Base()
        >>> entity[Base]
        Base()
        >>> entity.set(Derived())
        ComponentDict([Derived()])
        >>> entity[Base]
        Derived()
    """
    cls._COMPONENT_TYPE = cls  # type: ignore[attr-defined]
    return cls


def _convert_components(components: Iterable[object]) -> Dict[Type[Any], Any]:
    """Convert a sequence of objects to a component dictionary."""
    return {getattr(component, "_COMPONENT_TYPE", component.__class__): component for component in components}


@attrs.define(eq=False)
class ComponentDict:
    """A dictionary of component instances, addressed with their class as the key.

    This class implements the idea of a ``Dict[Type[T], T]`` type-hint.
    This allows adding data and behavior to an object without needing to define which classes the object holds ahead of time.

    An anonymous component is any class without a parent class marked with :any:`abstract_component`::

        >>> from attrs import define
        >>> from tcod.ec import ComponentDict
        >>> @attrs.define
        ... class Position:  # Any normal class works as a component.
        ...     x: int = 0
        ...     y: int = 0
        >>> entity = ComponentDict([Position()])  # Add Position during initialization.
        >>> entity.set(Position())  # Or with ComponentDict.set.
        ComponentDict([Position(x=0, y=0)])
        >>> entity[Position] = Position()  # Or explicitly by key.
        >>> entity[Position]  # Access the instance with the class as the key.
        Position(x=0, y=0)
        >>> Position in entity  # Test if an entity has a component.
        True
        >>> @attrs.define
        ... class Cursor(Position):  # If you need to store a 2nd Position then a subclass can be made.
        ...     pass
        >>> entity[Cursor] = Cursor()
        >>> entity
        ComponentDict([Position(x=0, y=0), Cursor(x=0, y=0)])
        >>> ComponentDict([Position(1, 2), Position(3, 4)])  # The same component always overwrites the previous one.
        ComponentDict([Position(x=3, y=4)])

    If you want to assign a subclass to a parents key then you should decorate that parent class with the
    :any:`abstract_component` function.
    """

    _components: Dict[Type[Any], Any] = attrs.field(default=(), converter=_convert_components)
    """The actual components stored in a dictionary.  The indirection is needed to make type hints work."""

    @staticmethod
    def __assert_key(key: T) -> None:
        """Assert that this key is either an abstract component or an anonymous component."""
        real_key = getattr(key, "_COMPONENT_TYPE", key)
        assert (
            real_key is key
        ), f"{key!r} is a child of an abstract component and can only be accessed with {real_key!r}."

    def set(self, *components: T) -> Self:
        """Assign or replace the components of this entity and return self."""
        for component in components:
            self._components[getattr(component, "_COMPONENT_TYPE", component.__class__)] = component
        return self

    def get(self, key: Type[T]) -> Optional[T]:
        """Return a component, or None if it doesn't exist."""
        if __debug__:
            self.__assert_key(key)
        return self._components.get(key)  # Cast to Optional[T].

    def __getitem__(self, key: Type[T]) -> T:
        """Return a component of type, raises KeyError if it doesn't exist."""
        if __debug__:
            self.__assert_key(key)
        value = self._components.get(key)
        if value is not None:
            return value  # type: ignore[no-any-return]  # Cast to T.
        return self.__missing__(key)

    def __missing__(self, key: Type[T]) -> T:
        '''Called when a key is missing.  Raises KeyError with the missing key.

        Example::

            class DefaultComponentDict(ComponentDict):
                __slots__ = ()

                def __missing__(self, key: Type[T]) -> T:
                    """Create default components for missing keys by calling `key` without parameters."""
                    self[key] = value = key()
                    return value
        '''
        raise KeyError(key)

    def __setitem__(self, key: Type[T], value: T) -> None:
        """Set or replace a component."""
        valid_key = getattr(value, "_COMPONENT_TYPE", value.__class__)
        if key is not valid_key:
            raise TypeError(f"{value!r} is being assigned to {key!r} but it belongs to {valid_key!r} instead!")
        self._components[key] = value

    def __delitem__(self, key: Type[T]) -> None:
        """Delete a component."""
        del self._components[key]

    def __contains__(self, key: Type[T]) -> bool:
        """Return true if a type of component exists in this entity."""
        if __debug__:
            self.__assert_key(key)
        return key in self._components

    def __len__(self) -> int:
        """Return the number of components contained in this object."""
        return len(self._components)

    def __iter__(self) -> Iterator[Type[object]]:
        """Iterate over the keys of this container."""
        return iter(self._components)

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        """Return the representation of this ComponentDict."""
        return f"{self.__class__.__name__}([{', '.join(repr(component) for component in self._components.values())}])"
