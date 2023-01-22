# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
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
