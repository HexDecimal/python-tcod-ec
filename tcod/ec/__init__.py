"""Entity/Component containers for implementing composition over inheritance.

Unlike with ECS, these containers are standalone.
This makes them simpler to use but they have fewer features.
"""

from __future__ import annotations

__version__ = "2.2.1"

import reprlib
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    DefaultDict,
    Iterable,
    Iterator,
    MutableMapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    overload,
)

from typing_extensions import Self

T = TypeVar("T")


ComponentDictObserver = Callable[["ComponentDict", Type[T], Optional[T], Optional[T]], None]
_ComponentDictObserver = Callable[["ComponentDict", Optional[T], Optional[T]], None]


def abstract_component(cls: type[T]) -> type[T]:
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


# Maybe needs PEP 695: https://peps.python.org/pep-0695/
class ComponentDict(MutableMapping[Type[Any], Any]):
    """A dictionary of component instances, addressed with their class as the key.

    This class implements the idea of a ``Dict[Type[T], T]`` type-hint.
    This allows adding data and behavior to an object without needing to define which classes the object holds ahead of time.

    For equality and hashing ComponentDict's use identity like a standard :any:`object` rather than like a :any:`dict`.
    This means two different ComponentDict's are considered unique even if they have the same exact components.

        >>> import attrs
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
        >>> {Position} in entity  # Test if an entity has a set of components.
        True
        >>> @attrs.define
        ... class Cursor(Position):  # If you need to store a 2nd Position then a subclass can be made.
        ...     pass
        >>> entity[Cursor] = Cursor()
        >>> entity
        ComponentDict([Position(x=0, y=0), Cursor(x=0, y=0)])
        >>> ComponentDict([Position(1, 2), Position(3, 4)])  # The same component always overwrites the previous one.
        ComponentDict([Position(x=3, y=4)])

    Observers can be used to track the assignment of components.
    These work best when the components are immutable and frozen.

        >>> @attrs.define(frozen=True)
        ... class Position():
        ...     x: int = 0
        ...     y: int = 0
        >>> def track_position(entity: ComponentDict, new_pos: Position | None, old_pos: Position | None) -> None:
        ...     print(f"Moved: {old_pos} -> {new_pos}")
        >>> entity = ComponentDict(components=[Position()], observers={Position: [track_position]})
        Moved: None -> Position(x=0, y=0)
        >>> entity
        ComponentDict([Position(x=0, y=0)], observers=...)
        >>> entity[Position] = Position(1, 2)
        Moved: Position(x=0, y=0) -> Position(x=1, y=2)
        >>> del entity[Position]
        Moved: Position(x=1, y=2) -> None

    Custom functions can be added to the class variable :any:`global_observers` to trigger side-effects on component assignment.
    This can be used to register components to a global system, handle save migration, or other effects::

        >>> @attrs.define(frozen=True)
        ... class Position():
        ...     x: int = 0
        ...     y: int = 0
        >>> def print_changes(entity: ComponentDict, kind: Type[Any], value: Any | None, old_value: Any | None) -> None:
        ...     print(f"{kind.__name__}: {old_value} -> {value}")
        >>> ComponentDict.global_observers.append(print_changes)
        >>> entity = ComponentDict([Position()])
        Position: None -> Position(x=0, y=0)
        >>> entity.set(Position(1, 2))
        Position: Position(x=0, y=0) -> Position(x=1, y=2)
        ComponentDict([Position(x=1, y=2)])
        >>> del entity[Position]
        Position: Position(x=1, y=2) -> None
        >>> ComponentDict.global_observers.remove(print_changes)

    .. versionchanged:: 2.2
        Is now a :any:`collections.abc.MutableMapping` and has all of the relevant methods such as ``.values()``.
    """

    __slots__ = ("_components", "observers", "__weakref__")

    _components: dict[type[Any], Any]
    """The actual components stored in a dictionary.  The indirection is needed to make type hints work."""

    global_observers: ClassVar[list[ComponentDictObserver[Any]]] = []
    '''A class variable list of functions to call with component changes.

    Unpickled and copied objects are observed as if their components are newly created.

    These work best with frozen immutable types as components if you want to observe all value changes.

    This can be used to improvise the "systems" of ECS.
    Observers can collect types of components in a global registry for example.

    Example::

        from typing import Any, Type
        import tcod.ec

        def my_observer(entity: ComponentDict, kind: Type[Any], value: Any | None, old_value: Any | None) -> None:
            """Print observed changes in components."""
            print(f"{entity=}, {kind=}, {value=}, {old_value=}")

        tcod.ec.ComponentDict.global_observers.append(my_observer)

    .. versionadded:: 2.0

    .. warning::
        Components in a garbage collected entity are not observed as being deleted.
        Use :any:`clear` when you are finished with an entity and want its components observed as being deleted.
    '''

    def __init__(
        self,
        components: Iterable[object] = (),
        observers: dict[type[Any], list[_ComponentDictObserver[Any]]] | None = None,
    ) -> None:
        """Initialize a ComponentDict.

        Args:
            components: An iterable of component objects.
                These are assigned by their type.
                If any components share the same type then the latter components overwrite the previous ones.
            observers: A dictionary of component observers.
                This is held by reference, so the same dict my be assigned to multiple ComponentDict's.
                Observers are called with the `components` used to create the ComponentDict.

        .. versionchanged:: 2.2
            Added `observers` parameter.
        """
        self.observers: dict[type[Any], list[_ComponentDictObserver[Any]]] = {} if observers is None else observers
        """A dictionary of a list of component observers.

        .. versionadded:: 2.2
        """
        self._components = {}
        self.set(*components)

    @staticmethod
    def __assert_key(key: T) -> None:
        """Assert that this key is either an abstract component or an anonymous component."""
        real_key = getattr(key, "_COMPONENT_TYPE", key)
        assert (
            real_key is key
        ), f"{key!r} is a child of an abstract component and can only be accessed with {real_key!r}."

    def set(self, *components: object) -> Self:
        """Assign or replace the components of this entity and return self.

        .. versionchanged:: 1.1
            Now returns self.
        """
        for component in components:
            self[getattr(component, "_COMPONENT_TYPE", component.__class__)] = component
        return self

    def __getitem__(self, key: type[T]) -> T:
        """Return a component of type, raises KeyError if it doesn't exist."""
        if __debug__:
            self.__assert_key(key)
        value = self._components.get(key)
        if value is not None:
            return value  # type: ignore[no-any-return]  # Cast to T.
        return self.__missing__(key)

    def __setstate__(self, state: Any | dict[str, Any]) -> None:  # noqa: ANN401
        """Unpickle instances from 1.0 or later, or complex subclasses from 2.0 or later.

        Component classes can change between picking and unpickling, and component order should be preserved.

        Side-effects are triggered.
        The unpickled object acts as if its components are newly assigned to it when observed.
        """
        # Normalize attrs handling.
        dict_state: dict[str, Any] = state[1] if isinstance(state, tuple) else state

        components: Iterable[object] = dict_state["_components"]
        del dict_state["_components"]
        if isinstance(components, dict):  # Convert v1.1 _components attribute into instance list.
            components = components.values()

        observers = {}
        if "observers" in dict_state:  # Missing from old objects.
            observers = dict_state["observers"]
            del dict_state["observers"]

        for attr, value in dict_state.items():
            setattr(self, attr, value)

        # Unpack components with global side-effects.
        self.observers = {}
        self._components = {}
        self.set(*components)
        self.observers = observers

    def __getstate__(self) -> dict[str, Any]:
        """Pickle this instance.  Any subclass slots and dict attributes will also be saved."""
        state: dict[str, Any] = {}
        for cls in self.__class__.__mro__:
            for attr in getattr(cls, "__slots__", ()):
                if not hasattr(self, attr):
                    continue
                if attr == "__weakref__":
                    continue
                if attr == "__dict__":
                    state.update(self.__dict__)
                    continue
                state[attr] = getattr(self, attr)
        state["_components"] = tuple(state["_components"].values())
        return state

    def __missing__(self, key: type[T]) -> T:
        '''Raise KeyError with the missing key.  Called when a key is missing.

        Example::

            class DefaultComponentDict(ComponentDict):
                __slots__ = ()

                def __missing__(self, key: Type[T]) -> T:
                    """Create default components for missing keys by calling `key` without parameters."""
                    self[key] = value = key()
                    return value
        '''
        raise KeyError(key)

    def __setitem__(self, key: type[T], value: T) -> None:
        """Set or replace a component."""
        valid_key = getattr(value, "_COMPONENT_TYPE", value.__class__)
        if key is not valid_key:
            msg = f"{value!r} is being assigned to {key!r} but it belongs to {valid_key!r} instead!"
            raise TypeError(msg)
        old_value = self._components.get(key)
        self._components[key] = value
        for global_observer in self.global_observers:
            global_observer(self, key, value, old_value)
        for local_observer in self.observers.get(key, ()):
            local_observer(self, value, old_value)

    def __delitem__(self, key: type[object]) -> None:
        """Delete a component."""
        old_value = self._components[key]
        del self._components[key]
        for global_observer in self.global_observers:
            global_observer(self, key, None, old_value)
        for local_observer in self.observers.get(key, ()):
            local_observer(self, None, old_value)

    def __contains__(self, keys: type[object] | Iterable[type[object]]) -> bool:  # type: ignore[override]
        """Return true if the types of component exist in this entity.  Takes a single type or an iterable of types.

        .. versionchanged:: 1.2
            Now supports checking multiple types at once.
        """
        if isinstance(keys, type):
            keys = (keys,)
        if __debug__:
            for key in keys:
                self.__assert_key(key)
        return all(key in self._components for key in keys)

    def __len__(self) -> int:
        """Return the number of components contained in this object."""
        return len(self._components)

    def __iter__(self) -> Iterator[type[Any]]:
        """Iterate over the keys of this container."""
        return iter(self._components)

    # Use identity comparison and hashing.
    __hash__ = object.__hash__
    __eq__ = object.__eq__
    __ne__ = object.__ne__

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        """Return the representation of this ComponentDict."""
        params = [f"[{', '.join(repr(component) for component in self._components.values())}]"]
        if self.observers:
            params.append(f"observers={self.observers!r}")
        return f"{self.__class__.__name__}({', '.join(params)})"

    if TYPE_CHECKING:

        @overload
        def get(self, __key: type[T]) -> T | None: ...

        @overload
        def get(self, __key: type[T], __default: T) -> T: ...

        def get(self, __key: type[T], __default: T | None = None) -> T | None:
            """Return a component, returns None or a default value when the component is missing."""
            # Type-hinted get override.

        def setdefault(self, __key: type[T], __default: T) -> T:  # type: ignore[override]
            """Assign a default value if a component is missing, then returns the current value."""
            # Type-hinted setdefault override, None is not a valid default.


class Composite:
    """A collection of multiple components organized by their inheritance tree.

    Allows multiple components for the same class and allows accessing components using a shared parent class.

    The order of components is preserved.

        >>> import attrs
        >>> from tcod.ec import Composite
        >>> @attrs.define
        ... class AreaOfEffect:
        ...     range: int
        >>> @attrs.define
        ... class Circle(AreaOfEffect):
        ...     pass
        >>> @attrs.define
        ... class Square(AreaOfEffect):
        ...     pass
        >>> spell = Composite([50, "fire", "damage", Circle(5)])
        >>> spell[int]
        [50]
        >>> spell[str]
        ['fire', 'damage']
        >>> spell[AreaOfEffect]
        [Circle(range=5)]
        >>> spell[Circle]
        [Circle(range=5)]
        >>> spell[Square]
        ()
        >>> spell[object]
        [50, 'fire', 'damage', Circle(range=5)]
        >>> spell.remove('damage')
        >>> spell.add("effect")
        >>> spell
        Composite([50, 'fire', Circle(range=5), 'effect'])
        >>> spell[int] = (20,)
        >>> spell[int]
        [20]
        >>> spell
        Composite(['fire', Circle(range=5), 'effect', 20])
        >>> spell[AreaOfEffect] = (Square(3),)
        >>> spell
        Composite(['fire', 'effect', 20, Square(range=3)])

    .. versionadded:: 2.1
    """

    __slots__ = ("_components", "__weakref__")

    _components: dict[type[Any], list[Any]]

    def __init__(self, components: Iterable[object] = ()) -> None:
        """Initialize a Composite object from an iterable of components.

        Args:
            components: An iterable of objects.
        """
        self._components = DefaultDict(list)
        for obj in components:
            self.add(obj)

    def add(self, component: object) -> None:
        """Add a component to this container."""
        for component_class in component.__class__.__mro__:
            self._components[component_class].append(component)

    def extend(self, components: Iterable[object]) -> None:
        """Add multiple components to this container."""
        for component in components:
            self.add(component)

    def remove(self, component: object) -> None:
        """Remove a component from this container.

        Will raise ValueError if the component was not present.
        """
        for component_class in component.__class__.__mro__:
            self._components[component_class].remove(component)
            if not self._components[component_class]:
                del self._components[component_class]

    def clear(self) -> None:
        """Clear all components from this container."""
        if object in self._components:
            del self[object]

    def __getitem__(self, key: type[T]) -> Sequence[T]:
        """Return a sequence of all instances of `key`.

        If no instances of `key` are stored then return an empty sequence.

        The actual list returned is internal and should not be saved.
        Copy the value with :any:`tuple` or :any:`list` if you intend to store the sequence.
        Do not modify the sequence.
        """
        return self._components.get(key, ())

    def __setitem__(self, key: type[T], values: Iterable[T]) -> None:
        """Replace all instances of `key` with the instances of `values`."""
        del self[key]
        for obj in values:
            self.add(obj)

    def __delitem__(self, key: type[object]) -> None:
        """Remove all instances of `key` if they exist."""
        if key not in self._components:
            return
        for obj in list(self._components[key]):
            self.remove(obj)

    def __contains__(self, keys: type[object] | Iterable[type[object]]) -> bool:
        """Return true if all types or sub-types of `keys` exist in this entity.

        Takes a single type or an iterable of types.
        """
        if isinstance(keys, type):
            keys = (keys,)
        return all(key in self._components for key in keys)

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Unpickle instances of this object.

        Any class changes in pickled components will be reflected correctly.
        """
        components: Iterable[object] = state["_components"]
        del state["_components"]

        for attr, value in state.items():
            setattr(self, attr, value)

        # Unpack components with side-effects.
        self._components = DefaultDict(list)
        for component in components:
            self.add(component)

    def __getstate__(self) -> dict[str, Any]:
        """Pickle this instance.  Any subclass slots and dict attributes will also be saved."""
        state: dict[str, Any] = {}
        for cls in self.__class__.__mro__:
            for attr in getattr(cls, "__slots__", ()):
                if not hasattr(self, attr):
                    continue
                if attr == "__weakref__":
                    continue
                if attr == "__dict__":
                    state.update(self.__dict__)
                    continue
                state[attr] = getattr(self, attr)
        state["_components"] = self._components.get(object, ())
        return state

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        """Return the representation of this Composite."""
        components = ", ".join(repr(component) for component in self._components.get(object, ()))
        return f"""{self.__class__.__name__}([{components}])"""
