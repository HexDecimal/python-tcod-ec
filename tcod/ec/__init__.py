"""Basic Entity/Component containers for implementing composition over inheritance.

Unlike with ECS, these containers are standalone.
This makes them simpler to use but they have fewer features.
"""
from __future__ import annotations

__version__ = "0.0.2"

import reprlib
from typing import Dict, Iterable, Iterator, Optional, Type, TypeVar

import attrs

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
        >>> entity = ComponentDict()
        >>> Base in entity
        False
        >>> entity[Base] = Derived()
        >>> Base in entity
        True
        >>> entity[Base]
        Derived()
        >>> entity[Base] = Base()
        >>> entity[Base]
        Base()
        >>> entity.set(Derived())
        >>> entity[Base]
        Derived()
    """
    cls._COMPONENT_TYPE = cls  # type: ignore[attr-defined]
    return cls


def _convert_components(components: Iterable[object]) -> Dict[Type[object], object]:
    """Convert a sequence of objects to a component dictionary."""
    return {getattr(component, "_COMPONENT_TYPE", component.__class__): component for component in components}


@attrs.define(eq=False)
class ComponentDict:
    """A dictionary of component instances, addressed with their class as the key."""

    _components: Dict[Type[object], object] = attrs.field(default=(), converter=_convert_components)
    """The actual components stored in a dictionary.  The indirection is needed to make type hints work."""

    @staticmethod
    def __assert_key(key: T) -> None:
        """Assert that this key is either an abstract component or an anonymous component."""
        real_key = getattr(key, "_COMPONENT_TYPE", key)
        assert (
            real_key is key
        ), f"{key!r} is a child of an abstract component and can only be accessed with {real_key!r}."

    def set(self, *components: T) -> None:
        """Assign or replace the components of this entity."""
        for component in components:
            self._components[getattr(component, "_COMPONENT_TYPE", component.__class__)] = component

    def get(self, key: Type[T]) -> Optional[T]:
        """Return a component, or None if it doesn't exist."""
        if __debug__:
            self.__assert_key(key)
        return self._components.get(key)  # type: ignore[return-value]  # Cast to T.

    def __getitem__(self, key: Type[T]) -> T:
        """Return a component of type, raises KeyError if it doesn't exist."""
        if __debug__:
            self.__assert_key(key)
        value = self._components.get(key)
        if value is not None:
            return value  # type: ignore[return-value]  # Cast to T.
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
