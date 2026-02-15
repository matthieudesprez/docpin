# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1](https://github.com/matthieudesprez/grippydoc/compare/v0.3.0...v0.3.1) (2026-02-15)


### Bug Fixes

* remove unused variable in test_record_warns_on_unresolvable ([662f84f](https://github.com/matthieudesprez/grippydoc/commit/662f84fff4dc2ad48a06f5466b74ea4f85a5d88d))

## [0.3.0](https://github.com/matthieudesprez/grippydoc/compare/v0.2.0...v0.3.0) (2026-02-13)


### Features

* add code diff and doc context to `grippydoc check --diff` ([7f86350](https://github.com/matthieudesprez/grippydoc/commit/7f8635096737dbee1b1073546672509f8c27acee))
* replace manifest with inline hashes in markdown ([988988a](https://github.com/matthieudesprez/grippydoc/commit/988988a9c52214f4b478033dee75eee2bc4c1b20))


### Bug Fixes

* add contents permission for publish job checkout ([e5de334](https://github.com/matthieudesprez/grippydoc/commit/e5de33409be32b81c362ad4d1718d03f1f2ef8e3))
* resolve lint errors in test files ([2e8d3ad](https://github.com/matthieudesprez/grippydoc/commit/2e8d3ad37aea11688a16c6a0e93ac12ade91061c))

## [0.2.0](https://github.com/matthieudesprez/grippydoc/compare/v0.1.0...v0.2.0) (2026-02-04)


### Features

* add orphan detection, whitespace-insensitive hashing, and CI/CD ([4b46bd6](https://github.com/matthieudesprez/grippydoc/commit/4b46bd6832327992961d989c9a06566e099c5255))


### Bug Fixes

* add Python 3.9 compatibility for type hints ([db7dea7](https://github.com/matthieudesprez/grippydoc/commit/db7dea77fba8accfce4ba346c7a5af1ddd17e35f))

## [0.1.0](https://github.com/grippydoc/grippydoc/releases/tag/v0.1.0) (2024-01-01)

### Features

* Initial release
* `grippydoc init` - Initialize tracking in a project
* `grippydoc record` - Record code reference hashes
* `grippydoc check` - Check for stale, broken, and orphaned references
* `grippydoc status` - Show status of tracked references
* Support for file references: `[grip:file.py]`
* Support for line references: `[grip:file.py:42]`
* Support for range references: `[grip:file.py:10-20]`
* Support for symbol references: `[grip:file.py#function_name]`
