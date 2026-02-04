# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
