# Changelog

## 0.3.0

- Added `on_missing_key = "ignore" | "warn" | "error"` as an alternative to `warn` that errors on missing keys (see [#14](https://github.com/zanieb/chevron-blue/pull/14))

## 0.2.1

- Fixed bug where `--no-escape` was not applied to recursive patterns; (see [#5](https://github.com/zanieb/chevron-blue/pull/5))

## 0.2.0

- Fixed spec compliance bug where variables could be incorrectly resolved from other scopes (see [#3](https://github.com/zanieb/chevron-blue/pull/3))
- Added global `--no-escape` option to disable HTML escaping (see [#4](https://github.com/zanieb/chevron-blue/pull/4))

## 0.1.0

Forked from [noahmorrison/chevron](noahmorrison/chevron).

- Switched to a modern build system
- Switched to GitHub Actions for CI
- Used Ruff for linting and formatting
- Dropped support for Python 2
- Verified support for Python 3.7 - 3.14
