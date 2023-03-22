# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.0] - 2023-03-21
### Added
- `ComponentDict` is now a `MutableMapping` subclass.
  It can now do everything expected of a dict-like object, such as the `.values()` method.
  Keep in mind it still uses identity comparison.
- Added local component observers to `ComponentDict`.

### Changed
- `abstract_component` is no longer deprecated.

## [2.1.0] - 2023-02-03
### Added
- New `tcod.ec.Composite` class.
  Supports multiple components of the same type and looking up components with a parent type.

### Fixed
- Better handling of `__dict__` in `ComponentDict` subclasses.
  Allowing migration of attributes to or from slots for subclasses the next time they are pickled.

## [2.0.0] - 2023-01-24
### Added
- `ComponentDict.global_observers` for observing changes in components globally.
- `ComponentDict.clear` for removing all components.

### Changed
- `ComponentDict` internals have changed.  No longer uses attrs and has a less complex constructor.
  Should still be able to unpickle plain instances pickled in v1.
- No longer depends on attrs.

### Deprecated
- `abstract_component` has been deprecated.  Components storing base classes should be used instead.

## [1.2.0] - 2023-01-14
### Added
- `ComponentDict` can now be tested for multiple components at once.  Example: `(Foo, Bar) in component_dict`

## [1.1.0] - 2023-01-13
### Added
- ``ComponentDict.set`` now returns `self`.

## [1.0.0] - 2023-01-06
Initial stable release with ``ComponentDict``.
