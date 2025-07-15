# chevron-blue

A Python implementation of the [mustache templating language](http://mustache.github.io).

## Acknowledgements

This library is a fork of [chevron](https://github.com/noahmorrison/chevron) authored by [Noah Morrison](https://github.com/noahmorrison).

The following changes have been made:

- Switched to a modern build system
- Switched to GitHub Actions for CI
- Used Ruff for linting and formatting
- Dropped support for Python 2
- Verified support for Python 3.7 - 3.14
- Fixed bug where variables could be incorrectly resolved from other scopes (see [#3](https://github.com/zanieb/chevron-blue/pull/3))
- Added global `--no-escape` option to disable HTML escaping (see [#4](https://github.com/zanieb/chevron-blue/pull/4))
